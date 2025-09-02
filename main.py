'''
Generate a graph (ontology) representation of the NeTeX part one
This project use graphml, lxml, networkx
'''

from lxml import etree
from pathlib import Path
import networkx as nx

NS = {"xs": "http://www.w3.org/2001/XMLSchema"}
SCHEMA_CACHE = {}

def parse_xsd(xsd_path: Path):
    tree = etree.parse(str(xsd_path))
    SCHEMA_CACHE[xsd_path] = tree
    return SCHEMA_CACHE[xsd_path]

def save_graphml(graph: nx.Graph, output_path: Path):
    nx.write_graphml(graph, str(output_path))

def visualize_graph(graph: nx.Graph):
    import matplotlib.pyplot as plt
    pos = nx.spring_layout(graph)
    nx.draw(graph, pos, with_labels=True)
    plt.show()

if __name__ == "__main__":
    xsd_path = Path("data/")
    graph = parse_xsd(xsd_path)
    visualize_graph(graph)
    save_graphml(graph, Path("output.graphml"))