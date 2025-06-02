"""
Streamlit application for Interactive Knowledge Graph Visualization.

This application allows users to upload JSON data representing relationships,
processes this data, builds a network graph, and visualizes it using PyVis.
"""
import copy  # For deep copying settings
import json  # For creating JSON string for PyVis
import tempfile
from pathlib import Path

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

# --- Main Application Logic ---
def main():
    """
    Main function to run the Streamlit application.
    Handles file uploading, data processing, graph generation, and visualization.
    """
    # --- Sidebar for File Upload and Controls ---
    st.sidebar.header("Controls")
    uploaded_file = st.sidebar.file_uploader(
        "Upload JSON data",
        type=["json"],
        help="Upload a JSON file containing relationship data. If no file is uploaded, a sample graph will be shown."
    )

    data_source = None
    source_name = ""

    if uploaded_file is not None:
        data_source = uploaded_file
        source_name = uploaded_file.name
        st.sidebar.info(f"Using uploaded file: '{source_name}'")
    else:
        sample_data_path = Path("assets/sample_data.json") # Adjusted path
        if sample_data_path.exists():
            st.sidebar.info("No file uploaded. Displaying sample knowledge graph.")
            data_source = str(sample_data_path) # Pass path to load_json_data
            source_name = "Sample Data"
        else:
            st.sidebar.warning("Sample data file not found (expected at assets/sample_data.json).")
            st.info("Please upload a JSON file to visualize the knowledge graph.")
            return # Exit if no data source is available

    # 1. Load Data
    if data_source:
        df = load_json_data(data_source)

        if not df.empty:
            st.sidebar.success(f"Data loaded successfully from '{source_name}'.")

            # 2. Validate Data
            if validate_data(df):
                st.sidebar.success("Data validation successful!")

                # 3. Clean Data
                cleaned_df = clean_data(df)
                if cleaned_df.empty and not df.empty: # Check if cleaning resulted in empty DF from non-empty
                    st.sidebar.warning("Data became empty after cleaning. Check for essential missing values.")
                    st.dataframe(df) # Show original df for context
                    return
                st.sidebar.write(f"Data cleaned. Rows remaining: {len(cleaned_df)}")

                # 4. Normalize Entities
                normalized_df = normalize_entities(cleaned_df)
                st.sidebar.write(f"Entities normalized. Total relationships: {len(normalized_df)}")

                if normalized_df.empty and not cleaned_df.empty : # Check if normalization resulted in empty
                     st.sidebar.warning("Data became empty after normalization.")
                     st.dataframe(cleaned_df) # Show cleaned df for context
                     return


                # Display processed data snippet in sidebar (optional)
                if st.sidebar.checkbox("Show processed data snippet"):
                    st.sidebar.dataframe(normalized_df.head())

                # 5. Create NetworkX Graph
                nx_graph = create_networkx_graph(normalized_df)
                if nx_graph.number_of_nodes() == 0 and not normalized_df.empty:
                    st.sidebar.error("Failed to create graph: No nodes were generated from the data.")
                    st.dataframe(normalized_df)
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
                if not isinstance(default_physics_dict, dict): # Ensure it's a dict
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
                current_physics_options = copy.deepcopy(default_physics_dict) # Start from a clean copy of defaults

                if 'barnesHut' not in current_physics_options: # Should be there from above check
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
                    Path(tmp_file.name).unlink() # Clean up the temporary file

                except Exception as e:
                    st.error(f"Error rendering graph: {e}")
                    # TODO: Log this error properly

            else:
                st.sidebar.error("Data validation failed. Please check the JSON structure and required fields.")
                st.warning(
                    "The uploaded JSON data does not meet the required format. "
                    "Ensure it's a list of records with 'head', 'relation', and 'tail' fields. "
                    "Other fields like 'head_type' and 'tail_type' are recommended."
                )
                if st.checkbox("Show raw data for debugging"):
                    st.dataframe(df)
        else:
            st.sidebar.error("Failed to load or parse JSON data. The file might be empty, malformed, or not a valid JSON list of records.")
            # Attempt to read and display raw content if it was an uploaded file and loading failed
            if uploaded_file is not None and df.empty: # only if it was an actual uploaded file
                uploaded_file.seek(0) 
                try:
                    raw_content = uploaded_file.read().decode()
                    if st.checkbox("Show raw file content for debugging (first 1000 chars)"):
                        st.text_area("Raw File Content:", raw_content[:1000], height=200)
                except Exception as e:
                    st.sidebar.warning(f"Could not read raw file content: {e}")
            elif df.empty and source_name == "Sample Data":
                 st.sidebar.error(f"Failed to load or parse the sample JSON data from '{str(sample_data_path)}'.")

    # This else block for 'if data_source:' is implicitly handled by the return if sample_data.json not found
    # and no file is uploaded. If a file IS uploaded but load_json_data returns empty, it's handled above.

if __name__ == "__main__":
    main()
