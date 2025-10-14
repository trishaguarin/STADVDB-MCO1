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
    
    test_queries = {
        "Q1: Total Orders Over Time": 
            """ SELECT 
                    DATE_FORMAT(o.createdAt, '%Y-%m') as period,
                    COUNT(DISTINCT o.orderID) as total_orders
                FROM FactOrders o
                JOIN DimUsers u ON o.userID = u.userID
                WHERE o.createdAt BETWEEN '2025-09-01' AND '2025-10-01'
                GROUP BY DATE_FORMAT(o.createdAt, '%Y-%m')
            """,

        "Q2: Total Sales Per Location": 
            """ SELECT 
                    u.country as location,
                    SUM(o.quantity * p.price) as total_sales
                FROM FactOrders o
                JOIN DimUsers u ON o.userID = u.userID
                JOIN DimProducts p ON o.productID = p.productID
                WHERE o.createdAt BETWEEN '2025-09-01' AND '2025-10-01' AND u.country IN ('Afghanistan', 'Philippines', 'Samoa', 'United Kingdom')
                GROUP BY u.country
                ORDER BY total_sales DESC
            """,
        
        "Q3: Total Sales per Product Category (per Time)": 
            """ SELECT 
                    p.category,
                    SUM(o.quantity * p.price) as total_sales
                FROM FactOrders o
                JOIN DimProducts p ON o.productID = p.productID
                JOIN DimUsers u ON o.userID = u.userID
                WHERE o.createdAt BETWEEN '2025-09-01' AND '2025-10-01' AND u.country IN ('Afghanistan', 'Philippines', 'Samoa', 'United Kingdom')
                GROUP BY p.category
                ORDER BY total_sales DESC
            """,
        
        "Q4: Orders by demographics": 
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
                    u.country as location,
                    COUNT(DISTINCT o.orderID) as total_orders
                FROM FactOrders o
                JOIN DimUsers u ON o.userID = u.userID
                JOIN DimProducts p ON o.productID = p.productID
                WHERE o.createdAt BETWEEN '2025-09-01' AND '2025-10-01' AND u.country IN ('Afghanistan', 'Philippines', 'Samoa', 'United Kingdom')
                        AND u.gender = 'F' AND TIMESTAMPDIFF(YEAR, u.dateofBirth, CURDATE()) BETWEEN 18 AND 24 
                GROUP BY u.gender, age_group, u.country
                ORDER BY total_orders DESC
            """,
        
        "Q5: Top-Selling Products Per Category": 
            """ SELECT 
                    p.name,
                    p.category,
                    SUM(o.quantity * p.price) as total
                FROM FactOrders o
                RIGHT JOIN DimProducts p ON o.productID = p.productID
                LEFT JOIN DimUsers u ON o.userID = u.userID
                WHERE o.createdAt BETWEEN '2025-09-01' AND '2025-10-01' AND u.country = 'Philippines'
                GROUP BY p.productID, p.category
                ORDER BY total DESC
            """,
        
        "Q6: Delivery Time":
            """ SELECT 
                    r.courierName as courier_name,
                    COUNT(DISTINCT o.orderID) as total_deliveries,
                    AVG(ABS(DATEDIFF(o.deliveryDate, o.createdAt))) as avg_delivery_days,
                    MIN(ABS(DATEDIFF(o.deliveryDate, o.createdAt))) as min_delivery_days,
                    MAX(ABS(DATEDIFF(o.deliveryDate, o.createdAt))) as max_delivery_days
                FROM FactOrders o
                JOIN DimRiders r ON o.riderID = r.riderID
                JOIN DimUsers u ON o.userID = u.userID
                WHERE r.courierName = 'JNT' AND o.createdAt BETWEEN '2025-09-01' AND '2025-10-01' AND u.country = 'Philippines'
                GROUP BY r.courierName
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
    print("OPTIMIZATION STRATEGIES EMPLOYED:")
    print("="*80)


if __name__ == '__main__':
    print("Starting Database Optimization Process...")
    print("="*80)
    
    # Option 1: Full analysis (drop, test, create, test)
    analyze_performance()
    
    # Option 2: Just create indexes without testing
    # create_indexes()
    
    print("\n" + "="*80)
    print("✓ Optimization process completed!")
    print("="*80)