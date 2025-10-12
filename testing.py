from flask import Flask, jsonify, request
from sqlalchemy import create_engine, text
from flask_cors import CORS
from datetime import datetime
import traceback

app = Flask(__name__)
CORS(app)

# Database connection
engine = create_engine(
    "mysql+mysqlconnector://root:12345678@127.0.0.1:3306/cleaned"
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
@app.route('/api/orders/total-orders-over-time', methods=['GET'])
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
        FROM factorders
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
@app.route('/api/orders/total-orders-by-location', methods=['GET'])
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
        FROM factorders o 
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
<<<<<<< HEAD
# working BUTTT need to make it so that if want lang na by date, date lang ung sa group by, loc lang, or neither, or both. 

@app.route('/api/orders/total-orders-by-product-category', methods=['GET']) 
def orders_by_product_category():
    """Total Orders Per Product Category - Which product categories generate the most orders?"""
    date_category = request.args.get('category', 'day') # day, week, month, quarter, year
    location_category = request.args.get('type', 'city')  # city, country
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
=======
@app.route('/api/orders/total-orders-by-product-category', methods=['GET']) 
def orders_by_product_category():
    """Total Orders Per Product Category - Which product categories generate the most orders based on [CATEGORY]?"""
    date_category = request.args.get('category')  # day, week, month, quarter, year or None
    location_category = request.args.get('type')  # city, country or None
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Date format map
>>>>>>> parent of 3fcd3a9 (f)
    date_formats = {
        'day': "DATE(o.createdAt)",
        'week': "DATE_FORMAT(o.createdAt, '%Y-%u')",
        'month': "DATE_FORMAT(o.createdAt, '%Y-%m')",
        'quarter': "CONCAT(YEAR(o.createdAt), '-Q', QUARTER(o.createdAt))",
        'year': "YEAR(o.createdAt)"
    }

<<<<<<< HEAD
    date_format = date_formats.get(date_category, date_formats['day']) # defaults to day
    location_field = 'city' if location_category == 'city' else 'country'

    conditions = []
    params = {}
    
=======
    # Initialize variables
    select_fields = ["p.category"]
    group_by_fields = ["p.category"]

    # Handle date grouping
    if date_category in date_formats:
        date_format = date_formats[date_category]
        select_fields.append(f"{date_format} AS period")
        group_by_fields.append("period")

    # Handle location grouping
    if location_category in ['city', 'country']:
        location_field = f"u.{location_category}"
        select_fields.append(f"{location_field} AS location")
        group_by_fields.append("location")

    # Common aggregation fields
    select_fields.extend([
        "COUNT(DISTINCT o.orderID) as total_orders",
        "SUM(o.quantity) as total_quantity",
        "COUNT(DISTINCT o.userID) as unique_customers"
    ])

    # Build WHERE clause
    conditions = []
    params = {}

>>>>>>> parent of 3fcd3a9 (f)
    if start_date:
        conditions.append("o.createdAt >= :start_date")
        params['start_date'] = start_date
    if end_date:
        conditions.append("o.createdAt <= :end_date")
        params['end_date'] = end_date
<<<<<<< HEAD

    where_clause = build_where_clause(conditions)

    query = f"""
        SELECT 
            {date_format} as period,
            u.{location_field} as location,
            p.category,
            COUNT(DISTINCT o.orderID) as total_orders,
            SUM(o.quantity) as total_quantity,
            COUNT(DISTINCT o.userID) as unique_customers
        FROM factorders o
        JOIN dimproducts p ON o.productID = p.productID
        JOIN dimusers u on o.userID = u.userID
        {where_clause}
        GROUP BY p.category, period, location  # to adjust pa this
        ORDER BY total_orders DESC
    """
    
=======
        
    where_clause = build_where_clause(conditions)

    # Final query
    query = f"""
        SELECT 
            {', '.join(select_fields)}
        FROM factorders o
        JOIN dimproducts p ON o.productID = p.productID
        JOIN dimusers u ON o.userID = u.userID
        {where_clause}
        GROUP BY {', '.join(group_by_fields)}
        ORDER BY total_orders DESC
    """

>>>>>>> parent of 3fcd3a9 (f)
    try:
        results = execute_query(query, params)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ========== SALES REPORTS ==========
@app.route('/api/orders/total-sales-over-time', methods=['GET'])
def total_sales_over_time():
    """Total Orders Over Time - How many sales do we receive each [DATE CATEGORY]?"""
    date_category = request.args.get('category', 'day')  # day, week, month, quarter, year
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    date_formats = {
        'day': "DATE(o.createdAt)",
        'week': "DATE_FORMAT(o.createdAt, '%Y-%u')",
        'month': "DATE_FORMAT(o.createdAt, '%Y-%m')",
        'quarter': "CONCAT(YEAR(o.createdAt), '-Q', QUARTER(o.createdAt))", # recheck how the quarter works
        'year': "YEAR(o.createdAt)"
    }
    
    date_format = date_formats.get(date_category, date_formats['day']) # defaults to day
    
    query = f"""
        SELECT 
            {date_format} as period,
            SUM(o.quantity * p.price) as total_sales,
            COUNT(DISTINCT orderID) as total_orders,
            SUM(o.quantity) as total_items
        FROM factorders o
        JOIN dimproducts p ON o.productID = p.productID 
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
    
# ===================================================================
@app.route('/api/orders/total-sales-by-location', methods=['GET'])
def sales_by_location():
    """Total Sales Per Location - How many sales do we receive in [LOCATION CATEGORY]?"""
    location_type = request.args.get('type', 'city')  # city, country
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    location_field = 'city' if location_type == 'city' else 'country' # defaults to city first
    
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
            u.{location_field} as period,
            SUM(o.quantity * p.price) as total_sales,
            COUNT(DISTINCT orderID) as total_orders,
            SUM(o.quantity) as total_items
        FROM factorders o
        JOIN dimusers u ON o.userID = u.userID
        JOIN dimproducts p ON o.productID = p.productID
        {where_clause}
        GROUP BY u.{location_field}
        ORDER BY total_orders DESC
    """

    try:
        results = execute_query(query, params)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =====================================
# working BUTTT need to make it so that if want lang na by date, date lang ung sa group by, loc lang, or neither, or both. 

@app.route('/api/orders/total-sales-by-product-category/', methods=['GET']) 
def sales_by_product_category():
    """Total Sales Per Product Category - Which product categories generate the most sales?"""
    date_category = request.args.get('category', 'day') # day, week, month, quarter, year
    location_category = request.args.get('type', 'city')  # city, country
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    date_formats = {
        'day': "DATE(o.createdAt)",
        'week': "DATE_FORMAT(o.createdAt, '%Y-%u')",
        'month': "DATE_FORMAT(o.createdAt, '%Y-%m')",
        'quarter': "CONCAT(YEAR(o.createdAt), '-Q', QUARTER(o.createdAt))",
        'year': "YEAR(o.createdAt)"
    }

    date_format = date_formats.get(date_category, date_formats['day']) # defaults to day
    location_field = 'city' if location_category == 'city' else 'country'

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
            {date_format} as period,
            u.{location_field} as location,
            p.category,
            SUM(o.quantity * p.price) as total_sales,
            COUNT(DISTINCT orderID) as total_orders,
            SUM(o.quantity) as total_items
        FROM factorders o
        JOIN dimproducts p ON o.productID = p.productID
        JOIN dimusers u on o.userID = u.userID
        {where_clause}
        GROUP BY p.category, period, location  # to adjust pa this
        ORDER BY total_orders DESC
    """
    
    try:
        results = execute_query(query, params)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ========== CUSTOMER REPORTS ==========
# kinda works?? BUT still need to make sure  

@app.route('/api/customers/orders-by-demographics', methods=['GET'])
def orders_by_demographics():
    """How many orders came from [GENDER] customers aged [AGE GROUP] in [LOCATION]"""
    gender = request.args.get('gender') 
    age_group = request.args.get('age_group')
    location_type = request.args.get('type', 'city') # city, country
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    location_field = 'city' if location_type == 'city' else 'country'

    conditions = []
    params = {}
    
    if gender:
        conditions.append("u.gender = :gender")
        params['gender'] = gender
        
    if age_group:
        age_ranges = {
            '18-24': (18, 24),
            '25-34': (25, 34),
            '35-44': (35, 44),
            '45-54': (45, 54),
            '55-64': (55, 64),
            '65+': (65, 150)
        }
        if age_group in age_ranges:
            min_age, max_age = age_ranges[age_group]
            conditions.append("TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN :min_age AND :max_age")
            params['min_age'] = min_age
            params['max_age'] = max_age
    
    if start_date:
        conditions.append("o.createdAt >= :start_date")
        params['start_date'] = start_date
    if end_date:
        conditions.append("o.createdAt <= :end_date")
        params['end_date'] = end_date

    where_clause = build_where_clause(conditions)
    query = f"""
        SELECT 
            u.gender,
            CASE
                WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 18 AND 24 THEN '18-24'
                WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 25 AND 34 THEN '25-34'
                WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 35 AND 44 THEN '35-44'
                WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 45 AND 54 THEN '45-54'
                WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 55 AND 64 THEN '55-64'
                ELSE '65+'
            END AS age_group,
            u.{location_field} as location,
            COUNT(DISTINCT o.orderID) as total_orders,
            COUNT(DISTINCT u.userID) as unique_customers
        FROM factorders o
        JOIN dimusers u ON o.userID = u.userID
        JOIN dimproducts p ON o.productID = p.productID
        {where_clause}
        GROUP BY u.gender, age_group, u.{location_field} # adjust this 
        ORDER BY total_orders DESC
    """
    
    try:
        results = execute_query(query, params)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ===================================================
@app.route('/api/customers/segments-revenue', methods=['GET'])
def customer_segments_revenue():
    """Customer Segments - Which customer segment contributes the most to total revenue?"""
    segment_type = request.args.get('segment', 'age')  # age, gender, location
    location_type = request.args.get('type', 'city') # city, country
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    location_field = 'city' if location_type == 'city' else 'country'

    if segment_type == 'age':
        segment_field = """
            CASE
                WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 18 AND 24 THEN '18-24'
                WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 25 AND 34 THEN '25-34'
                WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 35 AND 44 THEN '35-44'
                WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 45 AND 54 THEN '45-54'
                WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 55 AND 64 THEN '55-64'
                ELSE '65+'
            END
        """
    elif segment_type == 'gender':
        segment_field = "u.gender"
    else:  # location
        segment_field = f"u.{location_field}"
    
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
            {segment_field} as segment,
            SUM(o.quantity * p.price) as total_revenue,
            COUNT(DISTINCT o.orderID) as total_orders,
            COUNT(DISTINCT u.userID) as unique_customers,
            AVG(o.quantity * p.price) as avg_order_value
        FROM factorders o
        JOIN dimusers u ON o.userID = u.userID
        JOIN dimproducts p ON o.productID = p.productID
        {where_clause}
        GROUP BY {segment_field} 
        ORDER BY total_revenue DESC
        """
    
    try:
        results = execute_query(query, params)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ========== PRODUCT REPORTS ==========


# ========== RIDER REPORTS ==========


# test


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
