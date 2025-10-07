import mysql.connector
import pandas as pd
from sqlalchemy import create_engine, text


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

print("🧩 FactOrders Preview:")
print(orders_merged.head())
print("Rows:", len(orders_merged))


orders_merged.to_sql('FactOrders', engine, if_exists='replace', index=False, chunksize=5000, method='multi')
users.to_sql('DimUsers', engine, if_exists='replace', index=False, chunksize=5000, method='multi')
products.to_sql('DimProducts', engine, if_exists='replace', index=False, chunksize=5000, method='multi')
riders_merged.to_sql('DimRiders', engine, if_exists='replace', index=False, chunksize=5000, method='multi')

print("✅ Data loaded successfully to Cloud Data Warehouse!")
engine.dispose()

