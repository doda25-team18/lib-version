from pathlib import Path
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Bepaal de projectbasis vanaf de scriptlocatie
base_dir = Path(__file__).resolve().parent.parent

# Input- en outputpad bouwen
input_path = base_dir / "data" / "demand" / "Helmond_source" / "raw" / "RittenHelmond.csv"
output_path = base_dir / "data" / "demand" / "Helmond_source" / "matched" / "RittenHelmond_gps.csv"

# Laad de dataset
df = pd.read_csv(input_path, sep=";")

# Combineer postcode en stad tot één adresstring
df["address_origin"] = df["start"].str.strip()
df["address_destination"] = df["end"].str.strip()

# Haal unieke adressen op
unique_origin = df["address_origin"].unique()
unique_destination = df["address_destination"].unique()
unique_addresses = set(unique_origin).union(set(unique_destination))

# Initialiseer geocoder
geolocator = Nominatim(user_agent="Taxbuspy_geocoder")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

# Maak een dictionary voor caching
address_to_coords = {}

for address in unique_addresses:
    location = geocode(f"{address}, Nederland")
    if location:
        address_to_coords[address] = (location.longitude, location.latitude)
    else:
        address_to_coords[address] = (None, None)
    print(f"{address}: {address_to_coords[address]}")

# Voeg de coördinaten toe aan de dataframe
df["origin_lon"] = df["address_origin"].map(lambda addr: address_to_coords.get(addr)[0])
df["origin_lat"] = df["address_origin"].map(lambda addr: address_to_coords.get(addr)[1])
df["destination_lon"] = df["address_destination"].map(lambda addr: address_to_coords.get(addr)[0])
df["destination_lat"] = df["address_destination"].map(lambda addr: address_to_coords.get(addr)[1])

# Zorg dat de outputmap bestaat en sla op
output_path.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(output_path, index=False)

print(f" Verrijkte data succesvol opgeslagen in: {output_path}")
