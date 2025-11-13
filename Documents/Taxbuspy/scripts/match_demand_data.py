from geopy.distance import geodesic  # Zorg ervoor dat je deze import bovenaan je script plaatst
import pandas as pd
import rtree
from pathlib import Path

def clean_coordinate(value, decimalen):
    """Corrigeer coördinaten naar correct formaat"""
    try:
        # Verwijder onnodige tekens en split op komma
        cleaned = str(value).replace('.', '').replace(',', '.')
        # Als waarde te lang is, neem alleen relevante cijfers
        if len(cleaned) > 10:
            cleaned = cleaned[:10]
        # Voeg decimalen toe
        if len(cleaned) > decimalen:
            cleaned = cleaned[:decimalen] + '.' + cleaned[decimalen:]
        return float(cleaned)
    except:
        print(f"⚠️ Fout in coördinaat: {value}")
        return None

def match_demand_data():
    # Configuratie
    BASE_DIR = Path(__file__).parent.parent
    NETWORK_NAME = "Helmond_50km"
    DEMAND_SOURCE = "Helmond_source"
    PROJECT_NAME = "trips_taxbus_april_2"
    MAX_AFSTAND = 300  # maximale matchafstand in meters

    # Bestandspaden
    nodes_path = BASE_DIR / "data" / "networks" / NETWORK_NAME / "Base" / "nodes.csv"
    demand_path = BASE_DIR / "data" / "demand" / DEMAND_SOURCE / "raw" / "2aprilseconds.csv"
    output_path = BASE_DIR / "data" / "demand" / DEMAND_SOURCE / "matched" / NETWORK_NAME / f"trips_{PROJECT_NAME}.csv"

    try:
      
        output_path.parent.mkdir(parents=True, exist_ok=True)
   
        nodes = pd.read_csv(nodes_path)
        print(f" {len(nodes)} netwerk nodes geladen")
        print("\nVoorbeeld nodes:")
        print(nodes.head())
        
        demand = pd.read_csv(demand_path, sep=';')
        print("\nVoorbeeld demand data:")
        print(demand.head())
        
        coord_cols = {
            'start_lon': 1,
            'start_lat': 2,
            'end_lon': 1,
            'end_lat': 2
        }
        
        for col, decimalen in coord_cols.items():
            demand[col] = demand[col].apply(lambda x: clean_coordinate(x, decimalen))
        
        valid_demand = demand.dropna(subset=coord_cols.keys())
        print(f"\n {len(valid_demand)} geldige rijen gevonden")
        print("\nVoorbeeld coördinaten na correctie:")
        print(valid_demand[['start_lon', 'start_lat', 'end_lon', 'end_lat']].head(3))

        # R-tree index
        idx = rtree.index.Index()
        for _, row in nodes.iterrows():
            idx.insert(int(row["node_index"]), (row["pos_x"], row["pos_y"], row["pos_x"], row["pos_y"]))
        
        # Debug R-tree
        print("\n R-tree status:")
        print(f" Aantal indices: {len(nodes)}")
        
        # Matching functie met afstandsgrens
        def find_nearest_node(lon, lat):
            try:
                print(f" Start matching voor coördinaten: ({lon}, {lat})")
                
                x, y = lon, lat
                print(f" Gebruik coördinaten: ({x}, {y})")
                
                result = list(idx.nearest((x, y, x, y), 5))  # Zoek naar 5 dichtstbijzijnde nodes
                print(f" Dichtstbijzijnde nodes gevonden: {result}")
                
                min_distance = float('inf')
                nearest_node = None
                for node in result:
                    node_row = nodes[nodes["node_index"] == node].iloc[0]
                    node_lon, node_lat = node_row["pos_x"], node_row["pos_y"]
                    print(f" Coördinaten van node {node}: ({node_lon}, {node_lat})")
                    
                    distance = geodesic((y, x), (node_lat, node_lon)).meters
                    print(f" Afstand van node {node} naar de querypunten: {distance:.1f} meters")
                    
                    if distance < min_distance:
                        min_distance = distance
                        nearest_node = node
                
                # Controle op maximale afstand
                if min_distance > MAX_AFSTAND:
                    print(f"⚠️ Geen node binnen {MAX_AFSTAND} m gevonden voor ({lon}, {lat}) (min afstand = {min_distance:.1f} m)")
                    return -1
                
                print(f" Dichtstbijzijnde node gekozen: {nearest_node} op {min_distance:.1f} m")
                return nearest_node
            except Exception as e:
                print(f" Fout bij matching: {e}")
                return -1

        print("\n Start matching van punten")
        valid_demand['start'] = valid_demand.apply(
            lambda r: find_nearest_node(r['start_lon'], r['start_lat']), axis=1
        )
        valid_demand['end'] = valid_demand.apply(
            lambda r: find_nearest_node(r['end_lon'], r['end_lat']), axis=1
        )
        print(" Matching voltooid")
        
        # Sla op
        print("\n Sla resultaten op")
        valid_demand[['request_id', 'rq_time', 'start', 'end', 'Reizigers_totaal']]\
            .rename(columns={'Reizigers_totaal': 'number_passenger'})\
            .to_csv(output_path, index=False)
        print(f" Bestand opgeslagen in: {output_path}")

    except Exception as e:
        print(f"\n fout: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Start script")
    match_demand_data()
    print("Script voltooid")
