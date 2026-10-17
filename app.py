"""
Flask & MongoDB Atlas project - used for the Git & GitHub assignment
Author: Samriddhi Mishra

Routes:
  /api      -> reads a JSON list from data.json (backend file) and returns it as JSON
  /         -> form that inserts the submitted data into MongoDB Atlas
  /success  -> "Data submitted successfully" page
  /todo     -> To-Do page with a form (frontend)
"""
import json
import os
import re
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# Load MONGO_URI and other settings from the .env file
load_dotenv()

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")

MONGO_URI = os.getenv("MONGO_URI", "").strip()
DB_NAME = os.getenv("MONGO_DB_NAME", "flask_assignment")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "submissions")

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_client = None  # one MongoClient is reused for the whole app


def get_collection(name=COLLECTION_NAME):
    """Return a MongoDB collection, creating the client on first use."""
    global _client
    if not MONGO_URI:
        raise RuntimeError(
            "MONGO_URI is not set. Add your MongoDB Atlas connection string to the .env file."
        )
    if _client is None:
        # Fail after 5 seconds instead of hanging if Atlas cannot be reached
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _client[DB_NAME][name]


# ---------------- JSON API route ----------------
@app.route("/api")
def api():
    """Read the list stored in data.json and send it back as JSON."""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return jsonify({"error": "data.json not found"}), 500
    except json.JSONDecodeError as e:
        return jsonify({"error": f"data.json is not valid JSON: {e}"}), 500

    if not isinstance(data, list):
        return jsonify({"error": "data.json must contain a JSON list"}), 500
    return jsonify(data)


# ---------------- To-Do page (frontend) ----------------
@app.route("/todo")
def todo():
    """Show the To-Do form (Item Name and Item Description)."""
    return render_template("todo.html")


# ---------------- Form + MongoDB Atlas ----------------
@app.route("/", methods=["GET", "POST"])
def form():
    if request.method == "GET":
        return render_template("form.html", error=None, values={})

    values = {
        "name": request.form.get("name", "").strip(),
        "email": request.form.get("email", "").strip(),
        "course": request.form.get("course", "").strip(),
        "message": request.form.get("message", "").strip(),
    }

    # 1. Validate the input - show the error on the same page
    if not values["name"] or not values["email"] or not values["course"]:
        error = "Name, email and course are required."
        return render_template("form.html", error=error, values=values), 400
    if not EMAIL_PATTERN.match(values["email"]):
        error = "Please enter a valid email address."
        return render_template("form.html", error=error, values=values), 400

    # 2. Insert into MongoDB Atlas - show any database error on the same page
    try:
        document = {**values, "submitted_at": datetime.now(timezone.utc)}
        get_collection().insert_one(document)
    except (PyMongoError, RuntimeError) as e:
        reason = (str(e).strip() or type(e).__name__).splitlines()[0][:300]
        error = f"Could not save your data: {reason}"
        return render_template("form.html", error=error, values=values), 500

    # 3. Success - redirect to another page
    return redirect(url_for("success"))


@app.route("/success")
def success():
    return render_template("success.html")


# ---------------- To-Do backend API ----------------
TODO_COLLECTION = os.getenv("MONGO_TODO_COLLECTION", "todos")


@app.route("/submittodoitem", methods=["POST"])
def submit_todo_item():
    """Accept itemName and itemDescription via POST and store them in MongoDB."""
    # Accept both JSON bodies and normal HTML form submissions
    payload = request.get_json(silent=True) or request.form
    item_name = str(payload.get("itemName", "")).strip()
    item_description = str(payload.get("itemDescription", "")).strip()

    if not item_name or not item_description:
        return jsonify({"error": "itemName and itemDescription are required"}), 400

    document = {
        "itemName": item_name,
        "itemDescription": item_description,
        "created_at": datetime.now(timezone.utc),
    }
    try:
        result = get_collection(TODO_COLLECTION).insert_one(document)
    except (PyMongoError, RuntimeError) as e:
        reason = (str(e).strip() or type(e).__name__).splitlines()[0][:300]
        return jsonify({"error": f"Could not save the to-do item: {reason}"}), 500

    return jsonify({
        "message": "To-Do item saved successfully",
        "id": str(result.inserted_id),
        "itemName": item_name,
        "itemDescription": item_description,
    }), 201


if __name__ == "__main__":
    app.run(debug=True, port=5000)
