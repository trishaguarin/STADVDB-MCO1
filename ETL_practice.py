import mysql.connector
import pandas as pd
from sqlalchemy import create_engine, text, Table, Column, Integer, Date, DateTime, MetaData, ForeignKey
from sqlalchemy.types import VARCHAR, DECIMAL

# --- Extract ---
source_conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="iloveariel",
    database="stadvdb_source"
)

cursor = source_conn.cursor()

print("✅ Connected to source database")

orders = pd.read_sql("SELECT * FROM Orders", source_conn)
order_items = pd.read_sql("SELECT * FROM OrderItems", source_conn)
riders = pd.read_sql("SELECT * FROM Riders", source_conn)
products = pd.read_sql("SELECT * FROM Products", source_conn)
users = pd.read_sql("SELECT * FROM Users", source_conn)
couriers = pd.read_sql("SELECT * FROM Couriers", source_conn)

# Sample Query Test
query = """
SELECT * FROM Orders
LIMIT 10;
"""
df = pd.read_sql(query, source_conn)
print(df)


# --- Transform ---

# 1 - Rename stuff

orders.rename(columns={'OrderId': 'orderID', 'userId': 'userID', 'deliveryRiderId': 'riderID'}, inplace=True)
order_items.rename(columns={'OrderId': 'orderID', 'ProductId': 'productID'}, inplace=True)
products.rename(columns={'id': 'productID'}, inplace=True)
users.rename(columns={'id': 'userID'}, inplace=True)
riders.rename(columns={'id': 'riderID', 'courierId': 'courierID'}, inplace=True)
couriers.rename(columns={'id': 'courierID', 'name': 'courierName'}, inplace=True)


# orders: deliveryRiderId to riderID
# orders: userId to userID
# orderItems: productId to productID
# products: id to productID
# users: id to userID
# riders: id to riderID
# couriers: id to courierID
# couriers: name to courierName


# 2 - Drop Columns

orders.drop(columns=['orderNumber'], inplace=True, errors='ignore')
products.drop(columns=['description', 'productCode'], inplace=True, errors='ignore')
riders.drop(columns=['age', 'gender'], inplace=True, errors='ignore')
users.drop(columns=['username'], inplace=True, errors='ignore')

# Drop description (PRODUCT)
# Drop createdAt and updatedAt (RIDERS)
# Drop productCode (PRODUCTS)
# Drop username (USERS)

print("✅ Transformed data written back to database")


# 3 - Merge Tables for Fact Table

### Orders - OrderItems

orders_merged = pd.merge(
    orders, order_items[['orderID', 'productID', 'quantity']],
    on='orderID',
    how='inner' 
)

print("\n Orders Merged Successful.", orders_merged.shape)
print(orders_merged.head())

### Riders - Couriers

riders_merged = pd.merge(
    riders, couriers[['courierID', 'courierName']],
    on='courierID',
    how = 'inner'
)

riders_merged.drop(columns=['courierID'], inplace= True)

print("\n Riders Merged Successful.", riders_merged.shape)
print(riders_merged.head())

# 4 - Change formats and datatype

# gender -> user 
def normalize_gender(value):
    if pd.isna(value):
        return None
    value_str = str(value).strip().lower()
    
    if value_str.startswith("m"):
        return 'M'
    elif value_str.startswith("f"):
        return 'F'
    
users['gender'] = users['gender'].apply(normalize_gender)


# category -> products
def normalize_category(value):
    if pd.isna(value):
        return None
    value_str = str(value).strip().lower()
    if not value_str or value_str == "nan":
        return None
    elif value_str == "toy":
        return "Toys"
    elif value_str == "men's apparel":
        return "Clothing"
    elif value_str == "clothes":
        return "Clothing"
    elif value_str == "make up":
        return "Makeup"
    elif value_str == "laptops":
        return "Gadgets"
    elif value_str == "bag":
            return "Bags"
    return value_str.title()

products['category'] = products['category'].apply(normalize_category)

def parse_date(date_str):
    if pd.isna(date_str):
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%b %d, %Y", "%d-%m-%Y"):
        try:
            return pd.to_datetime(date_str, format=fmt).date()
        except (ValueError, TypeError):
            continue
    return None

users['dateOfBirth'] = users['dateOfBirth'].apply(parse_date)
users['createdAt'] = pd.to_datetime(users['createdAt']).dt.date
users['updatedAt'] = pd.to_datetime(users['updatedAt']).dt.date
orders_merged['deliveryDate'] = orders_merged['deliveryDate'].apply(parse_date)
products['createdAt'] = pd.to_datetime(products['createdAt']).dt.date
products['updatedAt'] = pd.to_datetime(products['updatedAt']).dt.date

cursor.close()
source_conn.close()
print("🧹 Data transformed successfully!")

# --- Connect to cloud Data Warehouse ---
engine = create_engine(
    "mysql+mysqlconnector://chrystel:Chrystel%401234@35.240.197.184:3306/stadvdb"
)

with engine.connect() as connection:
    print("✅ Connected to Cloud Data Warehouse successfully!")


metadata = MetaData()

# ========== DIMENSION TABLES ==========

# DimUsers table with Primary Key
dim_users = Table('DimUsers', metadata,
    Column('userID', Integer, primary_key=True, autoincrement=False),
    Column('firstName', VARCHAR(255)),
    Column('lastName', VARCHAR(255)),
    Column('address1', VARCHAR(255)),
    Column('address2', VARCHAR(255)),
    Column('city', VARCHAR(255)),
    Column('country', VARCHAR(255)),
    Column('zipCode', VARCHAR(10)),
    Column('phoneNumber', VARCHAR (255)),
    Column('gender', VARCHAR(1)),
    Column('dateOfBirth', Date, nullable=True),
    Column('createdAt', DateTime),
    Column('updatedAt', DateTime),
    mysql_engine='InnoDB',
    mysql_charset='utf8mb4'
)

# DimProducts table with Primary Key
dim_products = Table('DimProducts', metadata,
    Column('productID', Integer, primary_key=True, autoincrement=False),
    Column('name', VARCHAR(255)),
    Column('category', VARCHAR(255)),
    Column('price', DECIMAL(10, 2)),
    Column('createdAt', DateTime),
    Column('updatedAt', DateTime),
    mysql_engine='InnoDB',
    mysql_charset='utf8mb4'
)

# DimRiders table with Primary Key
dim_riders = Table('DimRiders', metadata,
    Column('riderID', Integer, primary_key=True, autoincrement=False),
    Column('firstName', VARCHAR(255)),
    Column('lastName', VARCHAR(255)),
    Column('courierName', VARCHAR(255)),
    Column('vehicleType', VARCHAR(255)),
    Column('age', Integer),
    Column('gender', VARCHAR(1)),
    mysql_engine='InnoDB',
    mysql_charset='utf8mb4'
)

# ========== FACT TABLE ==========

# FactOrders table with Primary Key and Foreign Keys
fact_orders = Table('FactOrders', metadata,
    Column('orderID', Integer, primary_key=True, autoincrement=False),
    Column('userID', Integer, ForeignKey('DimUsers.userID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
    Column('productID', Integer, ForeignKey('DimProducts.productID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
    Column('riderID', Integer, ForeignKey('DimRiders.riderID', ondelete='SET NULL', onupdate='CASCADE'), nullable=True),
    Column('quantity', Integer, nullable=False),
    Column('deliveryDate', DateTime),
    Column('createdAt', DateTime),
    Column('updatedAt', DateTime),
    mysql_engine='InnoDB',
    mysql_charset='utf8mb4'
)

print("🔨 Creating tables with schema definitions...")
metadata.drop_all(engine)  # Drop existing tables
metadata.create_all(engine)  # Create tables with proper schema
print("✅ Tables created with Primary Keys and Foreign Keys")
print("📦 Loading data to Cloud Data Warehouse...")


users.to_sql('DimUsers', engine, if_exists='append', index=False, chunksize=5000, method='multi')
print("✅ DimUsers loaded")

products.to_sql('DimProducts', engine, if_exists='append', index=False, chunksize=5000, method='multi')
print("✅ DimProducts loaded")

riders_merged.to_sql('DimRiders', engine, if_exists='append', index=False, chunksize=5000, method='multi')
print("✅ DimRiders loaded")

orders_merged.to_sql('FactOrders', engine, if_exists='append', index=False, chunksize=5000, method='multi')
print("✅ FactOrders loaded")


"""
orders_merged.to_sql('FactOrders', engine, if_exists='replace', index=False, chunksize=5000, method='multi')
users.to_sql('DimUsers', engine, if_exists='replace', index=False, chunksize=5000, method='multi')
products.to_sql('DimProducts', engine, if_exists='replace', index=False, chunksize=5000, method='multi')
riders_merged.to_sql('DimRiders', engine, if_exists='replace', index=False, chunksize=5000, method='multi')

"""
print("✅ Data loaded successfully to Cloud Data Warehouse!")

engine.dispose()

