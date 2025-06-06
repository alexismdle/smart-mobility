"""
Streamlit application for Interactive Knowledge Graph Visualization.

This application allows users to upload JSON data representing relationships,
processes this data, builds a network graph, and visualizes it using PyVis.
"""
import copy  # For deep copying settings
import json  # For creating JSON string for PyVis
import tempfile
from pathlib import Path

import pandas as pd  # Import pandas
import streamlit as st

from config.settings import APP_SETTINGS  # Import APP_SETTINGS

#imports
from utils.data_processor import (
    clean_data,
    load_json_data,
    normalize_entities,
    validate_data,
)
from utils.graph_builder import build_pyvis_graph, create_networkx_graph

# --- Streamlit Page Configuration ---
st.set_page_config(layout="wide", page_title="Knowledge Graph Visualizer")

# --- Application Title ---
st.title("Interactive Knowledge Graph Visualizer")

def main():
    """
    Main function to run the Streamlit application.
    Handles file uploading, data processing, graph generation, and visualization.
    """
    # --- Sidebar for Controls ---
    st.sidebar.header("Controls")

    # Direct loading of assets/sample_data.json
    sample_data_path = Path("assets/sample_data.json")
    source_name = "Sample Data (assets/sample_data.json)"

    if not sample_data_path.exists():
        st.sidebar.error(f"Critical: Sample data file not found at {sample_data_path}.")
        st.error(f"The application expects the sample data file at '{sample_data_path}'. Please ensure it exists.")
        return  # Exit if the hardcoded data source is not available

    st.sidebar.info(f"Displaying graph from: {source_name}")
    data_source = str(sample_data_path)

    # 1. Load Data
    edges_df, node_info_map = load_json_data(data_source)

    # Check if edges_df is a DataFrame and node_info_map is a dict, basic check for successful load
    if not isinstance(edges_df, pd.DataFrame) or not isinstance(node_info_map, dict):
        st.sidebar.error("Failed to load data correctly. Expected a DataFrame and a dictionary from load_json_data.")
        return

    # Proceed if we have at least nodes or edges
    if not edges_df.empty or node_info_map:
        st.sidebar.success(f"Data loaded. Nodes: {len(node_info_map)}, Edges: {len(edges_df)}")

        # 2. Validate Data (validates structure of edges_df)
        # If there are no edges, validation might not be meaningful or could be skipped.
        # However, validate_data handles empty df gracefully.
        if validate_data(edges_df):
            if not edges_df.empty:  # Only show success if there were edges to validate
                st.sidebar.success("Edge data validation successful!")
            elif not node_info_map and edges_df.empty:  # No nodes and no edges
                st.sidebar.warning("No nodes or edges found in the data.")
                # This case might be an actual empty valid JSON, so we might not want to return.
                # The graph building will handle empty graph. Let's let it proceed.
                pass  # Allow to proceed to show an empty graph or graph with only nodes

            # 3. Clean Data (cleans edges_df)
            cleaned_df = clean_data(edges_df)
            if cleaned_df.empty and not edges_df.empty:  # Check if cleaning resulted in empty DF from non-empty
                st.sidebar.warning("Edge data became empty after cleaning. Check for essential missing values.")
                st.dataframe(edges_df)  # Show original edges_df for context
                return
            if not edges_df.empty:  # Only report on cleaning if there were edges
                st.sidebar.write(f"Edge data cleaned. Rows remaining: {len(cleaned_df)}")

            # 4. Normalize Entities (normalizes edges_df)
            normalized_df = normalize_entities(cleaned_df)
            if not edges_df.empty:  # Only report on normalization if there were edges
                st.sidebar.write(f"Entities in edge data normalized. Total relationships: {len(normalized_df)}")

            if normalized_df.empty and not cleaned_df.empty:  # Check if normalization resulted in empty
                st.sidebar.warning("Edge data became empty after normalization.")
                st.dataframe(cleaned_df)  # Show cleaned df for context
                return

            # Display processed data snippet in sidebar (optional)
            if st.sidebar.checkbox("Show processed edge data snippet"):
                st.sidebar.dataframe(normalized_df.head())

            # 5. Create NetworkX Graph
            # Pass both the DataFrame of edges and the map of node information
            nx_graph = create_networkx_graph(normalized_df, node_info_map)

            # Check graph generation success based on nodes from node_info_map or edges
            # It's possible to have a graph with only nodes if node_info_map is not empty but normalized_df is
            if nx_graph.number_of_nodes() == 0 and not node_info_map and (normalized_df is None or normalized_df.empty):
                st.sidebar.error("Failed to create graph: No nodes or edges were generated from the data.")
                if normalized_df is not None and not normalized_df.empty:
                    st.dataframe(normalized_df)
                if not node_info_map:
                    st.sidebar.write("Node info map is also empty.")
                return
            elif nx_graph.number_of_nodes() == 0 and node_info_map:  # Nodes existed, but graph is empty (problem)
                st.sidebar.error("Failed to create graph: Graph has no nodes, but node data was present.")
                return

            st.sidebar.success(
                f"NetworkX graph created: {nx_graph.number_of_nodes()} nodes, "
                f"{nx_graph.number_of_edges()} edges."
            )

            # --- UI for Node Sizing ---
            st.sidebar.subheader("Graph Styling")
            sizing_options = ["default", "connection_count"]
            # Future: Add other metrics like centrality once calculated e.g. "degree_centrality"

            selected_size_metric = st.sidebar.selectbox(
                "Node Sizing Metric:",
                options=sizing_options,
                index=0,  # Default to "default"
                help=("Select how node sizes are determined. "
                      "'connection_count' sizes nodes by their number of connections.")
            )

            # 6. Build PyVis Graph
            # Create a copy of APP_SETTINGS to modify for the current build
            current_build_settings = APP_SETTINGS.copy()
            if selected_size_metric != "default":
                current_build_settings['node_size_metric'] = selected_size_metric
            else:
                # Ensure it's not set if "default" is chosen, so style_nodes uses its default_node_size
                current_build_settings.pop('node_size_metric', None)

            # --- UI for Physics Controls ---
            st.sidebar.subheader("Physics Controls (BarnesHut)")

            # Use a deep copy of the dictionary part of physics settings from APP_SETTINGS
            # to prevent modification of the global APP_SETTINGS on widget changes.
            # Fallback to an empty dict if 'pyvis_physics_options_dict' is not in APP_SETTINGS
            default_physics_dict = APP_SETTINGS.get('pyvis_physics_options_dict', {})
            if not isinstance(default_physics_dict, dict):  # Ensure it's a dict
                default_physics_dict = {}

            # Make sure barnesHut key exists in default_physics_dict
            if 'barnesHut' not in default_physics_dict:
                default_physics_dict['barnesHut'] = {}

            grav_const_default = default_physics_dict.get('barnesHut', {}).get('gravitationalConstant', -8000)
            central_gravity_default = default_physics_dict.get('barnesHut', {}).get('centralGravity', 0.3)
            spring_length_default = default_physics_dict.get('barnesHut', {}).get('springLength', 250)
            spring_const_default = default_physics_dict.get('barnesHut', {}).get('springConstant', 0.04)
            damping_default = default_physics_dict.get('barnesHut', {}).get('damping', 0.09)
            avoid_overlap_default = default_physics_dict.get('barnesHut', {}).get('avoidOverlap', 0.1)

            gravitational_constant = st.sidebar.slider(
                "Gravitational Constant", min_value=-30000, max_value=0,
                value=grav_const_default, step=100
            )
            central_gravity = st.sidebar.slider(
                "Central Gravity", min_value=0.0, max_value=1.0,
                value=central_gravity_default, step=0.05
            )
            spring_length = st.sidebar.slider(
                "Spring Length", min_value=50, max_value=500,
                value=spring_length_default, step=10
            )
            spring_constant = st.sidebar.slider(
                "Spring Constant", min_value=0.0, max_value=0.5,
                value=spring_const_default, step=0.01
            )
            damping = st.sidebar.slider(
                "Damping", min_value=0.0, max_value=0.5,
                value=damping_default, step=0.01
            )
            avoid_overlap = st.sidebar.slider(
                "Avoid Overlap", min_value=0.0, max_value=1.0,
                value=avoid_overlap_default, step=0.05
            )

            # Update physics settings in current_build_settings
            current_physics_options = copy.deepcopy(default_physics_dict)  # Start from a clean copy of defaults

            if 'barnesHut' not in current_physics_options:  # Should be there from above check
                current_physics_options['barnesHut'] = {}

            current_physics_options['barnesHut']['gravitationalConstant'] = gravitational_constant
            current_physics_options['barnesHut']['centralGravity'] = central_gravity
            current_physics_options['barnesHut']['springLength'] = spring_length
            current_physics_options['barnesHut']['springConstant'] = spring_constant
            current_physics_options['barnesHut']['damping'] = damping
            current_physics_options['barnesHut']['avoidOverlap'] = avoid_overlap

            # Ensure 'enabled' and 'solver' are correctly set for these controls
            current_physics_options['enabled'] = True
            current_physics_options['solver'] = 'barnesHut'

            # Update both the dictionary and the JSON string representation in current_build_settings
            current_build_settings['pyvis_physics_options_dict'] = current_physics_options
            current_build_settings['pyvis_physics_options_json_string'] = json.dumps({"physics": current_physics_options})

            pyvis_graph = build_pyvis_graph(nx_graph, settings=current_build_settings)

            # 7. Render PyVis Graph
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode='w', encoding='utf-8') as tmp_file:
                    pyvis_graph.save_graph(tmp_file.name)
                    html_content = Path(tmp_file.name).read_text()

                st.components.v1.html(html_content, height=750, scrolling=True)
                Path(tmp_file.name).unlink()  # Clean up the temporary file

            except Exception as e:
                st.error(f"Error rendering graph: {e}")
                # TODO: Log this error properly

        else:
            st.sidebar.error("Data validation failed. Please check the JSON structure and required fields.")
            st.warning(
                "The uploaded JSON data does not meet the required format. "
                "Ensure the JSON has 'nodes' and 'edges' arrays. Nodes need 'id', 'source_file', 'attributes'. Edges need 'from', 'to', 'label'."
            )
            # Show edges_df if it's not None and has data, for debugging structure issues
            if edges_df is not None and not edges_df.empty and st.sidebar.checkbox("Show edge data for debugging"):
                st.dataframe(edges_df)
            # Show node_info_map if it's not None and has data
            if node_info_map is not None and node_info_map and st.sidebar.checkbox("Show node info map for debugging"):
                st.json(node_info_map)  # Display node_info_map as JSON
    else:  # This means both edges_df is empty AND node_info_map is empty after loading
        st.sidebar.error(f"Failed to load data from '{source_name}': No nodes or edges were found.")
        # No need to attempt to show raw content as it's a fixed file path.
        # The error from load_json_data (if any) would have printed to console.

# This else block for 'if data_source:' is implicitly handled by the return if sample_data.json not found
# and no file is uploaded. If a file IS uploaded but load_json_data returns empty, it's handled above.

if __name__ == "__main__":
    main()
