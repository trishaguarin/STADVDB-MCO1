from sqlalchemy import create_engine, text
import time
from typing import List, Tuple
import pandas as pd

engine = create_engine(
    "mysql+mysqlconnector://chrystel:Chrystel%401234@34.142.244.237:3306/stadvdb"
)

def create_indexes():

    secondary_indexes = [
        "CREATE INDEX indx_products_category ON DimProducts(productID)",
        "CREATE INDEX indx_users_couriername ON DimRiders(couriername)",
        "CREATE INDEX indx_users_country ON DimUsers(country)",
        "CREATE INDEX indx_users_city ON DimUsers(city)",
        "CREATE INDEX indx_orders_createdat ON FactOrders(createdAt)",
    ]

    with engine.connect() as conn:
            print("\nCreating secondary indexes...")
            for idx_query in secondary_indexes:
                try:
                    conn.execute(text(idx_query))
                    conn.commit()
                    print(f"✓ Created: {idx_query.split('INDEX')[1].split('ON')[0].strip()}")
                except Exception as e:
                    print(f"✗ Error or already exists: {idx_query.split('INDEX')[1].split('ON')[0].strip()}")
                    print(f"  Details: {str(e)[:100]}")


def drop_indexes():
    """Drop all created indexes for testing purposes"""
    
    indexes_to_drop = [
        "DROP INDEX indx_products_category ON DimProducts",
        "DROP INDEX indx_users_couriername ON DimRiders",
        "DROP INDEX indx_users_country ON DimUsers",
        "DROP INDEX indx_users_city ON DimUsers",
        "DROP INDEX indx_orders_createdat ON FactOrders"
    ]
    
    with engine.connect() as conn:
        print("Dropping indexes...")
        for drop_query in indexes_to_drop:
            try:
                conn.execute(text(drop_query))
                conn.commit()
                print(f"✓ Dropped: {drop_query.split('INDEX')[1].split('ON')[0].strip()}")
            except Exception as e:
                print(f"✗ Index not found or error: {drop_query.split('INDEX')[1].split('ON')[0].strip()}")


def execute_query_with_timing(query: str, description: str) -> Tuple[float, any]:
    """Execute a query and return execution time and results"""
    with engine.connect() as conn:
        start_time = time.time()
        result = conn.execute(text(query))
        rows = result.fetchall()
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"{description}: {execution_time:.4f} seconds ({len(rows)} rows)")
        return execution_time, rows


def analyze_performance():
    """
    Analyze query performance before and after optimization.
    Tests various query patterns to demonstrate optimization benefits.
    """
    # Run 1 conditions: 1 country, 1 profuct category, 1 month, 1 courier
    # Run 2 conditions: 5 countries, 3 product categories, 4 months, 2 couriers
    # Run 3 conditions: At most 5 cities, 5 categories, 3 couriers, and 9-month time period included in queries
    test_queries = {
        "Q1: Total Orders Over Time": 
            """ SELECT 
                    DATE_FORMAT(o.createdAt, '%Y-%m') as period,
                    COUNT(DISTINCT o.orderID) as total_orders
                FROM FactOrders o
                JOIN DimUsers u ON o.userID = u.userID
                WHERE o.createdAt BETWEEN '2025-01-01' AND '2025-10-01'
                GROUP BY DATE_FORMAT(o.createdAt, '%Y-%m')
            """,
        
        "Q2: Total Sales Per Location": 
            """ SELECT 
                    u.city as location,
                    SUM(o.quantity * p.price) as total_sales
                FROM FactOrders o
                JOIN DimUsers u ON o.userID = u.userID
                JOIN DimProducts p ON o.productID = p.productID
                WHERE o.createdAt BETWEEN '2025-01-01' AND '2025-10-01' 
                AND u.city IN ('Adrienfield', 'Alexandria', 'Alexzandermouth', 'Aliborough', 'Alisashire')
                GROUP BY u.city
                ORDER BY total_sales DESC
            """,

        "Q3: Orders by Demographics": 
            """ SELECT 
                    u.gender,
                    CASE
                        WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 18 AND 24 THEN '18-24'
                        WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 25 AND 34 THEN '25-34'
                        WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 35 AND 44 THEN '35-44'
                        WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 45 AND 54 THEN '45-54'
                        WHEN TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 55 AND 64 THEN '55-64'
                        ELSE '65+'
                    END AS age_group,
                    u.city as location,
                    COUNT(DISTINCT o.orderID) as total_orders
                FROM FactOrders o
                JOIN DimUsers u ON o.userID = u.userID
                JOIN DimProducts p ON o.productID = p.productID
                WHERE o.createdAt BETWEEN '2025-06-01' AND '2025-10-01' 
                AND u.city IN ('Adrienfield', 'Alexandria', 'Alexzandermouth', 'Aliborough', 'Alisashire')
                AND u.gender = 'F' AND TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 18 AND 24 
                GROUP BY u.gender, age_group, u.city
                ORDER BY total_orders DESC
            """,

        "Q4: Top-performing per Category": 
            """ WITH ranked_products AS (
                    SELECT 
                        p.name,
                        p.category,
                        SUM(o.quantity) AS total_quantity,
                        SUM(o.quantity * p.price) AS total_revenue,
                        DENSE_RANK() OVER (
                            PARTITION BY p.category
                            ORDER BY SUM(o.quantity * p.price) DESC
                        ) AS category_rank
                    FROM FactOrders o
                    JOIN DimProducts p ON o.productID = p.productID
                    INNER JOIN DimUsers u ON o.userID = u.userID
                    WHERE o.createdAt >= '2025-01-01'
                        AND o.createdAt <= '2025-10-01'
                        AND p.category IN ('Electronics', 'Appliances', 'Toys', 'Bags', 'Gadgets')
                        AND u.city IN ('Adrienfield', 'Alexandria', 'Alexzandermouth', 'Aliborough', 'Alisashire')
                    GROUP BY p.productID, p.name, p.category
                )
                SELECT 
                    name,
                    category,
                    total_quantity,
                    total_revenue
                FROM ranked_products
                WHERE category_rank <= 3
                ORDER BY category, category_rank
            """,
        
        "Q5: Delivery Time":
            """ SELECT 
                    DATE(o.createdAt) as period,
                    u.city as location,
                    r.courierName as courier_name,
                    AVG(ABS(DATEDIFF(o.deliveryDate, o.createdAt))) as avg_delivery_days
                FROM FactOrders o
                JOIN DimRiders r ON o.riderID = r.riderID
                JOIN DimUsers u ON o.userID = u.userID
                WHERE r.courierName IN ('JNT', 'FEDEZ', 'LBCD')
                AND o.createdAt BETWEEN '2025-01-01' AND '2025-10-01'
                AND u.city IN ('Adrienfield', 'Alexandria', 'Alexzandermouth', 'Aliborough', 'Alisashire')
                GROUP BY period, u.city, r.courierName
                ORDER BY avg_delivery_days
                LIMIT 50
            """
    }
    
    print("\n" + "="*80)
    print("PERFORMANCE ANALYSIS: BEFORE vs AFTER OPTIMIZATION")
    print("="*80)
    
    # Store results for comparison
    results = []
    
    print("\n--- TESTING WITHOUT INDEXES (Baseline) ---")
    print("Dropping all indexes first...")
    drop_indexes()
    print("\nExecuting queries without indexes...")
    
    before_times = {}
    for desc, query in test_queries.items():
        try:
            exec_time, _ = execute_query_with_timing(query, desc)
            before_times[desc] = exec_time
        except Exception as e:
            print(f"Error executing {desc}: {str(e)[:100]}")
            before_times[desc] = None
    
    print("\n--- CREATING INDEXES ---")
    create_indexes()
    
    print("\n--- TESTING WITH INDEXES (Optimized) ---")
    after_times = {}
    for desc, query in test_queries.items():
        try:
            exec_time, _ = execute_query_with_timing(query, desc)
            after_times[desc] = exec_time
        except Exception as e:
            print(f"Error executing {desc}: {str(e)[:100]}")
            after_times[desc] = None
    
    # Calculate improvements
    print("\n" + "="*80)
    print("PERFORMANCE COMPARISON SUMMARY")
    print("="*80)
    print(f"{'Query':<50} {'Before':<12} {'After':<12} {'Improvement':<15}")
    print("-"*80)
    
    for desc in test_queries.keys():
        before = before_times.get(desc)
        after = after_times.get(desc)
        
        if before and after:
            improvement = ((before - after) / before) * 100
            speedup = before / after
            print(f"{desc:<50} {before:>10.4f}s {after:>10.4f}s {improvement:>10.2f}% ({speedup:.2f}x)")
            results.append({
                'Query': desc,
                'Before (s)': before,
                'After (s)': after,
                'Improvement (%)': improvement,
                'Speedup': speedup
            })
        else:
            print(f"{desc:<50} {'ERROR':<12} {'ERROR':<12} {'N/A':<15}")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    print("Starting Database Optimization Process...")
    print("="*80)
    
    analyze_performance()