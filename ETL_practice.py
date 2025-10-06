import mysql.connector
import pandas as pd
from sqlalchemy import create_engine


# --- Extract ---
source_conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="password",
    database="stadvdb_source"
)

print("✅ Connected to source database")

query = "SELECT * FROM Orders;"
df = pd.read_sql(query, source_conn)
source_conn.close()

# --- Transform ---
df['deliveryDate'] = pd.to_datetime(df['deliveryDate'], errors='coerce')
df = df.dropna(subset=['deliveryDate'])
df['orderNumber'] = df['orderNumber'].str.upper()

print("🧹 Data transformed successfully!")
# --- Connect to cloud Data Warehouse ---
engine = create_engine(
    "mysql+mysqlconnector://<cloud_user>:<cloud_password>@<cloud_host>/<cloud_database>"
)

# Example (for illustration):
# engine = create_engine("mysql+mysqlconnector://group1_admin:stadv123@stadvdb-cloud.mysql.database.azure.com/stadvdb_warehouse")

df.to_sql('DimOrders', engine, if_exists='replace', index=False)

print("✅ Data loaded successfully to Cloud Data Warehouse!")