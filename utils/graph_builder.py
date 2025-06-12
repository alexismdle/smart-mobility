from typing import Optional

import networkx as nx
import pandas as pd
from pyvis.network import Network

from utils.visualizer import style_nodes


def create_networkx_graph(edges_df: pd.DataFrame, node_info: Optional[dict] = None):
    graph = nx.MultiDiGraph()
    
    if node_info:
        for node_id, data in node_info.items():
            graph.add_node(node_id, type=data.get('type', 'unknown'))

    if edges_df is None or edges_df.empty:
        return graph

    if not all(col in edges_df.columns for col in ['head', 'relation', 'tail']):
        return graph

    for _, row in edges_df.iterrows():
        head, relation, tail = row['head'], row['relation'], row['tail']
        if head not in graph:
            graph.add_node(head)
        if tail not in graph:
            graph.add_node(tail)
        graph.add_edge(head, tail, relation=relation)

    return graph

def build_pyvis_graph(nx_graph: nx.MultiDiGraph):
    net = Network(height="600px", width="100%", directed=True)
    if nx_graph and nx_graph.number_of_nodes() > 0:
        for u, v, data in nx_graph.edges(data=True):
            label = data.get('relation', '')
            net.add_edge(u, v, label=label)
        for node in nx_graph.nodes(data=True):
            net.add_node(node[0], label=str(node[0]))
        style_nodes(net, nx_graph) 
    return net
