"""
Debug helper extracted from perpignan_prod.ipynb on 2026-06-12 (convention: no def in
notebooks). Checks that smoothed nodes keep their index and that edges map to existing
nodes. Ad-hoc validation, not part of the canonical pipeline.
"""

def validate_graph_topology(original_nodes, smoothed_nodes, edges):
    """
    Validates that the smoothed nodes perfectly align with the edge list
    and haven't lost their original index mapping.
    """
    print("--- Graph Topology Diagnostic ---")
    
    # 1. Check for dropped nodes
    missing_nodes = set(original_nodes.index) - set(smoothed_nodes.index)
    if missing_nodes:
        print(f"⚠️ WARNING: {len(missing_nodes)} nodes were dropped during smoothing.")
        print(f"Dropped Node IDs: {list(missing_nodes)[:5]}...") # Print first 5 for debugging
    else:
        print("✅ SUCCESS: All original nodes are present in the smoothed dataset.")

    # 2. Check for orphaned edges (Edges pointing to nodes that no longer exist)
    # Ensure edges DataFrame has 'node_1' and 'node_2' columns
    missing_in_node_1 = edges[~edges['node_1'].isin(smoothed_nodes.index)]
    missing_in_node_2 = edges[~edges['node_2'].isin(smoothed_nodes.index)]
    
    orphaned_edges = len(missing_in_node_1) + len(missing_in_node_2)
    
    if orphaned_edges > 0:
        print(f"🚨 CRITICAL: {orphaned_edges} edge endpoints reference missing nodes!")
        print("Running compute_lcp_network will fail or map incorrectly.")
    else:
        print("✅ SUCCESS: All edge endpoints map correctly to existing nodes.")
        
    # 3. Verify Geometry Integrity
    empty_geoms = smoothed_nodes.geometry.is_empty.sum()
    null_geoms = smoothed_nodes.geometry.isna().sum()
    
    if empty_geoms > 0 or null_geoms > 0:
        print(f"⚠️ WARNING: Found {empty_geoms} empty and {null_geoms} null geometries.")
    else:
        print("✅ SUCCESS: No empty or null geometries detected in smoothed nodes.")

    print("---------------------------------")

# Usage:
smoothed_nodes = rout.safe_smooth(df_nodes)  # was fast_safe_smooth (geoai); now index-stable
validate_graph_topology(df_nodes, smoothed_nodes, gdf_edges)