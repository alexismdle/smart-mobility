import networkx as nx
import pandas as pd


def create_networkx_graph(edges_df: pd.DataFrame, node_info: dict):
    """
    Creates a NetworkX MultiDiGraph from a pandas DataFrame of edges
    and a dictionary of node information.

    The edges_df is expected to have columns: 'head', 'relation', 'tail'.
    'head_type' and 'tail_type' in edges_df are optional if node_info is comprehensive.
    The node_info dictionary maps node IDs to their type and attributes:
    {node_id: {'type': 'some_type', 'attributes': [...]}}

    Args:
        edges_df: A pandas DataFrame containing the graph edge data.
        node_info: A dictionary containing node types and attributes.

    Returns:
        A networkx.MultiDiGraph object. Returns an empty graph if
        there's no node or edge data.
    """
    graph = nx.MultiDiGraph()

    # Add all nodes from node_info first
    if node_info:
        for node_id, data in node_info.items():
            graph.add_node(node_id,
                           type=data.get('type', 'unknown'),  # Use .get for safety
                           detailed_attributes=data.get('attributes', [])) # Use .get for safety

    # If there are no edges, we can return the graph with only nodes (if any)
    if edges_df is None or edges_df.empty:
        if not node_info: # No nodes and no edges
             # TODO: Log or print a message about empty input
            print("Info: No node or edge data provided to create_networkx_graph.")
        else: # Nodes exist, but no edges
            print("Info: No edges provided, graph will contain only nodes.")
        # Calculate degree for nodes even if there are no edges (all degrees will be 0)
        for node_id in list(graph.nodes()):
            degree = graph.degree(node_id)
            graph.nodes[node_id]['degree'] = degree
            graph.nodes[node_id]['connection_count'] = degree
        return graph

    # Process edges
    # Expected columns for edges_df - 'head_type' and 'tail_type' are less critical now
    # if nodes are added from node_info, but 'head', 'relation', 'tail' are essential.
    required_edge_cols = ['head', 'relation', 'tail']
    if not all(col in edges_df.columns for col in required_edge_cols):
        print(f"Warning: Edges DataFrame is missing one or more required columns: {required_edge_cols}. Cannot add edges.")
        # Still return the graph, it might contain nodes from node_info
        return graph

    for _, row in edges_df.iterrows():
        head = row['head']
        relation = row['relation']
        tail = row['tail']

        # Ensure head and tail nodes exist in the graph from node_info.
        # If not, they might be new nodes mentioned only in edges or node_info was incomplete.
        # NetworkX add_edge will add nodes if they don't exist, but without type/attributes from node_info.
        # It's better if node_info is the source of truth for all nodes.
        # For robustness, we can add them here if missing, using types from df if available.
        if head not in graph:
            head_type = row.get('head_type', 'unknown') # Fallback type
            graph.add_node(head, type=head_type, detailed_attributes=[])
            print(f"Warning: Head node '{head}' from edges was not in node_info. Added with type '{head_type}'.")

        if tail not in graph:
            tail_type = row.get('tail_type', 'unknown') # Fallback type
            graph.add_node(tail, type=tail_type, detailed_attributes=[])
            print(f"Warning: Tail node '{tail}' from edges was not in node_info. Added with type '{tail_type}'.")

        graph.add_edge(head, tail, relation=relation)

    # Calculate and store degree for each node (accounts for all nodes and edges)
    for node_id in list(graph.nodes()):
        degree = graph.degree(node_id)
        # Ensure 'degree' and 'connection_count' are updated or set for all nodes
        graph.nodes[node_id]['degree'] = degree
        graph.nodes[node_id]['connection_count'] = degree

    return graph


from pyvis.network import Network

from config.settings import (
    APP_SETTINGS,
    DEFAULT_EDGE_COLOR,
    DEFAULT_NODE_COLORS_BY_TYPE,
    DEFAULT_NODE_SIZE,
)
from utils.visualizer import style_nodes


def build_pyvis_graph(nx_graph: nx.MultiDiGraph, settings: dict = None):
    """
    Converts a NetworkX graph to a PyVis Network object and applies styling.

    Args:
        nx_graph: The NetworkX graph to convert.
        settings: A dictionary potentially containing styling and physics options.
                  Expected keys: 'node_colors_by_type', 'default_node_color',
                                 'default_edge_color', 'default_node_size',
                                 'physics_options'.

    Returns:
        A PyVis Network object.
    """
    if settings is None:
        # Use global APP_SETTINGS if no specific settings are passed
        settings = APP_SETTINGS

    if nx_graph is None or nx_graph.number_of_nodes() == 0:
        pyvis_empty_graph = Network(height="750px", width="100%", directed=True, notebook=False)
        # Complex physics settings removed for empty graph
        return pyvis_empty_graph

    pyvis_graph = Network(height="750px", width="100%", directed=True, notebook=False)

    # Complex physics configuration has been removed.
    # PyVis will use its default physics settings.
    # If a specific simple layout is desired in the future, it can be added here, e.g.:
    # pyvis_graph.force_atlas_2based(gravity=-50, central_gravity=0.01, spring_length=200, spring_strength=0.08, damping=0.4, overlap=0)
    # Or simply ensure physics are enabled if PyVis defaults are not sufficient:
    # pyvis_graph.options.physics.enabled = True
    # For now, relying on PyVis defaults which are generally good.

    # Populate PyVis graph from NetworkX graph
    # PyVis's from_nx attempts to carry over attributes.
    # For edges, it looks for 'title' (for hover), 'label' (for display), 'value' (for size), 'color'.
    # For nodes, it looks for 'title', 'label', 'shape', 'color', 'size'.
    # Our 'relation' on edges should become 'label' if not overridden.
    # Our 'type' on nodes is a custom attribute we'll use for styling.

    # We need to ensure edge labels are correctly mapped from 'relation' attribute.
    # We will create a temporary graph with 'label' attribute for edges.
    # This is because from_nx preferentially uses 'label' then 'title' for edge text.

    temp_nx_graph = nx_graph.copy()
    for u, v, k, data in temp_nx_graph.edges(data=True, keys=True):
        if 'relation' in data:
            temp_nx_graph.edges[u,v,k]['label'] = data['relation']
        if 'relation_type_from_edge_list' in data: # Compatibility with older versions
            temp_nx_graph.edges[u,v,k]['label'] = data['relation_type_from_edge_list']


    pyvis_graph.from_nx(temp_nx_graph) # Use the temp graph with 'label' for edges

    # Call style_nodes to apply node colors, default sizes, and potentially dynamic sizes
    style_nodes(
        pyvis_graph,
        nx_graph, # Pass the original nx_graph for attribute lookup
        node_colors_by_type=settings.get('node_colors_by_type', DEFAULT_NODE_COLORS_BY_TYPE),
        default_node_color=settings.get('default_node_color'),
        default_node_size=settings.get('default_node_size', DEFAULT_NODE_SIZE),
        size_metric=settings.get('node_size_metric'), # Pass the node_size_metric from settings
        size_multiplier=settings.get('node_size_multiplier', 5) # Default to 5 if not in settings
    )

    # Set default edge color - this part remains as it's edge-specific
    # and not covered by style_nodes
    current_default_edge_color = settings.get('default_edge_color', DEFAULT_EDGE_COLOR)
    for edge in pyvis_graph.edges:
        if 'color' not in edge or edge['color'] is None:
            edge['color'] = current_default_edge_color
        # Edge labels should be handled by the temp_nx_graph with 'label' attribute

    return pyvis_graph