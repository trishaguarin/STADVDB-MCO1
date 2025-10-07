from flask import Flask, jsonify
import mysql.connector

app = Flask(__name__)

@app.route('/')
def hello():
    return "Flask is working!"

@app.route('/test-db')
def test_db():
    try:
        conn = mysql.connector.connect(
            host="35.240.197.184",
            user="chrystel",
            password="Chrystel%401234",
            database="stadvdb"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM FactOrders")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return jsonify({"status": "Database connected!", "fact_orders_count": count})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
