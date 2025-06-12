import tempfile
from pathlib import Path

import streamlit as st
from pyvis.network import Network

from utils.data_processor import load_json_data, validate_data
from utils.graph_builder import create_networkx_graph

st.set_page_config(layout="wide", page_title="Knowledge Graph MVP")
st.title("Knowledge Graph Viewer (MVP)")

def main():
    sample_data_path = Path("assets/sample_data.json")
    if not sample_data_path.exists():
        st.error(f"Sample data not found at {sample_data_path}")
        return

    edges_df, node_info_map = load_json_data(sample_data_path)

    if not validate_data(edges_df) or not node_info_map:
        st.error("Invalid data format. Ensure JSON has valid nodes and edges.")
        return

    nx_graph = create_networkx_graph(edges_df, node_info_map)

    net = Network(height="750px", width="100%", directed=True)
    net.from_nx(nx_graph)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp_file:
        net.save_graph(tmp_file.name)
        html_content = Path(tmp_file.name).read_text()
    st.components.v1.html(html_content, height=750, scrolling=True)

if __name__ == "__main__":
    main()
