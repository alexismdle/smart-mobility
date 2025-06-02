"""
Utility functions for styling and enhancing graph visualizations.
"""
from config.settings import (
    APP_SETTINGS,
    DEFAULT_NODE_COLORS_BY_TYPE,
    DEFAULT_NODE_SIZE,
)

# Min and Max node sizes for dynamic sizing to prevent extremes
MIN_NODE_SIZE = 5
MAX_NODE_SIZE = 75 # Increased from 50 to allow more visual distinction for high-metric nodes

def style_nodes(
    pyvis_graph,
    nx_graph,
    node_colors_by_type=None,
    default_node_color=None,
    default_node_size=None,
    size_metric=None,
    size_multiplier=5
):
    """
    Applies styling to nodes in a PyVis graph based on their attributes
    from the source NetworkX graph. Styles include color by type and
    dynamic sizing based on a specified metric.

    Args:
        pyvis_graph: The PyVis Network object to style.
        nx_graph: The NetworkX graph (source of truth for node attributes).
        node_colors_by_type (dict, optional): Mapping of node types to colors.
            Defaults to DEFAULT_NODE_COLORS_BY_TYPE from settings.
        default_node_color (str, optional): Default color for nodes if type not in map.
            Defaults to APP_SETTINGS['default_node_color'].
        default_node_size (int, optional): Default size for nodes.
            Defaults to DEFAULT_NODE_SIZE from settings.
        size_metric (str, optional): Node attribute from nx_graph to use for sizing
            (e.g., 'degree', 'centrality_score').
        size_multiplier (float, optional): Factor to scale the size_metric value.
    """
    if node_colors_by_type is None:
        node_colors_by_type = APP_SETTINGS.get('node_colors_by_type', DEFAULT_NODE_COLORS_BY_TYPE)

    if default_node_color is None:
        default_node_color = APP_SETTINGS.get('default_node_color', "#D3D3D3") # Fallback grey

    if default_node_size is None:
        default_node_size = APP_SETTINGS.get('default_node_size', DEFAULT_NODE_SIZE)

    for pv_node in pyvis_graph.nodes:
        node_id = pv_node['id']
        try:
            nx_node_attributes = nx_graph.nodes[node_id]
        except KeyError:
            # This can happen if pyvis_graph nodes and nx_graph nodes are out of sync.
            # Should not occur if pyvis_graph was generated from nx_graph correctly.
            # TODO: Log a warning here
            pv_node['color'] = default_node_color
            pv_node['size'] = default_node_size
            pv_node['title'] = "Error: Node data not found in source graph"
            continue

        node_type = nx_node_attributes.get('type', 'unknown')

        # Set color
        pv_node['color'] = node_colors_by_type.get(node_type.lower(), default_node_color) # Use .lower() for case-insensitivity

        # Set title (hover text)
        base_title = f"ID: {node_id}\nType: {node_type}"
        if size_metric and size_metric in nx_node_attributes:
            metric_val = nx_node_attributes.get(size_metric, 0)
            base_title += f"\n{size_metric.replace('_', ' ').capitalize()}: {metric_val:.2f}" # Format metric name and value

        # Append other attributes to title if needed
        # Example: pv_node['title'] = base_title + f"\nDetails: {nx_node_attributes.get('details', 'N/A')}"
        pv_node['title'] = base_title


        # Node Sizing
        current_node_size = float(default_node_size) # Ensure base size is float
        if size_metric and size_metric in nx_node_attributes:
            metric_value = 0.0
            try:
                metric_value = float(nx_node_attributes.get(size_metric, 0.0))
            except (ValueError, TypeError):
                # TODO: Log a warning if metric value is not convertible to float
                pass # Keep metric_value as 0.0

            # Ensure metric_value is a number before multiplication
            if isinstance(metric_value, (int, float)): # Redundant check if try-except passes, but safe
                # Scale size: start from a base and add proportional size
                calculated_size = current_node_size + (metric_value * float(size_multiplier))
                current_node_size = max(float(MIN_NODE_SIZE), min(calculated_size, float(MAX_NODE_SIZE)))
            # else case already handled by metric_value defaulting to 0.0 or previous value

        pv_node['size'] = float(current_node_size) # Ensure final size is float