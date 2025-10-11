from flask import Flask, jsonify, request
from sqlalchemy import create_engine, text
from flask_cors import CORS
from datetime import datetime
import traceback

app = Flask(__name__)
CORS(app)

# Database connection
engine = create_engine(
    "mysql+mysqlconnector://trish:Trish%401234@35.240.197.184:3306/stadvdb"
)


with engine.connect() as conn:
    result = conn.execute(text("SELECT NOW()"))
    print("Connection successful, current time:", result.fetchone()[0])


def execute_query(query, params=None):
    """Helper function to execute queries and handle errors"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query), params or {})
            return [dict(row._mapping) for row in result]
    except Exception as e:
        print(f"Query error: {str(e)}")
        traceback.print_exc()
        raise

def build_where_clause(conditions):
    """Helper function to build WHERE clause from conditions list"""
    if not conditions:
        return ""
    return " WHERE " + " AND ".join(conditions)

@app.route('/')
def hello():
    return "OLAP Backend API etc etc"


# ========== ORDERS REPORTS ==========
@app.route('/api/orders/total-over-time', methods=['GET'])
def total_orders_over_time():
    """Total Orders Over Time - How many orders do we receive each [DATE CATEGORY]?"""
    date_category = request.args.get('category', 'day')  # day, week, month, quarter, year
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    date_formats = {
        'day': "DATE(createdAt)",
        'week': "DATE_FORMAT(createdAt, '%Y-%u')",
        'month': "DATE_FORMAT(createdAt, '%Y-%m')",
        'quarter': "CONCAT(YEAR(createdAt), '-Q', QUARTER(createdAt))",
        'year': "YEAR(createdAt)"
    }
    
    date_format = date_formats.get(date_category, date_formats['day']) # defaults to day
    
    query = f"""
        SELECT 
            {date_format} as period,
            COUNT(DISTINCT orderID) as total_orders,
            COUNT(DISTINCT userID) as unique_customers,
            SUM(quantity) as total_items
        FROM FactOrders
    """
    
    conditions = []
    params = {}
    
    if start_date:
        conditions.append("createdAt >= :start_date")
        params['start_date'] = start_date
    if end_date:
        conditions.append("createdAt <= :end_date")
        params['end_date'] = end_date
    
    query += build_where_clause(conditions)
    query += f" GROUP BY {date_format} ORDER BY period"
    
    try:
        results = execute_query(query, params)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ========================================
@app.route('/api/orders/by-location', methods=['GET'])
def orders_by_location():
    """Total Orders Per Location - How many orders do we receive in [LOCATION CATEGORY]?"""
    location_type = request.args.get('type', 'city')  # city, country
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    location_field = 'city' if location_type == 'city' else 'country' #defaults to city first
    
    conditions = []
    params = {}
    
    if start_date:
        conditions.append("o.createdAt >= :start_date")
        params['start_date'] = start_date
    if end_date:
        conditions.append("o.createdAt <= :end_date")
        params['end_date'] = end_date

    where_clause = build_where_clause(conditions) 
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

    try:
        results = execute_query(query, params)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
# ==============================================
@app.route('/api/orders/by-product-category', methods=['GET'])
def orders_by_product_category():
    """Total Orders Per Product Category - Which product categories generate the most orders?"""
    date_category = request.args.get('category', 'day') # day, week, month, quarter, year
    location_category = request.args.get('type', 'city')  # city, country
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    date_formats = {
        'day': "DATE(createdAt)",
        'week': "DATE_FORMAT(createdAt, '%Y-%u')",
        'month': "DATE_FORMAT(createdAt, '%Y-%m')",
        'quarter': "CONCAT(YEAR(createdAt), '-Q', QUARTER(createdAt))",
        'year': "YEAR(createdAt)"
    }

    date_format = date_formats.get(date_category, date_formats['day']) # defaults to day
    location_field = 'city' if location_category == 'city' else 'country'

    query = f"""
        SELECT 
            {date_format} as period
            u.{location_field} as location
            p.category,
            COUNT(DISTINCT o.orderID) as total_orders,
            SUM(o.quantity) as total_quantity,
            COUNT(DISTINCT o.userID) as unique_customers
        FROM FactOrders o
        JOIN DimProducts p ON o.productID = p.productID
        JOIN DimUsers u on o.userID = u.userID
    """
    
    conditions = []
    params = {}
    
    if start_date:
        conditions.append("o.createdAt >= :start_date")
        params['start_date'] = start_date
    if end_date:
        conditions.append("o.createdAt <= :end_date")
        params['end_date'] = end_date
    
    """if location_category:
        conditions.append("o.city = :location") # CHECK KO PA TOH SOON KUNG o.city BA TALGA
        params['location'] = location_category """
    
    query += build_where_clause(conditions)
    query += " GROUP BY p.category ORDER BY total_orders DESC"
    
    try:
        results = execute_query(query, params)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ========== SALES REPORTS ==========
@app.route('/api/orders/total-sales-over-time', methods=['GET'])
def total_orders_over_time():
    """Total Orders Over Time - How many orders do we receive each [DATE CATEGORY]?"""
    date_category = request.args.get('category', 'day')  # day, week, month, quarter, year
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    date_formats = {
        'day': "DATE(createdAt)",
        'week': "DATE_FORMAT(createdAt, '%Y-%u')",
        'month': "DATE_FORMAT(createdAt, '%Y-%m')",
        'quarter': "CONCAT(YEAR(createdAt), '-Q', QUARTER(createdAt))",
        'year': "YEAR(createdAt)"
    }
    
    date_format = date_formats.get(date_category, date_formats['day']) # defaults to day
    
    query = f"""
        SELECT 
            {date_format} as period,
            COUNT(DISTINCT orderID) as total_orders,
            COUNT(DISTINCT userID) as unique_customers,
            SUM(quantity) as total_items
        FROM FactOrders
    """
    
    conditions = []
    params = {}
    
    if start_date:
        conditions.append("o.createdAt >= :start_date")
        params['start_date'] = start_date
    if end_date:
        conditions.append("o.createdAt <= :end_date")
        params['end_date'] = end_date
    
    query += build_where_clause(conditions)
    query += f" GROUP BY {date_format} ORDER BY period"
    
    try:
        results = execute_query(query, params)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ========== CUSTOMER REPORTS ==========


# ========== PRODUCT REPORTS ==========


# ========== RIDER REPORTS ==========


# test


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
