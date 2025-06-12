from pathlib import Path
# import matplotlib.pyplot as plt # No longer directly used here
# import networkx as nx # No longer directly used here for drawing

from utils.data_processor import load_json_data, validate_data
from utils.graph_builder import create_networkx_graph
from utils.matplotlib_visualizer import draw_graph_matplotlib

def main():
    sample_data_path = Path("assets/sample_data.json")
    output_image_path = Path("knowledge_graph.png") # Output path for the graph image

    if not sample_data_path.exists():
        print(f"Error: Sample data not found at {sample_data_path}")
        return

    edges_df, node_info_map = load_json_data(sample_data_path)

    if not validate_data(edges_df) or not node_info_map:
        print("Error: Invalid data format. Ensure JSON has valid nodes and edges.")
        return

    nx_graph = create_networkx_graph(edges_df, node_info_map)

    # The check for nx_graph is now inside draw_graph_matplotlib
    # No need to explicitly check here if nx_graph is None or empty,
    # as the visualizer function handles it.

    # Use the new visualizer function
    draw_graph_matplotlib(
        nx_graph,
        output_path=str(output_image_path), # Ensure output_path is a string
        layout_type="spring", # Example: specify layout
        title="Knowledge Graph from App"
    )
    # The print statement for success is now inside draw_graph_matplotlib

if __name__ == "__main__":
    main()
