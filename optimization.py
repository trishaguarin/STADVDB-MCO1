from sqlalchemy import create_engine, text
import time
from typing import List, Tuple
import pandas as pd

engine = create_engine(
    "mysql+mysqlconnector://megan:Megan%401234@34.142.244.237:3306/stadvdb"
)

def create_indexes():

    secondary_indexes = [
        "CREATE INDEX indx_products_category ON DimProduucts(productID)",
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
        "DROP INDEX indx_products_category ON DimProduucts",
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
        "Q1: Select by Primary Key (PRODUCTS)": 
            "SELECT * FROM PRODUCTS WHERE productID = 'PROD001'",
        
        "Q2: Filter by Category (PRODUCTS)": 
            "SELECT * FROM PRODUCTS WHERE category = 'Electronics' LIMIT 100",
        
        "Q3: Join Users and Orders": 
            """SELECT u.userID, u.country, COUNT(o.orderID) as order_count
               FROM USERS u 
               LEFT JOIN ORDERS o ON u.userID = o.userID
               GROUP BY u.userID, u.country
               LIMIT 100""",
        
        "Q4: Filter by Country and City (USERS)": 
            "SELECT * FROM USERS WHERE country = 'USA' AND city = 'New York' LIMIT 100",
        
        "Q5: Orders by Date Range": 
            """SELECT * FROM ORDERS 
               WHERE createdAt BETWEEN '2024-01-01' AND '2024-12-31'
               LIMIT 100""",
        
        "Q6: Complex Join (Orders, Users, Products, Riders)":
            """SELECT o.orderID, u.country, p.category, r.courierName
               FROM ORDERS o
               JOIN USERS u ON o.userID = u.userID
               JOIN PRODUCTS p ON o.productID = p.productID
               JOIN RIDERS r ON o.riderID = r.riderID
               WHERE u.country = 'USA' AND p.category = 'Electronics'
               LIMIT 50""",
        
        "Q7: Aggregation by Courier":
            """SELECT r.courierName, COUNT(o.orderID) as delivery_count
               FROM RIDERS r
               LEFT JOIN ORDERS o ON r.riderID = o.riderID
               GROUP BY r.courierName
               ORDER BY delivery_count DESC
               LIMIT 20"""
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