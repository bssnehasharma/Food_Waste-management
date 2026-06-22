import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Food Wastage Management", layout="wide")

@st.cache_resource
def init_db(uploaded_files):
    conn = sqlite3.connect('food_waste.db', check_same_thread=False)

    if uploaded_files:
        tables = ['providers', 'receivers', 'food_listings', 'claims']
        for table, file in zip(tables, uploaded_files):
            if file is not None:
                try:
                    df = pd.read_csv(file)
                    df.to_sql(table, conn, if_exists='replace', index=False)
                    st.sidebar.success(f"✅ {table} loaded: {len(df)} rows")
                except Exception as e:
                    st.sidebar.error(f"Error loading {table}: {e}")
    return conn

st.title("🍎 Food Wastage Management System")

# Sidebar: Upload files first
st.sidebar.header("📁 Upload CSV Files")
uploaded_files = [
    st.sidebar.file_uploader("Providers CSV", type="csv", key="p"),
    st.sidebar.file_uploader("Receivers CSV", type="csv", key="r"),
    st.sidebar.file_uploader("Food Listings CSV", type="csv", key="f"),
    st.sidebar.file_uploader("Claims CSV", type="csv", key="c")
]

conn = init_db(uploaded_files)

def run_query(query):
    try:
        return pd.read_sql_query(query, conn)
    except Exception as e:
        st.warning(f"Query error: {e}")
        return pd.DataFrame()

def run_action(query, params=None):
    cursor = conn.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    conn.commit()
    cursor.close()

def get_col(df, keywords):
    """Find column name matching keywords like 'city', 'location'"""
    for col in df.columns:
        if any(k.lower() in col.lower() for k in keywords):
            return col
    return None

menu = st.sidebar.radio("Go to", ["Dashboard", "View Data", "Add Listing", "Claims"])

if menu == "Dashboard":
    if not all(uploaded_files):
        st.info("👆 Upload all 4 CSV files in sidebar to see dashboard")
        st.stop()

    # Get column names dynamically
    try:
        prov_df = pd.read_sql_query("SELECT * FROM providers LIMIT 1", conn)
        recv_df = pd.read_sql_query("SELECT * FROM receivers LIMIT 1", conn)
        list_df = pd.read_sql_query("SELECT * FROM food_listings LIMIT 1", conn)
        claim_df = pd.read_sql_query("SELECT * FROM claims LIMIT 1", conn)

        recv_city_col = get_col(recv_df, ['city', 'location'])
        list_city_col = get_col(list_df, ['city', 'location'])
        food_type_col = get_col(list_df, ['food_type', 'type'])
        meal_type_col = get_col(list_df, ['meal_type', 'meal'])
        status_col = get_col(claim_df, ['status'])
    except:
        st.error("Tables not loaded properly. Re-upload CSVs")
        st.stop()

    st.subheader("Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Providers", run_query("SELECT COUNT(*) as count FROM providers")['count'][0])
    col2.metric("Total Receivers", run_query("SELECT COUNT(*) as count FROM receivers")['count'][0])
    col3.metric("Food Listings", run_query("SELECT COUNT(*) as count FROM food_listings")['count'][0])
    col4.metric("Total Claims", run_query("SELECT COUNT(*) as count FROM claims")['count'][0])

    st.markdown("---")

    # Chart 1: Food Listings by City
    if list_city_col:
        st.subheader("Food Listings by City")
        df_city = run_query(f"SELECT {list_city_col} as City, COUNT(*) as Count FROM food_listings GROUP BY {list_city_col} ORDER BY Count DESC LIMIT 10")
        st.plotly_chart(px.bar(df_city, x='City', y='Count', title='Top 10 Cities'), use_container_width=True)

    # ===== STRETCH 1: Receivers by Each City =====
    if recv_city_col:
        st.subheader("Receivers by City")
        df_recv_city = run_query(f"""
            SELECT {recv_city_col} as City, COUNT(*) as Count
            FROM receivers
            GROUP BY {recv_city_col}
            ORDER BY Count DESC
            LIMIT 10
        """)
        st.plotly_chart(px.bar(df_recv_city, x='City', y='Count', title='Top 10 Cities by Receivers', color='Count'), use_container_width=True)

    # ===== STRETCH 2: Food Listings Heatmap =====
    if list_city_col and food_type_col:
        st.subheader("Food Listings: City vs Food Type")
        df_heatmap = run_query(f"""
            SELECT {list_city_col} as City, {food_type_col} as Food_Type, COUNT(*) as Count
            FROM food_listings
            GROUP BY {list_city_col}, {food_type_col}
        """)
        if not df_heatmap.empty:
            fig = px.density_heatmap(df_heatmap, x='City', y='Food_Type', z='Count', color_continuous_scale='Blues')
            st.plotly_chart(fig, use_container_width=True)

    # Chart 2: Listings by Food Type
    if food_type_col:
        st.subheader("Listings by Food Type")
        df_food_type = run_query(f"SELECT {food_type_col} as Food_Type, COUNT(*) as Count FROM food_listings GROUP BY {food_type_col}")
        st.plotly_chart(px.bar(df_food_type, x='Food_Type', y='Count', color='Food_Type'), use_container_width=True)

    # Chart 3: Meal Type Distribution
    if meal_type_col:
        st.subheader("Meal Type Distribution")
        df_meal = run_query(f"SELECT {meal_type_col} as Meal_Type, COUNT(*) as Count FROM food_listings GROUP BY {meal_type_col}")
        st.plotly_chart(px.bar(df_meal, x='Meal_Type', y='Count', color='Meal_Type'), use_container_width=True)

    # Chart 4: Claims Status
    if status_col:
        st.subheader("Claims Status")
        df_status = run_query(f"SELECT {status_col} as Status, COUNT(*) as Count FROM claims GROUP BY {status_col}")
        st.plotly_chart(px.pie(df_status, names='Status', values='Count'), use_container_width=True)

    # Chart 5: Top Providers
    st.subheader("Top 10 Providers by Listings")
    df_top_providers = run_query("""
        SELECT p.Name, COUNT(f.Food_ID) as Listings
        FROM providers p
        JOIN food_listings f ON p.Provider_ID = f.Provider_ID
        GROUP BY p.Name ORDER BY Listings DESC LIMIT 10
    """)
    st.plotly_chart(px.bar(df_top_providers, x='Name', y='Listings'), use_container_width=True)

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
