import matplotlib.pyplot as plt
import networkx as nx

DEFAULT_NODE_COLOR = "skyblue"
DEFAULT_NODE_SIZE = 700
DEFAULT_FONT_SIZE = 8
DEFAULT_FONT_WEIGHT = "bold"
DEFAULT_ARROW_SIZE = 20
DEFAULT_FIGURE_SIZE = (12, 12)
DEFAULT_LAYOUT = "spring"

def draw_graph_matplotlib(
    graph,
    output_path="graph.png",
    layout_type=DEFAULT_LAYOUT,
    node_color=DEFAULT_NODE_COLOR,
    node_size=DEFAULT_NODE_SIZE,
    font_size=DEFAULT_FONT_SIZE,
    font_weight=DEFAULT_FONT_WEIGHT,
    arrow_size=DEFAULT_ARROW_SIZE,
    figure_size=DEFAULT_FIGURE_SIZE,
    title="Knowledge Graph",
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

    plt.figure(figsize=figure_size)

    # Determine layout
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
        with_labels=True,
        node_color=node_color,
        node_size=node_size,
        font_size=font_size,
        font_weight=font_weight,
        arrowsize=arrow_size,
    )
    plt.title(title)

    try:
        plt.savefig(output_path)
        print(f"Graph saved to {output_path}")
    except Exception as e:
        print(f"Error saving graph to {output_path}: {e}")
    finally:
        plt.close() # Close the figure to free memory

if __name__ == "__main__":
    # Example usage (optional, for testing the visualizer directly)
    # Create a sample graph
    sample_graph = nx.DiGraph()
    sample_graph.add_edges_from([("A", "B"), ("B", "C"), ("A", "C"), ("C", "D")])

    # Add some node attributes for demonstration, if your graph creation logic does
    for node in sample_graph.nodes():
        sample_graph.nodes[node]['label'] = f"Node {node}" # Example label

    print("Drawing sample graph with default settings...")
    draw_graph_matplotlib(sample_graph, output_path="sample_default.png")

    print("Drawing sample graph with circular layout...")
    draw_graph_matplotlib(sample_graph, output_path="sample_circular.png", layout_type="circular", node_color="lightgreen")

    print("Drawing sample graph with Kamada-Kawai layout and custom styling...")
    draw_graph_matplotlib(
        sample_graph,
        output_path="sample_kamada_custom.png",
        layout_type="kamada_kawai",
        node_color="salmon",
        node_size=1000,
        font_size=10,
        arrow_size=30,
        title="Custom Styled Sample Graph"
    )
    print("Sample graphs drawn.")
