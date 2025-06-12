from typing import Optional

import networkx as nx
import pandas as pd
# from pyvis.network import Network # Removed
# from utils.visualizer import style_nodes # Removed


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

# Removed build_pyvis_graph function as Pyvis is no longer used.
