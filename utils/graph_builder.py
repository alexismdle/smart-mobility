import networkx as nx
import pandas as pd


def create_networkx_graph(df: pd.DataFrame):
    """
    Creates a NetworkX MultiDiGraph from a pandas DataFrame.

    The DataFrame is expected to have columns: 'head', 'head_type',
    'relation', 'tail', 'tail_type'.

    Args:
        df: A pandas DataFrame containing the graph data.

    Returns:
        A networkx.MultiDiGraph object. Returns an empty graph if the
        input DataFrame is empty or None.
    """
    if df is None or df.empty:
        # TODO: Log or print a message about empty input DataFrame
        return nx.MultiDiGraph()

    graph = nx.MultiDiGraph()

    # Expected columns - ensure they exist, though prior validation should catch this
    required_cols = ['head', 'head_type', 'relation', 'tail', 'tail_type']
    if not all(col in df.columns for col in required_cols):
        # TODO: Log a warning or raise an error if essential columns are missing
        # This indicates an issue upstream, as data validation should precede this.
        # For now, returning an empty graph to prevent runtime errors.
        print(f"Warning: Input DataFrame is missing one or more required columns: {required_cols}")
        return nx.MultiDiGraph()

    for _, row in df.iterrows():
        head = row['head']
        head_type = row['head_type']
        relation = row['relation']
        tail = row['tail']
        tail_type = row['tail_type']

        # Add nodes with their types. NetworkX handles existing nodes gracefully.
        # If node exists, new attributes might overwrite or be ignored based on NX version/behavior.
        # It's generally fine for 'type' if consistent.
        if head not in graph:
            graph.add_node(head, type=head_type)
        else:
            # Optionally update type if it was different or not set,
            # or ensure consistency. For now, assume first encountered type is used.
            # If type can vary, this might need more sophisticated handling.
            if 'type' not in graph.nodes[head] or graph.nodes[head].get('type') == "Unknown":
                 graph.nodes[head]['type'] = head_type


        if tail not in graph:
            graph.add_node(tail, type=tail_type)
        else:
            if 'type' not in graph.nodes[tail] or graph.nodes[tail].get('type') == "Unknown":
                graph.nodes[tail]['type'] = tail_type

        # Add a directed edge with the relation type as an attribute
        graph.add_edge(head, tail, relation=relation)

    # Calculate and store degree for each node
    for node_id in list(graph.nodes()): # Iterate over a copy of node list if modifying attributes
        degree = graph.degree(node_id)
        graph.nodes[node_id]['degree'] = degree
        graph.nodes[node_id]['connection_count'] = degree # Alias for user-friendliness

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
        # Apply physics options even to an empty graph if they are in settings
        if settings.get('physics_options'):
            pyvis_empty_graph.set_options(settings['physics_options'])
        return pyvis_empty_graph

    pyvis_graph = Network(height="750px", width="100%", directed=True, notebook=False)

    # Apply physics options from settings
    # Prioritize the JSON string if available and valid, as constructed by app.py
    physics_json_string = settings.get('pyvis_physics_options_json_string')
    physics_dict = settings.get('pyvis_physics_options_dict')
    import json  # Ensure json is imported

    applied_physics = False
    if physics_json_string:
        try:
            # Validate if it's proper JSON before passing
            json.loads(physics_json_string) # This will raise error if not valid JSON
            pyvis_graph.set_options(physics_json_string)
            applied_physics = True
        except json.JSONDecodeError:
            # This error should ideally be caught in app.py or logged
            # For now, if it occurs, we can try to fall back to the dict.
            # In a Streamlit context, st.error might not be ideal here if this is a library function.
            # Consider logging instead.
            print("Error: Invalid JSON in physics_options_json_string. Trying dict fallback.") # Changed to print
            # st.error("Error: Invalid JSON in physics options string from settings.") # Avoid st call here

    if not applied_physics and isinstance(physics_dict, dict) and physics_dict:
        # Fallback to dict if string wasn't applied and dict is valid
        # Pyvis Network.set_options can also take a dictionary directly,
        # but it needs to be structured correctly (e.g. options.physics = physics_dict)
        # The most straightforward way if physics_dict is already structured like vis.js options:
        # pyvis_graph.options.physics = physics_dict
        # However, set_options expects a JSON string. So, if we have a dict, convert it.
        try:
            json_string_from_dict = json.dumps({"physics": physics_dict}) # Wrap it in "physics" key
            pyvis_graph.set_options(json_string_from_dict)
            applied_physics = True
        except TypeError:
            print("Error: Could not serialize physics_options_dict to JSON.")
            # st.error("Error: Could not serialize physics_options_dict to JSON.")


    if not applied_physics:
        # Fallback to very basic default if nothing good was passed
        # This ensures the graph at least tries to render with some physics
        default_fallback_physics_json = APP_SETTINGS.get('pyvis_physics_options_json_string', '{}')
        try:
            json.loads(default_fallback_physics_json)
            pyvis_graph.set_options(default_fallback_physics_json)
        except json.JSONDecodeError:
             print("Error: Default JSON string from APP_SETTINGS is also invalid.")
             # As a last resort, enable basic physics if nothing else worked
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