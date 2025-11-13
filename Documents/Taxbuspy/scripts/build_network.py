import os
import osmnx as ox
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

def force_basistypes(gdf):
    for col in gdf.columns:
        if gdf[col].dtype == object:
            gdf[col] = gdf[col].apply(
                lambda x: ";".join(map(str, x)) if isinstance(x, list) else x
            )
        if not pd.api.types.is_string_dtype(gdf[col]):
            gdf[col] = gdf[col].astype(str)
    return gdf

def main():
    network_name = "Helmond_10km" #pas aan naar de naam van je network stad_radiuskm
    base_dir = os.path.join(os.getcwd(), "data", "networks", network_name, "base")
    raw_dir = os.path.join(os.getcwd(), "data", "networks", network_name, "raw")
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(raw_dir, exist_ok=True)

    # 1. Bepaal het centrum van stad
    print("Zoek centrum van Helmond...")
    helmond_gdf = ox.geocode_to_gdf("Helmond, Netherlands")
    centroid = helmond_gdf.geometry.centroid.iloc[0]
    
    # 2. Download netwerk
    print("Download netwerk")
    G = ox.graph_from_point(
        (centroid.y, centroid.x), 
        dist=10000,  # Verander dit getal indien je je radius wilt vergtoren of verkleien
        network_type='drive',
        truncate_by_edge=False,
        retain_all=True
    )

    if G.graph['crs'] != 'EPSG:4326':
        G = ox.project_graph(G, to_crs='EPSG:4326')

    nodes, edges = ox.graph_to_gdfs(G, nodes=True, edges=True)
    
    nodes = nodes.reset_index().rename(columns={'osmid': 'original_id'})
    nodes["node_index"] = nodes.index
    nodes["is_stop_only"] = False

    id_to_index = dict(zip(nodes["original_id"], nodes["node_index"]))
    edges = edges.reset_index()
    edges["from_node"] = edges["u"].map(id_to_index)
    edges["to_node"] = edges["v"].map(id_to_index)
    
    if edges[["from_node", "to_node"]].isna().any().any():
        raise ValueError("Edge bevat onbekende node IDs!")
    
    # 8. Hernoem en selecteer kolommen
    nodes = nodes.rename(columns={"x": "pos_x", "y": "pos_y"})
    edges = edges.rename(columns={"length": "distance"})
    edges["travel_time"] = edges["distance"] / 10.0
    edges["source_edge_id"] = edges["osmid"].apply(
        lambda x: ";".join(map(str, x)) if isinstance(x, list) else str(x)
    )
    
    # 9. Exporteer bestanden
    nodes[["node_index", "is_stop_only", "pos_x", "pos_y"]].to_csv(
        os.path.join(base_dir, "nodes.csv"), index=False)
    edges[["from_node", "to_node", "distance", "travel_time", "source_edge_id"]].to_csv(
        os.path.join(base_dir, "edges.csv"), index=False)
    
    force_basistypes(nodes).to_file(
        os.path.join(base_dir, "nodes_all_infos.geojson"), 
        driver="GeoJSON",
        encoding='utf-8'
    )
    force_basistypes(edges).to_file(
        os.path.join(base_dir, "edges_all_infos.geojson"), 
        driver="GeoJSON",
        encoding='utf-8'
    )
    
    with open(os.path.join(base_dir, "crs.info"), "w") as f:
        f.write("EPSG:4326")
    
    print(f"Netwerk opgebouwd met {len(nodes)} nodes en {len(edges)} edges!")

if __name__ == "__main__":
    main()