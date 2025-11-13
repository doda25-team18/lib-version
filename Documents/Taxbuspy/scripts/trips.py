INPUT_CSV   = '/Users/yasarkocdas/Documents/Taxbuspy/data/demand/Helmond_source/matched/Helmond_50km/trips_taxbus_april_2.csv'
OUTPUT_CSV  = '/Users/yasarkocdas/Documents/Taxbuspy/data/demand/Helmond_source/matched/Helmond_50km'  
COUNT       = 70
RQ_TIME_MIN = 7948800
RQ_TIME_MAX = 8035200                  
START_MIN   = 0                   
START_MAX   = 199503                  
END_MIN     = 0                   
END_MAX     = 199503                   

autoimport = True
import os
import random
import pandas as pd

def lees_csv(pad):
    print(f"Lezen van CSV: {pad}")

    df = pd.read_csv(
        pad,
        dtype={'request_id': 'Int64', 'rq_time': 'Int64',
               'start': 'Int64', 'end': 'Int64', 'number_passenger': 'Int64'}
    )

    df['request_id'] = df['request_id'].astype(int)
    df['rq_time'] = df['rq_time'].astype(int)
    print(f"  {len(df)} bestaande trips gevonden (dtypes: request_id={df['request_id'].dtype}, rq_time={df['rq_time'].dtype})")
    return df


def genereer_trips(df, aantal):
    print(f"Genereren van {aantal} nieuwe trips...")
    start_id = int(df['request_id'].max()) + 1
    records = []
    for i in range(aantal):
        records.append({
            'request_id': start_id + i,
            'rq_time': random.randint(RQ_TIME_MIN, RQ_TIME_MAX),
            'start': random.randint(START_MIN, START_MAX),
            'end': random.randint(END_MIN, END_MAX),
            'number_passenger': random.choice([1, 2])
        })
    print("  Gereed")
    return pd.DataFrame(records)

def prepare_output(df1, df2):
    print("Samenvoegen en sorteren op rq_time")
    df = pd.concat([df1, df2], ignore_index=True)
    df.sort_values('rq_time', inplace=True)
    df.reset_index(drop=True, inplace=True)


    pad = OUTPUT_CSV

    if os.path.isdir(pad) or not pad.lower().endswith('.csv'):
        mapnaam = pad if os.path.isdir(pad) else os.path.dirname(pad)
        if not mapnaam:
            mapnaam = os.getcwd()
        # base naam van input + '_augmented.csv'
        base = os.path.splitext(os.path.basename(INPUT_CSV))[0]
        pad = os.path.join(mapnaam, f"{base}_augmented.csv")
        print(f"OUTPUT_CSV is een map of mist .csv-extensie, gebruik: {pad}")
    return df, pad

def schrijf_csv(df, pad):
    print(f"Opslaan naar: {pad}")
    folder = os.path.dirname(pad)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)
    df.to_csv(pad, index=False)
    print(f"  Totaal {len(df)} trips opgeslagen")

if __name__ == '__main__':
    df_orig = lees_csv(INPUT_CSV)
    df_nieuw = genereer_trips(df_orig, COUNT)
    df_all, final_path = prepare_output(df_orig, df_nieuw)
    schrijf_csv(df_all, final_path)
