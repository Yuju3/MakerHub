import os
import re

from flask import Flask, jsonify, request

import hardwareDatabase
import projectsDatabase
import usersDatabase
from db import get_db


app = Flask(__name__)

# Accept a comma-separated list so both localhost and the Render URL work.
_raw_origins = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000,*")
ALLOWED_ORIGINS = {o.strip() for o in _raw_origins.split(",") if o.strip()}


def is_allowed_origin(origin):
    if not origin:
        return False
    if "*" in ALLOWED_ORIGINS:
        return True
    if origin in ALLOWED_ORIGINS:
        return True
    if origin.startswith("http://localhost:") or origin.startswith("http://127.0.0.1:"):
        return True
    if origin.endswith(".onrender.com"):
        return True
    return False


# Hardware set names become field names inside each project's hwUsage, so
# they can't contain "." or "$", which MongoDB treats as special.
HW_NAME_PATTERN = re.compile(r"^[A-Za-z0-9 _-]{1,50}$")

ERROR_STATUS = {"invalid": 400, "forbidden": 403, "not_found": 404, "conflict": 409}


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin", "")
    if is_allowed_origin(origin):
        response.headers["Access-Control-Allow-Origin"] = origin
    elif "*" in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def body():
    return request.get_json(silent=True) or {}


def missing_strings(data, fields):
    """Return the fields that are absent, empty, or not plain strings.

    Requiring strings matters with MongoDB: a JSON body like
    {"password": {"$ne": ""}} would otherwise be passed into a query
    as an operator and match any password (NoSQL injection).
    """
    return [f for f in fields if not isinstance(data.get(f), str) or not data[f].strip()]


def is_positive_int(value):
    # bool is a subclass of int in Python, so rule out true/false explicitly.
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def require(data, fields):
    missing = missing_strings(data, fields)
    if missing:
        return jsonify({"error": f"{', '.join(fields)} are required text fields"}), 400
    return None


@app.get("/health")
def health():
    try:
        get_db().command("ping")
        return jsonify({"status": "ok", "database": "connected"})
    except Exception as error:
        return jsonify({"status": "error", "database": str(error)}), 503


@app.post("/add_user")
def add_user():
    data = body()
    if (error := require(data, ("username", "userId", "password"))):
        return error
    user = usersDatabase.addUser(get_db(), data["username"], data["userId"], data["password"])
    if not user:
        return jsonify({"error": "username or userId already exists"}), 409
    return jsonify(user), 201


@app.post("/login")
def login():
    data = body()
    # Missing or non-text credentials get the same answer as wrong ones,
    # so the response never hints at which part was wrong.
    if missing_strings(data, ("username", "password")):
        return jsonify({"error": "invalid username or password"}), 401
    user = usersDatabase.login(get_db(), data["username"], data["password"])
    if not user:
        return jsonify({"error": "invalid username or password"}), 401
    return jsonify(user)


@app.post("/create_project")
def create_project():
    data = body()
    if (error := require(data, ("projectId", "name", "ownerId"))):
        return error
    description = data.get("description", "")
    if not isinstance(description, str):
        return jsonify({"error": "description must be text"}), 400
    db = get_db()
    if not db.users.find_one({"userId": data["ownerId"]}, {"_id": 1}):
        return jsonify({"error": "owner does not exist"}), 404
    project = projectsDatabase.createProject(
        db, data["name"], data["projectId"], description, data["ownerId"]
    )
    if not project:
        return jsonify({"error": "projectId already exists"}), 409
    return jsonify(project), 201


@app.post("/join_project")
def join_project():
    data = body()
    if (error := require(data, ("userId", "projectId"))):
        return error
    project = usersDatabase.joinProject(get_db(), data["userId"], data["projectId"])
    if not project:
        return jsonify({"error": "user or project does not exist"}), 404
    return jsonify(project)


@app.get("/get_user_projects_list/<user_id>")
def get_user_projects(user_id):
    projects = usersDatabase.getUserProjectsList(get_db(), user_id)
    if projects is None:
        return jsonify({"error": "user does not exist"}), 404
    return jsonify(projects)


@app.post("/get_user_projects_list")
def get_user_projects_post():
    data = body()
    if (error := require(data, ("userId",))):
        return error
    return get_user_projects(data["userId"])


@app.get("/get_project_info/<project_id>")
def get_project(project_id):
    project = projectsDatabase.queryProject(get_db(), project_id)
    if not project:
        return jsonify({"error": "project does not exist"}), 404
    return jsonify(project)


@app.post("/get_project_info")
def get_project_post():
    data = body()
    if (error := require(data, ("projectId",))):
        return error
    return get_project(data["projectId"])


# ---------------------------------------------------------------- hardware


@app.get("/get_all_hw")
def get_all_hw():
    """Capacity and availability of every hardware set."""
    return jsonify(hardwareDatabase.getAllHardwareSets(get_db()))


@app.get("/get_all_hw_names")
def get_all_hw_names():
    return jsonify(hardwareDatabase.getAllHwNames(get_db()))


@app.get("/get_hw_info/<hw_name>")
def get_hw_info(hw_name):
    hw_set = hardwareDatabase.queryHardwareSet(get_db(), hw_name)
    if not hw_set:
        return jsonify({"error": "hardware set does not exist"}), 404
    return jsonify(hw_set)


@app.post("/get_hw_info")
def get_hw_info_post():
    data = body()
    if (error := require(data, ("hwName",))):
        return error
    return get_hw_info(data["hwName"])


@app.post("/create_hardware_set")
def create_hardware_set():
    data = body()
    if (error := require(data, ("hwName",))):
        return error
    if not HW_NAME_PATTERN.match(data["hwName"]):
        return jsonify({"error": "hwName may only use letters, numbers, spaces, - and _"}), 400
    if not is_positive_int(data.get("capacity")):
        return jsonify({"error": "capacity must be a positive whole number"}), 400
    hw_set = hardwareDatabase.createHardwareSet(get_db(), data["hwName"], data["capacity"])
    if not hw_set:
        return jsonify({"error": "hardware set already exists"}), 409
    return jsonify(hw_set), 201


def hardware_request(operation):
    """Shared handling for /check_out and /check_in."""
    data = body()
    if (error := require(data, ("projectId", "hwName", "userId"))):
        return error
    if not is_positive_int(data.get("quantity")):
        return jsonify({"error": "quantity must be a positive whole number"}), 400
    try:
        result = operation(
            get_db(), data["projectId"], data["hwName"], data["quantity"], data["userId"]
        )
    except projectsDatabase.HardwareRequestError as error:
        return jsonify({"error": error.message}), ERROR_STATUS[error.kind]
    return jsonify(result)


@app.post("/check_out")
def check_out():
    return hardware_request(projectsDatabase.checkOutHW)


@app.post("/check_in")
def check_in():
    return hardware_request(projectsDatabase.checkInHW)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
