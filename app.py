import os
import re
import sqlite3
from flask import Flask, request, jsonify, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=BASE_DIR, static_url_path="")

# Database configuration
DB_PATH = os.path.join(BASE_DIR, "roster.db")

# Allowed CORS origins (can be configured via environment variable CORS_ORIGINS)
CORS_ORIGINS_RAW = os.environ.get("CORS_ORIGINS", "*")
ALLOWED_ORIGINS = [o.strip() for o in CORS_ORIGINS_RAW.split(",") if o.strip()]

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                body TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


# Initialize database tables on startup
init_db()


# CORS handlers to support browser fetch & preflight OPTIONS requests
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        origin = request.headers.get("Origin")
        if "*" in ALLOWED_ORIGINS or (origin and origin in ALLOWED_ORIGINS):
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")
    if "*" in ALLOWED_ORIGINS or (origin and origin in ALLOWED_ORIGINS):
        response.headers["Access-Control-Allow-Origin"] = origin or "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


# --- Frontend Static File Serving ---
@app.route("/", methods=["GET"])
def serve_index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/favicon.ico")
def favicon():
    return "", 204


# --- API Routes ---
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})


@app.route("/api/contact", methods=["POST"])
def contact():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    body = (data.get("body") or "").strip()

    if not name:
        return jsonify({"ok": False, "error": "Name is required."}), 400

    if not email or not EMAIL_REGEX.match(email):
        return jsonify({"ok": False, "error": "A valid email address is required."}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (name, email, body) VALUES (?, ?, ?)",
            (name, email, body)
        )
        conn.commit()
        contact_id = cursor.lastrowid

    return jsonify({
        "ok": True,
        "message": "Registration/message received successfully.",
        "id": contact_id
    }), 201


@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not email or not EMAIL_REGEX.match(email):
        return jsonify({"ok": False, "error": "A valid email address is required."}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO subscribers (email) VALUES (?)",
            (email,)
        )
        conn.commit()

    return jsonify({
        "ok": True,
        "message": "Subscribed successfully!"
    }), 200


@app.route("/api/contacts", methods=["GET"])
def list_contacts():
    with get_db() as conn:
        rows = conn.execute("SELECT id, name, email, body, created_at FROM contacts ORDER BY id DESC").fetchall()
        contacts = [dict(row) for row in rows]
    return jsonify({"ok": True, "count": len(contacts), "contacts": contacts})


@app.route("/api/subscribers", methods=["GET"])
def list_subscribers():
    with get_db() as conn:
        rows = conn.execute("SELECT id, email, created_at FROM subscribers ORDER BY id DESC").fetchall()
        subscribers = [dict(row) for row in rows]
    return jsonify({"ok": True, "count": len(subscribers), "subscribers": subscribers})


# Serve any remaining static assets (CSS, JS, images, etc.)
@app.route("/<path:filename>", methods=["GET"])
def serve_static(filename):
    file_path = os.path.join(BASE_DIR, filename)
    if os.path.isfile(file_path):
        return send_from_directory(BASE_DIR, filename)
    return jsonify({"error": f"File '{filename}' not found"}), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development" or os.environ.get("DEBUG") == "1"
    print(f"Starting Rustrum Media server on http://localhost:{port}...")
    app.run(host="0.0.0.0", port=port, debug=debug)
