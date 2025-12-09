import os
from flask import Flask, jsonify, render_template, request
import psycopg2
import logging
from urllib.parse import urlparse

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Read PostgreSQL connection info from environment variables

# Parse connection string

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432").replace("'", ""))
DB_NAME = os.getenv("DB_NAME", "mydb")
DB_USER = os.getenv("DB_USER", "myuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mypassword")


def get_db_connection():
    """Create a new database connection"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


@app.route("/metadata")
def metadata():
    """Return app metadata"""
    return jsonify(
        {
            "app_name": os.getenv("APP_NAME", "Unknown App"),
            "app_version": os.getenv("APP_VERSION", "0.0.0"),
            "deploy_region": os.getenv("DEPLOY_REGION", "unknown-region"),
        }
    )


@app.route("/")
def home():
    """Serve the HTML page"""
    return render_template("index.html")


@app.route("/health")
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 503


@app.route("/run_sql", methods=["POST"])
def run_sql():
    """Execute SQL queries"""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    sql = data.get("sql", "").strip()

    if not sql:
        return jsonify({"error": "No SQL provided"}), 400

    # Security: Prevent multiple statements (basic protection)
    if ";" in sql[:-1]:  # Allow trailing semicolon
        return jsonify({"error": "Multiple statements not allowed"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        logger.info(f"Executing SQL: {sql[:100]}...")  # Log first 100 chars

        cur.execute(sql)

        # Handle SELECT queries
        if sql.lower().startswith("select"):
            if cur.description:
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                # Convert rows to list of dicts
                result_rows = [dict(zip(columns, row)) for row in rows]

                cur.close()
                conn.close()

                return jsonify(
                    {
                        "type": "select",
                        "columns": columns,
                        "rows": result_rows,
                        "row_count": len(result_rows),
                    }
                )
            else:
                cur.close()
                conn.close()

                return jsonify(
                    {
                        "type": "select",
                        "columns": [],
                        "rows": [],
                        "row_count": 0,
                    }
                )

        # Handle INSERT, UPDATE, DELETE, etc.
        else:
            conn.commit()
            rows_affected = cur.rowcount
            cur.close()
            conn.close()

            return jsonify(
                {
                    "type": "modify",
                    "rows_affected": rows_affected,
                    "message": "Query executed successfully",
                }
            )

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        logger.error(f"SQL execution error: {e}", exc_info=True)
        return jsonify({"error": str(e), "type": "execution_error"}), 400


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    try:
        logger.info(f"Connecting to database at {DB_HOST}:{DB_PORT}/{DB_NAME}")
        app.run(host="0.0.0.0", port=9998, debug=False)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
