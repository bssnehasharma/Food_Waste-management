import pandas as pd

INPUT_FILE = 'flights.csv'
OUTPUT_FILE = 'Cleaned_flights.csv'
CHUNK_SIZE = 100000 # process 1 lakh rows at a time

clean_chunks = []

# Read file in chunks so RAM doesn't explode
for chunk in pd.read_csv(INPUT_FILE, chunksize=CHUNK_SIZE, low_memory=False):

    # 1. Standardize column names: make everything UPPERCASE + remove spaces
    chunk.columns = chunk.columns.str.upper().str.strip().str.replace(' ', '_')

    # 2. Map common column name variations to standard names
    col_map = {
        'AIRLINE': 'AIRLINE_CODE',
        'CARRIER': 'AIRLINE_CODE',
        'ORIGIN': 'ORIGIN_AIRPORT',
        'DEST': 'DESTINATION_AIRPORT',
        'DEST_AIRPORT': 'DESTINATION_AIRPORT',
        'DATE': 'FLIGHT_DATE'
    }
    chunk = chunk.rename(columns=col_map)

    # 3. Drop rows where key columns are missing
    key_cols = ['FLIGHT_ID', 'AIRLINE_CODE', 'ORIGIN_AIRPORT', 'DESTINATION_AIRPORT', 'FLIGHT_DATE']
    # Keep only cols that actually exist in file
    key_cols = [c for c in key_cols if c in chunk.columns]
    chunk = chunk.dropna(subset=key_cols)

    # 4. Standardize values
    if 'AIRLINE_CODE' in chunk.columns:
        chunk['AIRLINE_CODE'] = chunk['AIRLINE_CODE'].astype(str).str.upper().str.strip()

    if 'ORIGIN_AIRPORT' in chunk.columns:
        chunk['ORIGIN_AIRPORT'] = chunk['ORIGIN_AIRPORT'].astype(str).str.upper().str.strip()

    if 'DESTINATION_AIRPORT' in chunk.columns:
        chunk['DESTINATION_AIRPORT'] = chunk['DESTINATION_AIRPORT'].astype(str).str.upper().str.strip()

    # 5. Standardize dates
    if 'FLIGHT_DATE' in chunk.columns:
        chunk['FLIGHT_DATE'] = pd.to_datetime(chunk['FLIGHT_DATE'], errors='coerce')
        chunk = chunk.dropna(subset=['FLIGHT_DATE']) # drop rows where date failed

    # 6. Fill numeric nulls with 0 so charts don't break
    num_cols = ['DELAY_MINUTES', 'DISTANCE', 'CANCELLED']
    for col in num_cols:
        if col in chunk.columns:
            chunk[col] = pd.to_numeric(chunk[col], errors='coerce').fillna(0)

    # 7. Remove duplicate flights
    if 'FLIGHT_ID' in chunk.columns:
        chunk = chunk.drop_duplicates(subset=['FLIGHT_ID'])

    clean_chunks.append(chunk)

# Join all chunks and save
final_df = pd.concat(clean_chunks, ignore_index=True)
final_df.to_csv(OUTPUT_FILE, index=False)

print(f"✅ Done! Cleaned file saved as {OUTPUT_FILE}")
print(f"Final rows: {len(final_df):,}")
print(f"Columns: {list(final_df.columns)}")

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Flight Delays EDA", layout="wide")
st.title("✈️ Flight Delays Exploratory Data Analysis")

# 1. Load data
@st.cache_data
def load_data():
    df = pd.read_csv('Cleaned_flights.csv')
    return df

df = load_data()

# 2. Avg Delay by Airline Code - matches your Power BI chart
st.subheader("1. Average Delay by Airline Code")
airline_delay = df.groupby('AIRLINE_CODE')['DEPARTURE_DELAY'].mean().sort_values(ascending=False)

col1, col2 = st.columns(2)
with col1:
    st.bar_chart(airline_delay)
with col2:
    st.dataframe(airline_delay.round(2))
st.caption("VX = Virgin America, AA = American, etc. Higher = worse delays")

# 3. Delay by Day of Week
st.subheader("2. Average Delay by Day of Week")
day_delay = df.groupby('DAY_OF_WEEK')['DEPARTURE_DELAY'].mean().sort_values()
st.line_chart(day_delay)
st.dataframe(day_delay.round(2))
st.caption("1=Monday, 7=Sunday")

# 4. Delay by Departure Hour
if 'CRS_DEP_TIME' in df.columns:
    st.subheader("3. Average Delay by Departure Hour")
    df['DEP_HOUR'] = (df['CRS_DEP_TIME'] // 100).astype(int)
    hour_delay = df.groupby('DEP_HOUR')['DEPARTURE_DELAY'].mean()
    st.area_chart(hour_delay)
    st.dataframe(hour_delay.round(2))

# 5. Top delayed routes
st.subheader("4. Top 10 Most Delayed Routes")
if 'ORIGIN_AIRPORT' in df.columns and 'DESTINATION_AIRPORT' in df.columns:
    df['ROUTE'] = df['ORIGIN_AIRPORT'].astype(str) + ' → ' + df['DESTINATION_AIRPORT'].astype(str)
    route_delay = df.groupby('ROUTE')['DEPARTURE_DELAY'].mean().sort_values(ascending=False).head(10)
    st.bar_chart(route_delay)
    st.dataframe(route_delay.round(2))

# 6. Raw data preview
st.subheader("5. Raw Data Sample")
st.dataframe(df.head(100))
print("\n=== 7. OUTLIERS CHECK ===")
q99 = df['DEPARTURE_DELAY'].quantile(0.99)
print(f"99th percentile delay: {q99:.0f} minutes")
print(f"Flights with delay > 3 hours: {(df['DEPARTURE_DELAY'] > 180).sum()}")

print("\n=== 8. CORRELATION ===")
cols = ['DEPARTURE_DELAY', 'DISTANCE', 'AIR_SYSTEM_DELAY', 'AIRLINE_DELAY']
print(df[cols].corr()['DEPARTURE_DELAY'].sort_values(ascending=False))




