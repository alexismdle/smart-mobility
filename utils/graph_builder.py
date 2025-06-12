import networkx as nx
import networkx.community as nx_comm
import pandas as pd
import json


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


def limit_graph_nodes_by_degree(graph: nx.MultiDiGraph, max_nodes: int = 0) -> nx.MultiDiGraph:
    """
    Limits the number of nodes in the graph based on node degree.

    Args:
        graph: The input NetworkX MultiDiGraph. Assumes nodes have a 'degree' attribute.
        max_nodes: The maximum number of nodes to keep. If 0 or greater than
                   current number of nodes, the original graph is returned.

    Returns:
        A new NetworkX MultiDiGraph containing the top N nodes by degree,
        or a copy of the original graph if no limiting is applied.
    """
    if graph is None:
        return nx.MultiDiGraph() # Return an empty graph if input is None

    num_original_nodes = graph.number_of_nodes()

    if max_nodes <= 0 or max_nodes >= num_original_nodes:
        return graph.copy() # Return a copy of the original graph

    if num_original_nodes == 0:
        return graph.copy() # Return a copy if graph is already empty

    # Get nodes and their degrees. Fallback to 0 if 'degree' is missing for some reason.
    node_degrees = [(n, graph.nodes[n].get('degree', 0)) for n in graph.nodes()]

    # Sort nodes by degree in descending order
    sorted_nodes_by_degree = sorted(node_degrees, key=lambda x: x[1], reverse=True)

    # Select the top max_nodes
    selected_node_ids = [node_id for node_id, degree in sorted_nodes_by_degree[:max_nodes]]

    # Create and return a subgraph containing only these selected nodes
    # The .copy() is important to ensure it's a new graph object with its own data.
    subgraph = graph.subgraph(selected_node_ids).copy()

    # Node attributes (like 'degree', 'type', 'connection_count', 'detailed_attributes')
    # are preserved by graph.subgraph(). Edges between these nodes are also preserved.
    # If degree *within the subgraph* was needed, it would need recalculation,
    # but for ranking purposes, original degree is typically used.

    return subgraph


def assign_node_communities(graph: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """
    Assigns a community ID to each node in the graph using a community detection algorithm.

    Args:
        graph: The input NetworkX MultiDiGraph.

    Returns:
        The graph with an added 'community_id' attribute for each node.
        Returns the original graph if it's empty, too small, or if detection fails.
    """
    if graph is None or graph.number_of_nodes() < 2 or graph.number_of_edges() == 0:
        # Community detection is not meaningful for empty or very small graphs,
        # or graphs with no edges.
        # print("Info: Graph is too small or has no edges for community detection.")
        return graph

    try:
        # Using greedy_modularity_communities. It works on an undirected view of the graph.
        # Convert the graph to undirected for this algorithm, as it's typical.
        # This algorithm returns a list of frozensets, where each frozenset is a community.
        if graph.is_directed():
            undirected_graph = graph.to_undirected()
        else:
            undirected_graph = graph # Already undirected, no need to convert

        # Check if the undirected graph still has edges, as to_undirected() might change this
        # if the original directed graph had only non-reciprocal edges that formed no structure
        # when direction is ignored (though unlikely for typical MultiDiGraphs from create_networkx_graph).
        if undirected_graph.number_of_edges() == 0:
            # print("Info: Undirected view of the graph has no edges for community detection.")
            return graph

        communities = list(nx_comm.greedy_modularity_communities(undirected_graph))

        if not communities:
            # print("Warning: No communities found.")
            return graph

        # Assign community_id to each node
        for community_index, community_nodes in enumerate(communities):
            for node_id in community_nodes:
                if node_id in graph.nodes: # Ensure node exists in original graph
                    graph.nodes[node_id]['community_id'] = community_index
                else:
                    # This case should ideally not happen if communities are derived from the graph.
                    print(f"Warning: Node {node_id} from community detection not found in original graph.")

        # print(f"Info: Assigned {len(communities)} communities to nodes.")

    except Exception as e:
        # Catch any error during community detection (e.g., algorithm specific issues)
        print(f"Warning: Community detection failed: {e}. Returning original graph.")
        # Optionally, log the error e

    return graph


from pyvis.network import Network

from config.settings import (
    APP_SETTINGS,
    DEFAULT_EDGE_COLOR,
    DEFAULT_NODE_COLORS_BY_TYPE,
    DEFAULT_NODE_SIZE,
)
from utils.visualizer import style_nodes


def build_pyvis_graph(nx_graph: nx.MultiDiGraph, settings: dict, solver_type: str):
    """
    Converts a NetworkX graph to a PyVis Network object and applies styling and physics.

    Args:
        nx_graph: The NetworkX graph to convert.
        settings: A dictionary containing styling and physics configurations.
                  Expected keys: 'node_colors_by_type', 'default_node_color',
                                 'default_edge_color', 'default_node_size',
                                 'pyvis_barnesHut_options',
                                 'pyvis_forceatlas2based_options'.
        solver_type: The type of physics solver to use ('barnesHut' or 'forceAtlas2Based').

    Returns:
        A PyVis Network object.
    """
    if nx_graph is None or nx_graph.number_of_nodes() == 0:
        pyvis_empty_graph = Network(height="750px", width="100%", directed=True, notebook=False)
        # No physics settings needed for an empty graph
        return pyvis_empty_graph

    pyvis_graph = Network(height="750px", width="100%", directed=True, notebook=False)

    # Select and apply physics options based on solver_type
    physics_options = None
    if solver_type == 'barnesHut':
        physics_options = settings.get('pyvis_barnesHut_options')
    elif solver_type == 'forceAtlas2Based':
        physics_options = settings.get('pyvis_forceatlas2based_options')

    if physics_options:
        # PyVis set_options expects a JSON string or a dict.
        # The structure should be like: {"physics": { ...solver_specific_options... }}
        # Our current dictionaries are already structured correctly.
        options_str = json.dumps({"physics": physics_options})
        pyvis_graph.set_options(options_str)
        # Ensure physics are enabled (though already in our dicts)
        # The set_options call above should handle this if "enabled": True is in the dict.
        # Forcing it here might be redundant if options_str is correctly structured.
        # pyvis_graph.options.physics.enabled = True
    else:
        # Fallback or default behavior if solver_type is unknown or options are missing
        # PyVis will use its default physics settings if not explicitly set.
        # print(f"Warning: Physics options for solver '{solver_type}' not found. Using PyVis defaults.")
        # Enable basic physics if nothing else is specified.
        pyvis_graph.options.physics.enabled = True


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
    # The 'settings' dictionary is passed directly, style_nodes will extract what it needs.
    style_nodes(
        pyvis_graph,
        nx_graph, # Pass the original nx_graph for attribute lookup
        settings=settings
    )

    # Set default edge color - this part remains as it's edge-specific
    # and not covered by style_nodes
    # Update edge styling
    default_edge_color_val = settings.get('default_edge_color', DEFAULT_EDGE_COLOR) # Fallback to global default
    edge_highlight_color = settings.get('edge_color_highlight', '#FF0000') # Fallback red
    edge_hover_color = settings.get('edge_color_hover', '#E0E0E0') # Fallback light grey
    edge_smooth_type = settings.get('default_edge_smooth_type', 'dynamic')
    # edge_width is now specifically set from settings in app.py, defaults handled there.
    default_edge_width = settings.get('default_edge_weight', 1) # Fallback from APP_SETTINGS
    current_edge_width = settings.get('edge_width', default_edge_width)


    for edge in pyvis_graph.edges:
        # Set base color if not already set (e.g. by from_nx if 'color' attribute existed)
        # Then structure it for highlight/hover
        base_color = edge.get('color', default_edge_color_val)
        if isinstance(base_color, dict): # Already has structure, ensure our keys are there
            base_color.setdefault('highlight', edge_highlight_color)
            base_color.setdefault('hover', edge_hover_color)
            # ensure the main 'color' key is present if it was a dict but malformed
            base_color.setdefault('color', default_edge_color_val)
        else: # Is a simple color string, or None
            edge['color'] = {
                'color': base_color if base_color is not None else default_edge_color_val,
                'highlight': edge_highlight_color,
                'hover': edge_hover_color
            }

        # Set edge width
        edge['width'] = current_edge_width

        # Set edge smoothness
        # PyVis expects smooth to be a boolean or a dictionary like {'type': 'dynamic'}
        if isinstance(edge_smooth_type, str): # If it's just a string, wrap it
             edge['smooth'] = {'type': edge_smooth_type, 'roundness': 0.5} # default roundness
        elif isinstance(edge_smooth_type, dict): # If it's already a dict
             edge['smooth'] = edge_smooth_type
        else: # boolean or other, directly assign
             edge['smooth'] = edge_smooth_type


        # Edge labels ('label' attribute) are handled by the temp_nx_graph passed to from_nx.
        # Tooltip ('title' attribute) can also be set here if desired, e.g. from edge attributes in nx_graph.
        # Example: edge['title'] = f"Relation: {edge.get('label', 'N/A')}"

    return pyvis_graph