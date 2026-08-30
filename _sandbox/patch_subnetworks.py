"""One-off: recompute the sub-network fields in already-written outputs (no pipeline re-run).

For each guild it reads the nodes (displayed set + geometry), lcp (realized success corridors)
and edges (theoretical Gabriel edges, AOI-clipped) GeoJSON, recomputes the sub-network metrics
and rewrites stats_*.csv + the nodes' subnetwork_id in place.

Rule (matches utils/sp_pipeline.py): a sub-network is a connected component of the true graph
with >=3 patches INSIDE the AOI. Connectivity is read on the true graph (a patch linked through
a kept out-of-AOI ring patch stays in its sub-network); the count and size use only in-AOI
patches, so the metric matches the AOI-clipped dashboard (a ring-only component is not counted,
no id gap). The id is still written on the ring members of a counted component.

Realized fields are exact (lcp IS the realized graph). n_subnetworks_theory is reconstructed
from the AOI-clipped Gabriel edges (the full city+buffer graph is not on disk), so it can differ
by a hair from the in-pipeline value.

Usage: python3 _sandbox/patch_subnetworks.py [<city_outputs_dir>]
"""
import glob
import os
import sys

import geopandas as gpd
import networkx as nx
import pandas as pd

sys.path.insert(0, "/home/jovyan/work/team/marion/corridor_project/utils")  # run_pipeline.py in utils/
from run_pipeline import load_aoi  # noqa: E402  (AOI source per city, CITY_CONFIG-based)

os.umask(0)

CITY_DIR = sys.argv[1] if len(sys.argv) > 1 else \
    "/home/jovyan/work/team/marion/corridor_project/data/outputs/PNR_Ardennes"
CITY = os.path.basename(CITY_DIR.rstrip("/"))
AOI_RAW = load_aoi(CITY)


def subnetworks(graph: nx.Graph, in_aoi: set, displayed: set) -> tuple[dict, list]:
    """Components with >=3 in-AOI patches; size = in-AOI count, id written on displayed members."""
    min_patches = 3
    labels, sizes = {}, []
    for comp in nx.connected_components(graph):
        core = comp & in_aoi
        if len(core) >= min_patches:
            sizes.append(len(core))
            for nid in comp & displayed:
                labels[nid] = len(sizes)
    return labels, sizes


def graph_from(path: str, displayed: set) -> nx.Graph:
    """Build a graph from a node_1/node_2 GeoJSON, plus the displayed nodes as singletons."""
    g = nx.Graph()
    if path and os.path.exists(path):
        gdf = gpd.read_file(path)
        if {"node_1", "node_2"} <= set(gdf.columns):
            g.add_edges_from(zip(gdf["node_1"].astype(int), gdf["node_2"].astype(int)))
    g.add_nodes_from(displayed)
    return g


for gdir in sorted(glob.glob(os.path.join(CITY_DIR, "*/"))):
    guild = os.path.basename(gdir.rstrip("/"))
    nodes_p = glob.glob(os.path.join(gdir, "nodes_*.geojson"))
    lcp_p = glob.glob(os.path.join(gdir, "lcp_*.geojson"))
    edges_p = glob.glob(os.path.join(gdir, "edges_*.geojson"))
    stats_p = glob.glob(os.path.join(gdir, "stats_*.csv"))
    if not (nodes_p and stats_p):
        print(f"{guild}: SKIP (missing nodes/stats)")
        continue

    nodes = gpd.read_file(nodes_p[0])
    displayed = set(nodes["node_id"].astype(int))
    aoi = AOI_RAW.to_crs(nodes.crs).union_all()
    in_aoi = set(nodes.loc[nodes.geometry.intersects(aoi), "node_id"].astype(int))

    lab_real, sizes_real = subnetworks(graph_from(lcp_p[0] if lcp_p else None, displayed), in_aoi, displayed)
    _, sizes_theo = subnetworks(graph_from(edges_p[0] if edges_p else None, displayed), in_aoi, displayed)
    n_real = len(sizes_real)
    largest = max(sizes_real) if sizes_real else 0
    n_theo = len(sizes_theo)

    nodes["subnetwork_id"] = nodes["node_id"].astype(int).map(lab_real.get)
    nodes.to_file(nodes_p[0], driver="GeoJSON")

    st = pd.read_csv(stats_p[0])
    before = (int(st.loc[0, "n_subnetworks_theory"]), int(st.loc[0, "n_subnetworks"]),
              int(st.loc[0, "largest_subnetwork_size"]))
    st.loc[0, "n_subnetworks_theory"] = n_theo
    st.loc[0, "n_subnetworks"] = n_real
    st.loc[0, "subnetworks_split_by_barriers"] = n_real - n_theo
    st.loc[0, "largest_subnetwork_size"] = largest
    st.to_csv(stats_p[0], index=False)

    nb = int(st.loc[0, "nb_nodes"])
    print(f"{guild:18} nb_nodes={nb:5} in_aoi={len(in_aoi):5}  theory {before[0]}->{n_theo}  "
          f"realized {before[1]}->{n_real}  largest {before[2]}->{largest}  (largest<=in_aoi: {largest <= len(in_aoi)})")
