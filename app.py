import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Food Wastage Management", layout="wide")

@st.cache_resource
def init_db():
    conn = sqlite3.connect('food_waste.db', check_same_thread=False)
    # Maps your _data.csv files to table names
    file_table_map = {
        'providers_data.csv': 'providers',
        'receivers_data.csv': 'receivers',
        'food_listings_data.csv': 'food_listings',
        'claims_data.csv': 'claims'
    }
    for file_name, table_name in file_table_map.items():
        try:
            df = pd.read_csv(file_name)
            df.to_sql(table_name, conn, if_exists='replace', index=False)
        except Exception as e:
            st.error(f"Error loading {file_name}: {e}")
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

st.title("🍎 Food Wastage Management System")

menu = st.sidebar.radio("Go to", ["Dashboard", "View Data", "Add Listing", "Claims"])

if menu == "Dashboard":
    st.subheader("Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Providers", run_query("SELECT COUNT(*) as count FROM providers")['count'][0])
    col2.metric("Total Receivers", run_query("SELECT COUNT(*) as count FROM receivers")['count'][0])
    col3.metric("Food Listings", run_query("SELECT COUNT(*) as count FROM food_listings")['count'][0])
    col4.metric("Total Claims", run_query("SELECT COUNT(*) as count FROM claims")['count'][0])

    st.markdown("---")
    st.subheader("Food Listings by City")
    df_city = run_query("SELECT Location as City, COUNT(*) as Count FROM food_listings GROUP BY Location ORDER BY Count DESC LIMIT 10")
    st.plotly_chart(px.bar(df_city, x='City', y='Count'), use_container_width=True)

    st.subheader("Claims Status Distribution")
    df_status = run_query("SELECT Status, COUNT(*) as Count FROM claims GROUP BY Status")
    st.plotly_chart(px.pie(df_status, names='Status', values='Count'), use_container_width=True)

elif menu == "View Data":
    table = st.selectbox("Select Table", ["providers", "receivers", "food_listings", "claims"])
    st.dataframe(run_query(f"SELECT * FROM {table} LIMIT 1000"))

elif menu == "Add Listing":
    st.subheader("Add New Food Listing")
    with st.form("add_form"):
        provider_id = st.number_input("Provider ID", min_value=1)
        food_name = st.text_input("Food Name")
        quantity = st.number_input("Quantity", min_value=1)
        expiry_date = st.date_input("Expiry Date")
        location = st.text_input("Location")
        food_type = st.selectbox("Food Type", ["Vegetarian", "Non-Vegetarian", "Vegan"])
        meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snacks"])
        if st.form_submit_button("Add Listing"):
            run_action(
                "INSERT INTO food_listings (Provider_ID, Food_Name, Quantity, Expiry_Date, Location, Food_Type, Meal_Type) VALUES (?,?,?,?,?,?,?)",
                (provider_id, food_name, quantity, str(expiry_date), location, food_type, meal_type)
            )
            st.success("Food listing added!")

elif menu == "Claims":
    st.subheader("Food Claims")
    available = run_query("SELECT Food_ID, Food_Name, Quantity, Location FROM food_listings WHERE Food_ID NOT IN (SELECT Food_ID FROM claims WHERE Status='Completed')")
    st.dataframe(available)
    with st.form("claim_form"):
        food_id = st.number_input("Food ID to Claim", min_value=1)
        receiver_id = st.number_input("Receiver ID", min_value=1)
        if st.form_submit_button("Claim Food"):
            run_action("INSERT INTO claims (Food_ID, Receiver_ID, Status, Timestamp) VALUES (?,?, 'Pending', datetime('now'))", (food_id, receiver_id))
            st.success("Claim submitted!")
