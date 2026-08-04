import pandas as pd
import os

new_data_path = r'C:\Users\umert\Downloads\AquaVolt-AI Telemetry Log (3).xlsx'
old_data_path = r'C:\Users\umert\aquavolt-ai-pk\data\raw_telemetry.csv'

if os.path.exists(new_data_path):
    print(f'Loading new data: {new_data_path}')
    try:
        df_new = pd.read_excel(new_data_path)
        print(f'New data rows: {len(df_new)}')
        if 'Timestamp' in df_new.columns:
            df_new['Timestamp'] = pd.to_datetime(df_new['Timestamp'])
            print(f'New Date range: {df_new["Timestamp"].min()} to {df_new["Timestamp"].max()}')
    except Exception as e:
        print(f'Error reading excel: {e}')
        
if os.path.exists(old_data_path):
    print(f'\nLoading old data: {old_data_path}')
    df_old = pd.read_csv(old_data_path)
    if 'Timestamp' in df_old.columns:
        df_old['Timestamp'] = pd.to_datetime(df_old['Timestamp'])
        print(f'Old data rows: {len(df_old)}')
        print(f'Old Date range: {df_old["Timestamp"].min()} to {df_old["Timestamp"].max()}')
