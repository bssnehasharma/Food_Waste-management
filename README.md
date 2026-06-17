# Food Wastage Management System

A Streamlit + MySQL web app to track food donations, manage providers/receivers, and reduce food waste.

### Features
- Dashboard with metrics and charts
- View all providers, receivers, food listings, claims
- Add new food listings 
- Claim available food items
- Filter by city and food type

### Setup
1. **Database**: Import the 4 CSV files into MySQL tables named `providers`, `receivers`, `food_listings`, `claims`
   ```sql
   CREATE DATABASE food_wastage_db;
   USE food_wastage_db;
   -- Run table creation SQL, then import CSVs using Table Data Import Wizard
