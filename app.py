from flask import Flask, jsonify, request
from sqlalchemy import create_engine, text
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Database connection
engine = create_engine(
    "mysql+mysqlconnector://chrystel:Chrystel%401234@35.240.197.184:3306/stadvdb"
)

@app.route('/')
def hello():
    return "OLAP Backend API etc etc"

# ========== ORDERS REPORTS ==========


# ========== SALES REPORTS ==========


# ========== CUSTOMER REPORTS ==========


# ========== PRODUCT REPORTS ==========


# ========== RIDER REPORTS ==========


# test


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
