from sqlalchemy import create_engine, text

engine = create_engine(
    "mysql+mysqlconnector://trish:Trish%401234@35.240.197.184:3306/stadvdb"
)
