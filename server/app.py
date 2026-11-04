import os

from flask import Flask, jsonify, request

import projectsDatabase
import usersDatabase
from db import get_db


app = Flask(__name__)
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = FRONTEND_ORIGIN
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


if __name__ == "__main__":
    app.run(debug=True)
