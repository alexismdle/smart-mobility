import matplotlib.pyplot as plt
import networkx as nx

DEFAULT_NODE_COLOR = "#ADD8E6"  # Light Blue
DEFAULT_NODE_SIZE = 1000
DEFAULT_FONT_SIZE = 8
DEFAULT_FONT_WEIGHT = "bold"
DEFAULT_FONT_COLOR = "white" # For node labels
DEFAULT_ARROW_SIZE = 20
DEFAULT_EDGE_COLOR = "#D3D3D3" # Light Gray
DEFAULT_FIGURE_SIZE = (19, 15)
DEFAULT_LAYOUT = "spring"

def draw_graph_matplotlib(
    graph,
    output_path="graph.png",
    layout_type=DEFAULT_LAYOUT,
    node_color=DEFAULT_NODE_COLOR,
    node_size=DEFAULT_NODE_SIZE,
    font_size=DEFAULT_FONT_SIZE,
    font_weight=DEFAULT_FONT_WEIGHT,
    font_color=DEFAULT_FONT_COLOR,
    arrow_size=DEFAULT_ARROW_SIZE,
    edge_color=DEFAULT_EDGE_COLOR,
    figure_size=DEFAULT_FIGURE_SIZE,
    title="Knowledge Graph",
    background_color="#222222",
):
    """
    Draws a NetworkX graph using Matplotlib and saves it to a file.

    Args:
        graph (nx.Graph): The NetworkX graph to draw.
        output_path (str): The path to save the output image.
        layout_type (str): The layout algorithm to use (e.g., "spring", "circular", "kamada_kawai").
        node_color (str): Color of the nodes.
        node_size (int): Size of the nodes.
        font_size (int): Font size for labels.
        font_weight (str): Font weight for labels.
        arrow_size (int): Size of the arrows for directed graphs.
        figure_size (tuple): Size of the Matplotlib figure (width, height).
        title (str): Title of the graph.
    """
    if not graph or not graph.nodes():
        print("Error: Graph is empty or None. Cannot draw.")
        return

    fig, ax = plt.subplots(figsize=figure_size)
    ax.set_facecolor(background_color)
    fig.patch.set_facecolor(background_color) # Also set figure background

    # Determine layout
    # Scaling of positions is generally handled by NetworkX's layout functions
    # and Matplotlib's plotting, relative to the figure size.
    if layout_type == "spring":
        pos = nx.spring_layout(graph)
    elif layout_type == "circular":
        pos = nx.circular_layout(graph)
    elif layout_type == "kamada_kawai":
        pos = nx.kamada_kawai_layout(graph)
    elif layout_type == "random":
        pos = nx.random_layout(graph)
    elif layout_type == "shell":
        pos = nx.shell_layout(graph)
    elif layout_type == "spectral":
        pos = nx.spectral_layout(graph)
    else:
        print(f"Warning: Unknown layout type '{layout_type}'. Using spring layout as default.")
        pos = nx.spring_layout(graph)

    nx.draw(
        graph,
        pos,
        ax=ax, # Draw on the specified Axes object
        with_labels=True,
        node_color=node_color,
        node_size=node_size,
        font_size=font_size,
        font_weight=font_weight,
        font_color=font_color, # Added font_color for labels
        edge_color=edge_color, # Added edge_color
        arrowsize=arrow_size,
    )
    ax.set_title(title, color=font_color) # Set title color for dark background

    try:
        plt.savefig(output_path, facecolor=fig.get_facecolor()) # Ensure figure background is used in saved image
        print(f"Graph saved to {output_path}")
    except Exception as e:
        print(f"Error saving graph to {output_path}: {e}")
    finally:
        plt.close(fig) # Close the specific figure

if __name__ == "__main__":
    # Example usage (optional, for testing the visualizer directly)
    # Create a sample graph
    sample_graph = nx.DiGraph()
    sample_graph.add_edges_from([("A", "B"), ("B", "C"), ("A", "C"), ("C", "D")])

    # Add some node attributes for demonstration, if your graph creation logic does
    for node in sample_graph.nodes():
        sample_graph.nodes[node]['label'] = f"Node {node}" # Example label

    print("Drawing sample graph with new default dark theme settings...")
    draw_graph_matplotlib(sample_graph, output_path="sample_dark_default.png")

    print("Drawing sample graph with circular layout and overridden light background...")
    draw_graph_matplotlib(sample_graph,
                          output_path="sample_circular_light_bg.png",
                          layout_type="circular",
                          node_color="skyblue", # Default for light bg
                          font_color="black",
                          edge_color="gray",
                          background_color="white",
                          title="Sample - Circular on Light BG")

    print("Drawing sample graph with Kamada-Kawai layout and custom dark theme styling...")
    draw_graph_matplotlib(
        sample_graph,
        output_path="sample_kamada_custom_dark.png",
        layout_type="kamada_kawai",
        node_color="lightcoral", # Custom node color
        node_size=1200,
        font_size=10,
        font_color="white",
        edge_color="silver",
        arrow_size=25,
        title="Custom Styled Sample Graph (Dark Theme)"
    )
    print("Sample graphs drawn. Check for 'sample_dark_default.png', 'sample_circular_light_bg.png', and 'sample_kamada_custom_dark.png'.")
