import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Food Wastage Management", layout="wide")

@st.cache_resource
def init_db():
    conn = sqlite3.connect('food_waste.db', check_same_thread=False)
    # Auto-create tables from your CSV files
    tables = ['providers', 'receivers', 'food_listings', 'claims']
    for table in tables:
        try:
            df = pd.read_csv(f'{table}.csv')
            df.to_sql(table, conn, if_exists='replace', index=False)
        except Exception as e:
            st.error(f"Error loading {table}.csv: {e}")
    return conn

conn = init_db()

def run_query(query):
    return pd.read_sql_query(query, conn)

def run_action(query, params=None):
    cursor = conn.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    conn.commit()
    cursor.close()

st.title("🍎 Food Wastage Management System")

menu = st.sidebar.radio("Go to", ["Dashboard", "View Data", "Add Listing", "Claims"])


