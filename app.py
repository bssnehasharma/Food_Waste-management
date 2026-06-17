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

col1, col2 = st.columns(2)
    with col1:
        st.subheader("Claims by Status")
        status_df = run_query("SELECT Status, COUNT(*) as Count FROM claims GROUP BY Status")
        if not status_df.empty:
            fig2 = px.pie(status_df, names='Status', values='Count')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No claims data yet.")

    with col2:
        st.subheader("Top Cities by Listings")
        city_df = run_query("""
            SELECT p.City, COUNT(*) as Count
            FROM food_listings f
            JOIN providers p ON f.Provider_ID = p.Provider_ID
            GROUP BY p.City ORDER BY Count DESC LIMIT 10
        """)
        if not city_df.empty:
            fig3 = px.bar(city_df, x='City', y='Count')
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No city data yet.")

elif page == "View Data":
    table = st.selectbox("Select Table", ["providers", "receivers", "food_listings", "claims"])
    df = run_query(f"SELECT * FROM {table} LIMIT 1000")
    st.dataframe(df, use_container_width=True)
    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, f"{table}.csv", "text/csv")

elif page == "Add Listing":
    st.subheader("Add New Food Listing")
    providers = run_query("SELECT Provider_ID, Name FROM providers")
    if providers.empty:
        st.error("No providers found.")
    else:
        with st.form("listing_form"):
            provider = st.selectbox("Provider", providers['Name'])
            provider_id = providers[providers['Name'] == provider]['Provider_ID'].values[0]
            food_name = st.text_input("Food Name")
            quantity = st.number_input("Quantity", min_value=1)
            expiry_date = st.date_input("Expiry Date", min_value=date.today())
            food_type = st.selectbox("Food Type", ["Vegetarian", "Non-Vegetarian", "Vegan", "Fruits", "Dairy"])
            meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snacks"])
            submitted = st.form_submit_button("Add Listing")
            if submitted:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""INSERT INTO food_listings
                    (Food_Name, Quantity, Expiry_Date, Provider_ID, Food_Type, Meal_Type)
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                    (food_name, quantity, expiry_date, int(provider_id), food_type, meal_type))
                conn.commit()
                conn.close()
                st.success("Listing added!")
                st.cache_data.clear()

elif page == "Claims":
    st.subheader("Available Food Listings")
    city_filter = st.text_input("Filter by City")
    food_filter = st.text_input("Filter by Food Type")
    query = """
        SELECT f.Food_ID, f.Food_Name, f.Quantity, f.Expiry_Date, p.Name as Provider, p.City, p.Contact
        FROM food_listings f
        JOIN providers p ON f.Provider_ID = p.Provider_ID
        WHERE f.Food_ID NOT IN (SELECT Food_ID FROM claims WHERE Status = 'Completed')
    """
    if city_filter:
        query += f" AND p.City LIKE '%{city_filter}%'"
    if food_filter:
        query += f" AND f.Food_Type LIKE '%{food_filter}%'"
    available = run_query(query)
    if not available.empty:
        st.dataframe(available, use_container_width=True)
    else:
        st.info("No available food listings.")

    st.subheader("Claim Food")
    receivers = run_query("SELECT Receiver_ID, Name FROM receivers")
    if receivers.empty:
        st.error("No receivers found.")
    else:
        with st.form("claim_form"):
            food_id = st.number_input("Food ID to Claim", min_value=1)
            receiver = st.selectbox("Receiver", receivers['Name'])
            receiver_id = receivers[receivers['Name'] == receiver]['Receiver_ID'].values[0]
            submitted = st.form_submit_button("Submit Claim")
            if submitted:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO claims (Food_ID, Receiver_ID, Status) VALUES (%s, %s, 'Pending')",
                               (food_id, int(receiver_id)))
                conn.commit()
                conn.close()
                st.success("Claim submitted!")
                st.cache_data.clear()
