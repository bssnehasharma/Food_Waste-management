import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Food Wastage Management", layout="wide")

DB_FILE = "food_waste.db"

@st.cache_resource
def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    # Load CSVs into SQLite on first run
    for table in ['providers', 'receivers', 'food_listings', 'claims']:
        try:
            df = pd.read_csv(f"{table}.csv")
            df.to_sql(table, conn, if_exists='replace', index=False)
        except:
            pass
    return conn

conn = init_db()

def run_query(query):
    return pd.read_sql_query(query, conn)

st.title("🍎 Food Wastage Management System")

# Your existing dashboard code works the same
# Just replace mysql.connector with sqlite3 and you're done
