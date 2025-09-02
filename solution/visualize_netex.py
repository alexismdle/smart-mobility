import argparse
from lxml import etree
from pathlib import Path
import networkx as nx
from pyvis.network import Network
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# XML namespace for XSD
XSD_NAMESPACE = "http://www.w3.org/2001/XMLSchema"
ns = {'xsd': XSD_NAMESPACE}

def find_xsd_files(directory):
    """Find all XSD files in a directory."""
    return list(Path(directory).rglob("*.xsd"))

def parse_xsd_file(file_path, graph, substitution_groups):
    """Parse a single XSD file and populate the graph and substitution groups."""
    try:
        tree = etree.parse(str(file_path))
        # Find all top-level element definitions
        for element in tree.xpath("//xsd:element[@name]", namespaces=ns):
            element_name = element.get("name")
            graph.add_node(element_name, title=f"Defined in: {file_path.name}")

            # Handle substitution groups
            if element.get("substitutionGroup"):
                head = element.get("substitutionGroup").split(':')[-1]
                if head not in substitution_groups:
                    substitution_groups[head] = []
                substitution_groups[head].append(element_name)
                graph.add_edge(head, element_name, label="substitution")

            # Find child elements within complex types
            for child in element.xpath(".//xsd:element[@ref]", namespaces=ns):
                child_ref = child.get("ref").split(':')[-1]
                graph.add_edge(element_name, child_ref, label="composition")

        # Find parent-child relationships from complex types to elements
        for complex_type in tree.xpath("//xsd:complexType[@name]", namespaces=ns):
            type_name = complex_type.get("name")
            for child in complex_type.xpath(".//xsd:element[@ref]", namespaces=ns):
                child_ref = child.get("ref").split(':')[-1]
                # Find elements that use this complex type
                for user_element in tree.xpath(f"//xsd:element[@type='{type_name}' or @type='netex:{type_name}']", namespaces=ns):
                    user_element_name = user_element.get("name")
                    graph.add_edge(user_element_name, child_ref, label="composition")

    except etree.XMLSyntaxError as e:
        logging.error(f"Error parsing {file_path}: {e}")

def resolve_substitution_groups(graph, substitution_groups):
    """Resolve substitution groups by adding edges to the graph."""
    for head, members in substitution_groups.items():
        if head in graph:
            # Find all parents of the substitution group head
            parents = list(graph.predecessors(head))
            for parent in parents:
                for member in members:
                    if member in graph:
                        # Add edge from parent to each member of the substitution group
                        graph.add_edge(parent, member, label="substitution")

def main(directory, output_file):
    """Main function to generate the NeTEx visualization."""
    xsd_files = find_xsd_files(directory)
    if not xsd_files:
        logging.error("No XSD files found in the specified directory.")
        return

    graph = nx.DiGraph()
    substitution_groups = {}

    logging.info(f"Found {len(xsd_files)} XSD files. Parsing...")
    for xsd_file in xsd_files:
        parse_xsd_file(xsd_file, graph, substitution_groups)

    logging.info("Resolving substitution groups...")
    resolve_substitution_groups(graph, substitution_groups)

    # Remove isolated nodes to clean up the graph
    isolated_nodes = [node for node, degree in graph.degree() if degree == 0]
    graph.remove_nodes_from(isolated_nodes)
    logging.info(f"Removed {len(isolated_nodes)} isolated nodes.")

    logging.info("Generating visualization...")
    net = Network(height="1000px", width="100%", notebook=True, directed=True)
    net.from_nx(graph)
    net.show_buttons(filter_=['physics'])
    net.save_graph(output_file)
    logging.info(f"Visualization saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a graphical representation of the NeTEx standard.")
    parser.add_argument("directory", help="Path to the directory containing NeTEx XSD files.")
    parser.add_argument("--output", default="solution/netex_visualization.html", help="Output HTML file path.")
    args = parser.parse_args()

    main(args.directory, args.output)
