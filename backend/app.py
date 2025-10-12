from flask import Flask, jsonify, request
from sqlalchemy import create_engine, text
from flask_cors import CORS
import traceback

app = Flask(__name__)
CORS(app)

engine = create_engine(
    "mysql+mysqlconnector://trish:Trish%401234@35.240.197.184:3306/stadvdb"
)

with engine.connect() as conn:
    result = conn.execute(text("SELECT NOW()"))
    print("✅ Connection successful, current time:", result.fetchone()[0])

def execute_query(query, params=None):
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query), params or {})
            return [dict(row._mapping) for row in result]
    except Exception as e:
        print(f"❌ Query error: {str(e)}")
        traceback.print_exc()
        raise

@app.route('/')
def hello():
    return "OLAP Backend API - Running!"

# ========== ORDERS WITH FILTERS ==========
@app.route('/api/orders/total-over-time', methods=['GET'])
def total_orders_over_time():
    """Total Orders Over Time with Country/City Filters"""
    date_category = request.args.get('category', 'month')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Get filter parameters (multiple values possible)
    countries = request.args.getlist('country')  # Get list of countries
    cities = request.args.getlist('city')        # Get list of cities
    
    print(f"📥 Received: category={date_category}, dates={start_date} to {end_date}")
    print(f"📥 Filters: countries={countries}, cities={cities}")
    
    date_formats = {
        'day': "DATE(o.createdAt)",
        'week': "DATE_FORMAT(o.createdAt, '%Y-%u')",
        'month': "DATE_FORMAT(o.createdAt, '%Y-%m')",
        'quarter': "CONCAT(YEAR(o.createdAt), '-Q', QUARTER(o.createdAt))",
        'year': "YEAR(o.createdAt)"
    }
    
    date_format = date_formats.get(date_category, date_formats['month'])
    
    # Build query with JOIN to filter by country/city
    query = f"""
        SELECT 
            {date_format} as period,
            COUNT(DISTINCT o.orderID) as total_orders,
            COUNT(DISTINCT o.userID) as unique_customers,
            SUM(o.quantity) as total_items
        FROM FactOrders o
        JOIN DimUsers u ON o.userID = u.userID
    """
    
    conditions = []
    params = {}
    
    if start_date:
        conditions.append("o.createdAt >= :start_date")
        params['start_date'] = start_date
    if end_date:
        conditions.append("o.createdAt <= :end_date")
        params['end_date'] = end_date
    
    # Add country filter
    if countries:
        country_placeholders = ','.join([f':country{i}' for i in range(len(countries))])
        conditions.append(f"u.country IN ({country_placeholders})")
        for i, country in enumerate(countries):
            params[f'country{i}'] = country
    
    # Add city filter
    if cities:
        city_placeholders = ','.join([f':city{i}' for i in range(len(cities))])
        conditions.append(f"u.city IN ({city_placeholders})")
        for i, city in enumerate(cities):
            params[f'city{i}'] = city
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += f" GROUP BY {date_format} ORDER BY period"
    
    print(f"📤 SQL:\n{query}")
    print(f"📤 Params: {params}")
    
    try:
        results = execute_query(query, params)
        print(f"✅ Returning {len(results)} rows")
        return jsonify({"success": True, "data": results})
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/orders/by-location', methods=['GET'])
def orders_by_location():
    """Orders by Location with Filters"""
    location_type = request.args.get('type', 'city')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    countries = request.args.getlist('country')
    cities = request.args.getlist('city')
    
    print(f"📥 Location query: type={location_type}")
    print(f"📥 Filters: countries={countries}, cities={cities}")
    
    location_field = 'city' if location_type == 'city' else 'country'
    
    conditions = []
    params = {}
    
    if start_date:
        conditions.append("o.createdAt >= :start_date")
        params['start_date'] = start_date
    if end_date:
        conditions.append("o.createdAt <= :end_date")
        params['end_date'] = end_date
    
    # Add country filter
    if countries:
        country_placeholders = ','.join([f':country{i}' for i in range(len(countries))])
        conditions.append(f"u.country IN ({country_placeholders})")
        for i, country in enumerate(countries):
            params[f'country{i}'] = country
    
    # Add city filter
    if cities:
        city_placeholders = ','.join([f':city{i}' for i in range(len(cities))])
        conditions.append(f"u.city IN ({city_placeholders})")
        for i, city in enumerate(cities):
            params[f'city{i}'] = city
    
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    
    query = f"""
        SELECT 
            u.{location_field} as location,
            COUNT(DISTINCT o.orderID) as total_orders,
            COUNT(DISTINCT o.userID) as unique_customers,
            SUM(o.quantity) as total_items
        FROM FactOrders o 
        JOIN DimUsers u ON o.userID = u.userID
        {where_clause}
        GROUP BY u.{location_field}
        ORDER BY total_orders DESC
    """
    
    print(f"📤 SQL:\n{query}")

    try:
        results = execute_query(query, params)
        print(f"✅ Found {len(results)} locations")
        return jsonify({"success": True, "data": results})
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/orders/by-product-category', methods=['GET'])
def orders_by_product_category():
    """Orders by Product Category with Filters"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    countries = request.args.getlist('country')
    cities = request.args.getlist('city')
    
    print(f"📥 Category query")
    print(f"📥 Filters: countries={countries}, cities={cities}")
    
    query = """
        SELECT 
            p.category,
            COUNT(DISTINCT o.orderID) as total_orders,
            SUM(o.quantity) as total_quantity,
            COUNT(DISTINCT o.userID) as unique_customers
        FROM FactOrders o
        JOIN DimProducts p ON o.productID = p.productID
        JOIN DimUsers u ON o.userID = u.userID
    """
    
    conditions = []
    params = {}
    
    if start_date:
        conditions.append("o.createdAt >= :start_date")
        params['start_date'] = start_date
    if end_date:
        conditions.append("o.createdAt <= :end_date")
        params['end_date'] = end_date
    
    # Add country filter
    if countries:
        country_placeholders = ','.join([f':country{i}' for i in range(len(countries))])
        conditions.append(f"u.country IN ({country_placeholders})")
        for i, country in enumerate(countries):
            params[f'country{i}'] = country
    
    # Add city filter
    if cities:
        city_placeholders = ','.join([f':city{i}' for i in range(len(cities))])
        conditions.append(f"u.city IN ({city_placeholders})")
        for i, city in enumerate(cities):
            params[f'city{i}'] = city
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " GROUP BY p.category ORDER BY total_orders DESC"
    
    print(f"📤 SQL:\n{query}")
    
    try:
        results = execute_query(query, params)
        print(f"✅ Found {len(results)} categories")
        return jsonify({"success": True, "data": results})
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# ========== SALES REPORTS ==========


# ========== CUSTOMER REPORTS ==========


# ========== PRODUCT REPORTS ==========


# ========== RIDER REPORTS ==========


# test

# ========== FOR DROPDOWN STUFF IN SIDEBAR ==========


# ========== DROPDOWN FILTERS ==========
@app.route('/api/filters/countries', methods=['GET'])
def get_countries():
    """Get unique countries"""
    query = """
        SELECT DISTINCT country 
        FROM DimUsers
        WHERE country IS NOT NULL
        ORDER BY country
    """
    try:
        results = execute_query(query)
        countries = [
            {"id": row["country"].lower().replace(" ", "_"), "name": row["country"]}
            for row in results if row["country"]
        ]
        print(f"✅ Found {len(countries)} countries")
        return jsonify({"success": True, "data": countries})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/filters/cities', methods=['GET'])
def get_cities():
    """Get cities, optionally filtered by country"""
    country = request.args.get('country')

    query = """
        SELECT DISTINCT city, country 
        FROM DimUsers
        WHERE city IS NOT NULL
    """
    params = {}

    if country:
        query += " AND country = :country"
        params['country'] = country

    query += " ORDER BY city"

    try:
        results = execute_query(query, params)
        cities = [
            {
                "id": f"{row['city'].lower().replace(' ', '_')}_{row['country'].lower().replace(' ', '_')}", 
                "city": row["city"],
                "country": row["country"]
            }
            for row in results if row["city"]
        ]
        print(f"✅ Found {len(cities)} cities")
        return jsonify({"success": True, "data": cities})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Flask Backend...")
    print("📍 Running on http://localhost:5000")
    app.run(debug=True, port=5000, host='0.0.0.0')