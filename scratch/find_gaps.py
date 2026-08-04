import pandas as pd

df = pd.read_csv('data/telemetry_log_2026_06_to_08.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
actual_hours = pd.Series(df['timestamp'].unique()).sort_values()

diffs = actual_hours.diff()
big_gaps = actual_hours[diffs > pd.Timedelta(hours=12)]

print('Major Gaps > 12 hours:')
for t in big_gaps:
    prev = actual_hours[actual_hours < t].iloc[-1]
    print(f'Gap from {prev} to {t} (Duration: {t-prev})')

expected_days = pd.date_range(start='2026-06-28', end='2026-08-03', freq='D').date
actual_days = set(actual_hours.dt.date)
missing_days = sorted(set(expected_days) - actual_days)

print(f'\nTotal Full Days completely missed: {len(missing_days)}')
print(f'Dates: {missing_days}')
