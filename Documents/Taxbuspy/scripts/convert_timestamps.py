#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

def process_file(path_in, path_out):
    # 1. Inlezen
    df = pd.read_csv(path_in, sep=';')
    
    # 2. Parse & vervang rq_time: seconden sinds 2024-01-01 00:00
    ref = pd.Timestamp('2024-01-01 00:00:00')
    df['rq_time'] = (
        (pd.to_datetime(
            df['rq_time'],
            format='%d-%m-%Y %H:%M',
            dayfirst=True,
            errors='coerce'
        ) - ref)
        .dt.total_seconds()
        .fillna(-1)    # optioneel: mislukte parses worden -1
        .astype(int)
    )

    df.to_csv(path_out, index=False, sep=';')
    print(f"✔️ Verwerkt: {path_in.name} → {path_out.name}")

def main():
    home = Path.home()
    raw_dir = home / "Documents" / "Taxbuspy" / "data" / "demand" / "Helmond_source" / "raw"
    proc_dir = home / "Documents" / "Taxbuspy" / "data" / "demand" / "Helmond_source" / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)

    for csv_in in raw_dir.glob("*raw.csv"):
        csv_out = proc_dir / csv_in.name.replace("raw.csv", "seconds.csv")
        process_file(csv_in, csv_out)

if __name__ == "__main__":
    main()
