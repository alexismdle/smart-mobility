DEFAULT_NODE_COLOR = "#D3D3D3"
DEFAULT_NODE_SIZE = 20

from typing import Optional


def style_nodes(pyvis_graph, nx_graph, settings: Optional[dict] = None):
    for pv_node in pyvis_graph.nodes:
        node_id = pv_node['id']
        node_data = nx_graph.nodes.get(node_id, {})
        node_type = node_data.get('type', 'unknown')
        
        pv_node['color'] = DEFAULT_NODE_COLOR
        pv_node['size'] = DEFAULT_NODE_SIZE
        pv_node['title'] = f"ID: {node_id}\nType: {node_type}"
