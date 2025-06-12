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
from utils.graph_builder import (
    assign_node_communities, # Import the new community assignment function
    build_pyvis_graph,
    create_networkx_graph,
    limit_graph_nodes_by_degree
)

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
                f"Full NetworkX graph created: {nx_graph.number_of_nodes()} nodes, "
                f"{nx_graph.number_of_edges()} edges."
            )

            # --- UI for Node Sizing and Limiting ---
            st.sidebar.subheader("Graph Display Options")

            max_nodes_to_display = st.sidebar.number_input(
                "Max Nodes to Display (0 for all, by degree):",
                min_value=0,
                value=0,  # Default to 0 (show all nodes)
                step=10,
                help="Limits the number of nodes in the visualization based on degree. 0 means no limit."
            )

            # Apply node limiting
            limited_nx_graph = limit_graph_nodes_by_degree(nx_graph, max_nodes_to_display)

            # Assign communities to the (potentially limited) graph
            # This function modifies the graph in place or returns it if no changes.
            # For clarity, reassign, though nx_graph passed to community assignment
            # should be limited_nx_graph.
            graph_for_viz = assign_node_communities(limited_nx_graph)
            # Ensure any messages about graph size use graph_for_viz
            # (though assign_node_communities doesn't change node/edge count)

            if max_nodes_to_display > 0 and max_nodes_to_display < nx_graph.number_of_nodes():
                st.sidebar.info(
                    f"Displaying: {graph_for_viz.number_of_nodes()} nodes, "
                    f"{graph_for_viz.number_of_edges()} edges (limited by degree)."
                )
            elif graph_for_viz.number_of_nodes() == 0 : # If graph_for_viz is empty
                 st.sidebar.info("Graph is empty or all nodes were filtered out. Nothing to display.")
            else: # No limiting applied or limit >= num_nodes
                 st.sidebar.info(
                    f"Displaying: {graph_for_viz.number_of_nodes()} nodes, "
                    f"{graph_for_viz.number_of_edges()} edges."
                )


            sizing_options = ["default", "connection_count"]
            # Future: Add other metrics like centrality once calculated e.g. "degree_centrality"

            selected_size_metric = st.sidebar.selectbox(
                "Node Sizing Metric:",
                options=sizing_options,
                index=0,  # Default to "default"
                help=("Select how node sizes are determined. "
                      "'connection_count' sizes nodes by their number of connections.")
            )

            use_community_coloring = st.sidebar.checkbox(
                "Color Nodes by Community",
                value=False,
                help="Overrides type-based coloring with community-based colors if communities are detected."
            )

            # Edge width selection
            edge_width_options = ["Normal", "Thin"]
            selected_edge_width_style = st.sidebar.selectbox(
                "Edge Width:",
                options=edge_width_options,
                index=0, # Default to "Normal"
                help="Adjust the visual thickness of edges."
            )

            # 6. Build PyVis Graph
            # Create a copy of APP_SETTINGS to modify for the current build
            # current_build_settings = APP_SETTINGS.copy() # This should be a deepcopy for nested dicts
            current_build_settings = copy.deepcopy(APP_SETTINGS)


            if selected_size_metric != "default":
                current_build_settings['node_size_metric'] = selected_size_metric
            else:
                # Ensure it's not set if "default" is chosen, so style_nodes uses its default_node_size
                current_build_settings.pop('node_size_metric', None)

            current_build_settings['color_by_community'] = use_community_coloring
            # 'default_community_colors' is already in APP_SETTINGS and thus in current_build_settings

            # Update edge width in current_build_settings based on selection
            if selected_edge_width_style == "Normal":
                current_build_settings['edge_width'] = current_build_settings.get('default_edge_weight', 1)
            elif selected_edge_width_style == "Thin":
                current_build_settings['edge_width'] = current_build_settings.get('light_edge_weight', 0.5)
            # Other edge settings like smooth_type, highlight/hover colors are already in current_build_settings
            # from the deepcopy of APP_SETTINGS.

            # --- UI for Physics Controls ---
            st.sidebar.subheader("Physics Solver")
            solver_options = ['barnesHut', 'forceAtlas2Based']
            selected_solver = st.sidebar.selectbox(
                "Choose Solver:",
                options=solver_options,
                index=0, # Default to barnesHut
                help="Select the physics solver for graph layout."
            )

            # Make a deep copy of the relevant physics options from APP_SETTINGS to current_build_settings
            # This ensures that APP_SETTINGS remains unchanged, and current_build_settings
            # holds the potentially modified settings for this specific build.
            if 'pyvis_barnesHut_options' not in current_build_settings:
                current_build_settings['pyvis_barnesHut_options'] = copy.deepcopy(APP_SETTINGS.get('pyvis_barnesHut_options', {}))
            if 'pyvis_forceatlas2based_options' not in current_build_settings:
                current_build_settings['pyvis_forceatlas2based_options'] = copy.deepcopy(APP_SETTINGS.get('pyvis_forceatlas2based_options', {}))

            active_solver_options = {}

            if selected_solver == 'barnesHut':
                st.sidebar.subheader("BarnesHut Options")
                default_bh_opts = APP_SETTINGS.get('pyvis_barnesHut_options', {}).get('barnesHut', {})
                current_bh_opts = copy.deepcopy(current_build_settings['pyvis_barnesHut_options'].get('barnesHut', {}))

                grav_const = st.sidebar.slider(
                    "Gravitational Constant (BH)", min_value=-30000, max_value=0,
                    value=current_bh_opts.get('gravitationalConstant', default_bh_opts.get('gravitationalConstant', -8000)),
                    step=100, key="bh_grav_const"
                )
                central_gravity = st.sidebar.slider(
                    "Central Gravity (BH)", min_value=0.0, max_value=1.0,
                    value=current_bh_opts.get('centralGravity', default_bh_opts.get('centralGravity', 0.3)),
                    step=0.05, key="bh_central_gravity"
                )
                spring_length = st.sidebar.slider(
                    "Spring Length (BH)", min_value=50, max_value=500,
                    value=current_bh_opts.get('springLength', default_bh_opts.get('springLength', 250)),
                    step=10, key="bh_spring_length"
                )
                spring_constant = st.sidebar.slider(
                    "Spring Constant (BH)", min_value=0.0, max_value=0.5,
                    value=current_bh_opts.get('springConstant', default_bh_opts.get('springConstant', 0.04)),
                    step=0.01, key="bh_spring_constant"
                )
                damping = st.sidebar.slider(
                    "Damping (BH)", min_value=0.0, max_value=0.5,
                    value=current_bh_opts.get('damping', default_bh_opts.get('damping', 0.09)),
                    step=0.01, key="bh_damping"
                )
                avoid_overlap = st.sidebar.slider(
                    "Avoid Overlap (BH)", min_value=0.0, max_value=1.0,
                    value=current_bh_opts.get('avoidOverlap', default_bh_opts.get('avoidOverlap', 0.1)),
                    step=0.05, key="bh_avoid_overlap"
                )

                # Update the barnesHut part of the options in current_build_settings
                current_build_settings['pyvis_barnesHut_options']['barnesHut'] = {
                    'gravitationalConstant': grav_const,
                    'centralGravity': central_gravity,
                    'springLength': spring_length,
                    'springConstant': spring_constant,
                    'damping': damping,
                    'avoidOverlap': avoid_overlap
                }
                # Ensure other parts like 'enabled', 'solver', 'stabilization' are preserved from defaults
                full_bh_options_template = APP_SETTINGS.get('pyvis_barnesHut_options', {})
                for key, value in full_bh_options_template.items():
                    if key not in current_build_settings['pyvis_barnesHut_options']:
                        current_build_settings['pyvis_barnesHut_options'][key] = copy.deepcopy(value)
                    elif key == 'barnesHut': # Already updated above
                        continue
                    elif isinstance(value, dict): # e.g. stabilization
                         current_build_settings['pyvis_barnesHut_options'][key] = copy.deepcopy(value)


                current_build_settings['pyvis_barnesHut_options']['enabled'] = True
                current_build_settings['pyvis_barnesHut_options']['solver'] = 'barnesHut'
                active_solver_options = current_build_settings['pyvis_barnesHut_options']

            elif selected_solver == 'forceAtlas2Based':
                st.sidebar.subheader("ForceAtlas2Based Options")
                default_fa2_opts = APP_SETTINGS.get('pyvis_forceatlas2based_options', {}).get('forceAtlas2Based', {})
                current_fa2_opts = copy.deepcopy(current_build_settings['pyvis_forceatlas2based_options'].get('forceAtlas2Based', {}))

                gravity = st.sidebar.slider(
                    "Gravity (FA2)", min_value=-200, max_value=0,
                    value=current_fa2_opts.get('gravity', default_fa2_opts.get('gravity', -50)),
                    step=1, key="fa2_gravity"
                )
                central_gravity = st.sidebar.slider(
                    "Central Gravity (FA2)", min_value=0.0, max_value=0.2,
                    value=current_fa2_opts.get('centralGravity', default_fa2_opts.get('centralGravity', 0.01)),
                    step=0.001, format="%.3f", key="fa2_central_gravity"
                )
                spring_length = st.sidebar.slider(
                    "Spring Length (FA2)", min_value=10, max_value=500,
                    value=current_fa2_opts.get('springLength', default_fa2_opts.get('springLength', 100)),
                    step=10, key="fa2_spring_length"
                )
                spring_constant = st.sidebar.slider(
                    "Spring Constant (FA2)", min_value=0.0, max_value=0.5,
                    value=current_fa2_opts.get('springConstant', default_fa2_opts.get('springConstant', 0.08)),
                    step=0.01, key="fa2_spring_constant"
                )
                damping = st.sidebar.slider(
                    "Damping (FA2)", min_value=0.0, max_value=1.0,
                    value=current_fa2_opts.get('damping', default_fa2_opts.get('damping', 0.4)),
                    step=0.01, key="fa2_damping"
                )
                avoid_overlap = st.sidebar.slider(
                    "Avoid Overlap (FA2)", min_value=0.0, max_value=1.0,
                    value=current_fa2_opts.get('avoidOverlap', default_fa2_opts.get('avoidOverlap', 0)), # Default 0 for FA2
                    step=0.05, key="fa2_avoid_overlap"
                )

                # Update the forceAtlas2Based part of the options in current_build_settings
                current_build_settings['pyvis_forceatlas2based_options']['forceAtlas2Based'] = {
                    'gravity': gravity,
                    'centralGravity': central_gravity,
                    'springLength': spring_length,
                    'springConstant': spring_constant,
                    'damping': damping,
                    'avoidOverlap': avoid_overlap
                }
                # Ensure other parts like 'enabled', 'solver', 'stabilization' are preserved from defaults
                full_fa2_options_template = APP_SETTINGS.get('pyvis_forceatlas2based_options', {})
                for key, value in full_fa2_options_template.items():
                    if key not in current_build_settings['pyvis_forceatlas2based_options']:
                        current_build_settings['pyvis_forceatlas2based_options'][key] = copy.deepcopy(value)
                    elif key == 'forceAtlas2Based': # Already updated
                        continue
                    elif isinstance(value, dict): # e.g. stabilization
                        current_build_settings['pyvis_forceatlas2based_options'][key] = copy.deepcopy(value)


                current_build_settings['pyvis_forceatlas2based_options']['enabled'] = True
                current_build_settings['pyvis_forceatlas2based_options']['solver'] = 'forceAtlas2Based'
                active_solver_options = current_build_settings['pyvis_forceatlas2based_options']

            # Update the JSON string representation in current_build_settings for the active solver
            # This key is for general reference or if other parts of the app expect it.
            # build_pyvis_graph will use the dictionary for the selected solver.
            current_build_settings['pyvis_options_json_string'] = json.dumps({"physics": active_solver_options})


            # Pass the graph (potentially limited and with communities) to the PyVis builder
            pyvis_graph = build_pyvis_graph(graph_for_viz, settings=current_build_settings, solver_type=selected_solver)

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
