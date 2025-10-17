import os
from flask import Flask, jsonify, render_template, request
import psycopg2
import time

app = Flask(__name__)

# Read PostgreSQL connection info from environment variables
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", 5432)


def connect_to_db():
    # Connect to PostgreSQL at app startup
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            port=POSTGRES_PORT,
        )
        print("Connected to PostgreSQL successfully.")
    except Exception as e:
        print(f"Failed to connect to PostgreSQL: {e}")
        time.sleep(5)
        return connect_to_db()
    return conn


conn = connect_to_db()


@app.route("/metadata")
def index():
    return jsonify(
        {
            "app_name": os.getenv("APP_NAME", "Unknown App"),
            "app_version": os.getenv("APP_VERSION", "0.0.0"),
            "deploy_region": os.getenv("DEPLOY_REGION", "unknown-region"),
        }
    )


# Serve the HTML page
@app.route("/")
def home():
    return render_template("index.html")


# Endpoint to run SQL queries
@app.route("/run_sql", methods=["POST"])
def run_sql():
    data = request.get_json()
    sql = data.get("sql", "")
    if not sql:
        return jsonify({"error": "No SQL provided."}), 400
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            if sql.strip().lower().startswith("select"):
                columns = [desc[0] for desc in cur.description]
                rows = [dict(zip(columns, row)) for row in cur.fetchall()]
                return jsonify({"type": "select", "columns": columns, "rows": rows})
            else:
                conn.commit()
                return jsonify({"type": "other", "rowcount": cur.rowcount})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9998)
