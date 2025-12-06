import os
from flask import Flask, jsonify, render_template, request
from psycopg2 import pool
import logging
from contextlib import contextmanager

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Read PostgreSQL connection info from environment variables
POSTGRES_CONNECTION_STRING = os.getenv(
    "CONNECTION_STRING", "postgresql://myuser:mypassword@db:5432/mydb"
)

# Initialize connection pool
connection_pool = None


def init_connection_pool():
    """Initialize PostgreSQL connection pool"""
    global connection_pool
    try:
        connection_pool = pool.ThreadedConnectionPool(
            minconn=1, maxconn=10, dsn=POSTGRES_CONNECTION_STRING
        )
        logger.info("PostgreSQL connection pool created successfully")
    except Exception as e:
        logger.error(
            f"Failed to create connection pool: {e} - Connection string value used is:\n {POSTGRES_CONNECTION_STRING}"
        )
        logger.error(f"Connection string value used is:\n {POSTGRES_CONNECTION_STRING}")
        raise


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = connection_pool.getconn()
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)


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
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
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

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                logger.info(f"Executing SQL: {sql[:100]}...")  # Log first 100 chars

                cur.execute(sql)

                # Handle SELECT queries
                if sql.lower().startswith("select"):
                    if cur.description:
                        columns = [desc[0] for desc in cur.description]
                        rows = cur.fetchall()
                        # Convert rows to list of dicts
                        result_rows = [dict(zip(columns, row)) for row in rows]

                        return jsonify(
                            {
                                "type": "select",
                                "columns": columns,
                                "rows": result_rows,
                                "row_count": len(result_rows),
                            }
                        )
                    else:
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
                    return jsonify(
                        {
                            "type": "modify",
                            "rows_affected": cur.rowcount,
                            "message": "Query executed successfully",
                        }
                    )

    except Exception as e:
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


def cleanup():
    """Cleanup function to close connection pool"""
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        logger.info("Connection pool closed")


if __name__ == "__main__":
    try:
        init_connection_pool()
        app.run(host="0.0.0.0", port=9998, debug=False)  # Set debug=False in production
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        cleanup()
