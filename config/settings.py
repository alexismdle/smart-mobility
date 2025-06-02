"""
Configuration settings for the Knowledge Graph Visualizer application.

This file defines default parameters for graph styling, physics,
and analytics.
"""

# --- Node Styling ---
DEFAULT_NODE_COLORS_BY_TYPE = {
    "person": "#FF69B4",          # Hot Pink
    "organization": "#1E90FF",    # Dodger Blue
    "company": "#1E90FF",         # Dodger Blue (alias for organization)
    "institution": "#1E90FF",     # Dodger Blue (alias for organization)
    "location": "#32CD32",        # Lime Green
    "place": "#32CD32",           # Lime Green (alias for location)
    "city": "#00FA9A",            # Medium Spring Green (specific location)
    "country": "#00CED1",         # Dark Turquoise (specific location)
    "event": "#FFD700",           # Gold
    "project": "#FFA500",         # Orange
    "publication": "#8A2BE2",     # Blue Violet
    "concept": "#DDA0DD",         # Plum
    "theory": "#DDA0DD",          # Plum (alias for concept)
    "field_of_study": "#BA55D3",  # Medium Orchid
    "technology": "#40E0D0",      # Turquoise
    "software": "#40E0D0",        # Turquoise (alias for technology)
    "product": "#6495ED",         # Cornflower Blue
    "disease": "#DC143C",         # Crimson
    "protein": "#20B2AA",         # Light Sea Green
    "gene": "#9370DB",            # Medium Purple
    "chemical_compound": "#F08080", # Light Coral
    "drug": "#F08080",            # Light Coral (alias for chemical_compound)
    "unknown": "#B0C4DE",         # Light Steel Blue (more distinct than grey)
    "default": "#B0C4DE"          # Same as unknown, for nodes with no type
}

DEFAULT_NODE_SIZE = 15 # Default size for nodes in PyVis graph
DEFAULT_NODE_SIZE_MULTIPLIER = 3 # Multiplier for dynamic node sizing based on metrics

# --- Edge Styling ---
DEFAULT_EDGE_COLOR = "#696969"  # Dim Grey, for better visibility than very light grey

# --- PyVis Physics Configuration ---
# These options control the simulation of the graph layout.
# For more details: https://pyvis.readthedocs.io/en/latest/documentation.html#pyvis.network.Network.set_options
# and vis.js physics module documentation: https://visjs.github.io/vis-network/docs/network/physics.html
PYVIS_PHYSICS_OPTIONS_DICT = {
    "enabled": True,
    "barnesHut": {
        "gravitationalConstant": -15000, # Increased repulsion for less overlap with many nodes
        "centralGravity": 0.1,          # Lower central gravity to allow more spread
        "springLength": 200,            # Default is 95, longer for more spread
        "springConstant": 0.05,         # Default is 0.04
        "damping": 0.09,                # Default
        "avoidOverlap": 0.1             # Between 0 and 1, how much to avoid overlap. Higher is more space.
    },
    "maxVelocity": 35,                  # Default is 50
    "minVelocity": 0.75,                # Default is 0.1, higher can help stabilize faster
    "solver": "barnesHut",              # Common choice. Others: "forceAtlas2Based", "repulsion"
    "stabilization": {
        "enabled": True,                # Run stabilization before displaying
        "iterations": 500,             # Default is 1000. Fewer for faster loading, more for complex graphs.
        "updateInterval": 50,
        "onlyDynamicEdges": False,
        "fit": True                     # Fit the graph to the view after stabilization
    },
    "timestep": 0.5,                    # Default
    "adaptiveTimestep": True            # Default
}

# It's often easier to pass the physics options as a JSON string to pyvis.set_options
# This format is directly what the underlying vis.js library expects.
PYVIS_PHYSICS_OPTIONS_JSON_STRING = """
{
  "physics": {
    "enabled": true,
    "barnesHut": {
      "gravitationalConstant": -15000,
      "centralGravity": 0.1,
      "springLength": 200,
      "springConstant": 0.05,
      "damping": 0.09,
      "avoidOverlap": 0.1
    },
    "maxVelocity": 35,
    "minVelocity": 0.75,
    "solver": "barnesHut",
    "stabilization": {
      "enabled": true,
      "iterations": 500,
      "updateInterval": 50,
      "onlyDynamicEdges": false,
      "fit": true
    },
    "timestep": 0.5,
    "adaptiveTimestep": true
  }
}
"""
# For the application, we will primarily use the dictionary `PYVIS_PHYSICS_OPTIONS_DICT`
# and let build_pyvis_graph handle it. The JSON string is for reference or alternative use.


# --- Graph Analytics ---
CENTRALITY_METRICS_TO_CALCULATE = [
    "degree",           # Degree centrality
    "betweenness",      # Betweenness centrality
    "closeness",        # Closeness centrality (Consider computational cost on large graphs)
    "eigenvector"       # Eigenvector centrality (Can be computationally intensive)
    # "pagerank"        # PageRank (Often useful)
]

# --- Other Settings ---
# Example: API keys, file paths for other resources, etc.
# MAX_NODES_FOR_FULL_RENDER = 1000 # Example: A threshold for performance considerations

# It's good practice to ensure all keys used in the main app are defined here
# even if some are advanced and not immediately used by default UI.
# This centralizes configuration.
APP_SETTINGS = {
    'node_colors_by_type': DEFAULT_NODE_COLORS_BY_TYPE,
    'default_node_color': DEFAULT_NODE_COLORS_BY_TYPE.get("unknown"), # Fallback
    'default_edge_color': DEFAULT_EDGE_COLOR,
    'default_node_size': DEFAULT_NODE_SIZE,
    'node_size_multiplier': DEFAULT_NODE_SIZE_MULTIPLIER,
    'physics_options': PYVIS_PHYSICS_OPTIONS_JSON_STRING, # PyVis set_options takes a string
    'centrality_metrics': CENTRALITY_METRICS_TO_CALCULATE
}