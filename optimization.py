from sqlalchemy import create_engine, text

engine = create_engine(
    "mysql+mysqlconnector://trish:Trish%401234@35.240.197.184:3306/stadvdb"
)
"""
def create_indexes():
    indexes = [
        # Indexes for fact table
        "CREATE INDEX idx_factorders_createdat ON FactOrders(createdAt)",
        
        # Indexes for dimension table

        # etc etc

    ]


# Something for analyzing query performance bf and aft optimizing
def analyze_performance():


if __name__ == '__main__':
    create_indexes()
    analyze_performance()
    print("Optimization is done.")
