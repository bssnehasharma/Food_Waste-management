import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Food Wastage Management", layout="wide")

@st.cache_resource
def get_connection():
    conn = sqlite3.connect('food_waste.db', check_same_thread=False)
    # Auto-load CSVs into SQLite tables on first run
    for table in ['providers', 'receivers', 'food_listings', 'claims']:
        try:
            df = pd.read_csv(f'{table}.csv')
            df.to_sql(table, conn, if_exists='replace', index=False)
        except:
            pass
    return conn

conn = get_connection()

def run_query(query):
    return pd.read_sql_query(query, conn)

def run_action(query, params=None):
    cursor = conn.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    conn.commit()

st.title("🍎 Food Wastage Management System")

# Sidebar
menu = st.sidebar.radio("Go to", ["Dashboard", "View Data", "Add Listing", "Claims"])

if menu == "Dashboard":
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Providers", run_query("SELECT COUNT(*) as count FROM providers")['count'][0])
    col2.metric("Total Receivers", run_query("SELECT COUNT(*) as count FROM receivers")['count'][0])
    col3.metric("Food Listings", run_query("SELECT COUNT(*) as count FROM food_listings")['count'][0])
    col4.metric("Total Claims", run_query("SELECT COUNT(*) as count FROM claims")['count'][0])
    
    st.subheader("Food Listings by City")
    df_city = run_query("SELECT Location as City, COUNT(*) as Count FROM food_listings GROUP BY Location")
    st.plotly_chart(px.bar(df_city, x='City', y='Count'), use_container_width=True)

elif menu == "View Data":
    table = st.selectbox("Select Table", ["providers", "receivers", "food_listings", "claims"])
    st.dataframe(run_query(f"SELECT * FROM {table}"))

# Add your Add Listing and Claims code here - just replace %s with? for SQLite
