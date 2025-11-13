#Gebruikt om de juiste node te vinden voor start locatie van de busjes

import pandas as pd
import math

nodes_path = "/Users/yasarkocdas/Documents/Taxbuspy/data/networks/Helmond_50km/base/nodes.csv"
nodes = pd.read_csv(nodes_path)
ref_point = (5.7721816, 51.4602676)

def bereken_afstand(node_punt, referentie_punt):
    verschil_x = node_punt[0] - referentie_punt[0]
    verschil_y = node_punt[1] - referentie_punt[1]
    afstand = math.sqrt(verschil_x ** 2 + verschil_y ** 2)
    return afstand

# Voeg een kolom toe met de berekende afstand voor elke node
afstanden = []
for index, row in nodes.iterrows():
    node_punt = (row['pos_x'], row['pos_y'])
    afstand = bereken_afstand(node_punt, ref_point)
    afstanden.append(afstand)

nodes['afstand'] = afstanden

# Sorteer de nodes op afstand en pak de 3 dichtstbijzijnde
dichtstbijzijnde_nodes = nodes.sort_values('afstand').head(3)

# Print
for index, row in dichtstbijzijnde_nodes.iterrows():
    print(f"Node {row['node_index']} is ongeveer {row['afstand']:.6f} afstand verwijderd.")