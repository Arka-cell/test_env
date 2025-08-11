import os
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return jsonify(
        {
            "app_name": os.getenv("APP_NAME", "Unknown App"),
            "app_version": os.getenv("APP_VERSION", "0.0.0"),
            "deploy_region": os.getenv("DEPLOY_REGION", "unknown-region"),
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
