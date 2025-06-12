"""
Utility functions for styling and enhancing graph visualizations.
"""
from config.settings import (
    APP_SETTINGS,
    DEFAULT_NODE_COLORS_BY_TYPE,
    DEFAULT_NODE_SIZE,
    DEFAULT_COMMUNITY_COLORS, # Import the new default community colors
)
import random # For generating random colors if needed

# Min and Max node sizes for dynamic sizing to prevent extremes
MIN_NODE_SIZE = 5
MAX_NODE_SIZE = 75 # Increased from 50 to allow more visual distinction for high-metric nodes

def generate_random_color():
    """Generates a random hex color."""
    return f"#{random.randint(0, 0xFFFFFF):06x}"

def style_nodes(
    pyvis_graph,
    nx_graph,
    settings: dict
):
    """
    Applies styling to nodes in a PyVis graph based on their attributes
    from the source NetworkX graph using settings provided in the dictionary.
    Styles include color by type or community, and dynamic sizing.

    Args:
        pyvis_graph: The PyVis Network object to style.
        nx_graph: The NetworkX graph (source of truth for node attributes).
        settings (dict): A dictionary containing styling parameters like:
            'node_colors_by_type', 'default_node_color', 'default_node_size',
            'size_metric', 'node_size_multiplier', 'color_by_community',
            'default_community_colors'.
    """
    node_colors_by_type = settings.get('node_colors_by_type', DEFAULT_NODE_COLORS_BY_TYPE)
    default_node_color = settings.get('default_node_color', "#D3D3D3") # Fallback grey
    default_node_size = settings.get('default_node_size', DEFAULT_NODE_SIZE)
    size_metric = settings.get('node_size_metric') # Note: 'node_size_metric' from APP_SETTINGS
    size_multiplier = settings.get('node_size_multiplier', 5)

    color_by_community = settings.get('color_by_community', False)
    community_colors_list = settings.get('default_community_colors', DEFAULT_COMMUNITY_COLORS)

    if not community_colors_list: # Fallback if list is empty or not provided
        community_colors_list = [generate_random_color() for _ in range(20)] # Generate 20 random colors

    for pv_node in pyvis_graph.nodes:
        node_id = pv_node['id']
        try:
            nx_node_attributes = nx_graph.nodes[node_id]
        except KeyError:
            pv_node['color'] = default_node_color
            pv_node['size'] = default_node_size
            pv_node['title'] = f"Error: Node ID {node_id} not found in source graph"
            continue

        node_type = nx_node_attributes.get('type', 'unknown')
        community_id = nx_node_attributes.get('community_id')

        # Color assignment logic
        assigned_color = False
        if color_by_community and community_id is not None:
            if community_colors_list: # Ensure list is not empty
                pv_node['color'] = community_colors_list[community_id % len(community_colors_list)]
                assigned_color = True
            else: # Should not happen if DEFAULT_COMMUNITY_COLORS is populated
                pv_node['color'] = default_node_color # Fallback
                # print(f"Warning: Community colors list is empty. Using default for node {node_id}.")
                assigned_color = True # Technically assigned, but to default

        if not assigned_color:
            pv_node['color'] = node_colors_by_type.get(node_type.lower(), default_node_color)

        # Set title (hover text)
        base_title = f"ID: {node_id}\nType: {node_type}"
        if community_id is not None:
            base_title += f"\nCommunity ID: {community_id}"

        if size_metric and size_metric in nx_node_attributes:
            metric_val = nx_node_attributes.get(size_metric, 0)
            try:
                # Ensure metric_val is formatted, handling potential non-numeric gracefully
                base_title += f"\n{size_metric.replace('_', ' ').capitalize()}: {float(metric_val):.2f}"
            except (ValueError, TypeError):
                base_title += f"\n{size_metric.replace('_', ' ').capitalize()}: {metric_val}"


        pv_node['title'] = base_title

        # Node Sizing
        current_node_size = float(default_node_size)
        if size_metric and size_metric in nx_node_attributes:
            metric_value = 0.0
            try:
                metric_value = float(nx_node_attributes.get(size_metric, 0.0))
            except (ValueError, TypeError):
                pass

            if isinstance(metric_value, (int, float)):
                calculated_size = current_node_size + (metric_value * float(size_multiplier))
                current_node_size = max(float(MIN_NODE_SIZE), min(calculated_size, float(MAX_NODE_SIZE)))

        pv_node['size'] = float(current_node_size)