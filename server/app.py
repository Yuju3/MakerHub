import json
from pathlib import Path

from flask import Flask, jsonify, request

import projectsDatabase
import usersDatabase


app = Flask(__name__)
DATABASE_FILE = Path(__file__).with_name("database.json")


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def load_data():
    with DATABASE_FILE.open() as file:
        return json.load(file)


def save_data(data):
    with DATABASE_FILE.open("w") as file:
        json.dump(data, file, indent=2)


def body():
    return request.get_json(silent=True) or {}


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/add_user")
def add_user():
    data = body()
    if any(not data.get(field) for field in ("username", "userId", "password")):
        return jsonify({"error": "username, userId, and password are required"}), 400
    database = load_data()
    user = usersDatabase.addUser(database, data["username"], data["userId"], data["password"])
    if not user:
        return jsonify({"error": "username or userId already exists"}), 409
    save_data(database)
    return jsonify(user), 201


@app.post("/login")
def login():
    data = body()
    user = usersDatabase.login(load_data(), data.get("username"), data.get("password"))
    if not user:
        return jsonify({"error": "invalid username or password"}), 401
    return jsonify(user)


@app.post("/create_project")
def create_project():
    data = body()
    if any(not data.get(field) for field in ("projectId", "name", "ownerId")):
        return jsonify({"error": "projectId, name, and ownerId are required"}), 400
    database = load_data()
    if not any(user["userId"] == data["ownerId"] for user in database["users"]):
        return jsonify({"error": "owner does not exist"}), 404
    project = projectsDatabase.createProject(
        database, data["name"], data["projectId"], data.get("description", ""), data["ownerId"]
    )
    if not project:
        return jsonify({"error": "projectId already exists"}), 409
    save_data(database)
    return jsonify(project), 201


@app.post("/join_project")
def join_project():
    data = body()
    if not data.get("userId") or not data.get("projectId"):
        return jsonify({"error": "userId and projectId are required"}), 400
    database = load_data()
    project = usersDatabase.joinProject(database, data["userId"], data["projectId"])
    if not project:
        return jsonify({"error": "user or project does not exist"}), 404
    save_data(database)
    return jsonify(project)


@app.get("/get_user_projects_list/<user_id>")
def get_user_projects(user_id):
    projects = usersDatabase.getUserProjectsList(load_data(), user_id)
    if projects is None:
        return jsonify({"error": "user does not exist"}), 404
    return jsonify(projects)


@app.post("/get_user_projects_list")
def get_user_projects_post():
    user_id = body().get("userId")
    if not user_id:
        return jsonify({"error": "userId is required"}), 400
    return get_user_projects(user_id)


@app.get("/get_project_info/<project_id>")
def get_project(project_id):
    project = projectsDatabase.queryProject(load_data(), project_id)
    if not project:
        return jsonify({"error": "project does not exist"}), 404
    return jsonify(project)


@app.post("/get_project_info")
def get_project_post():
    project_id = body().get("projectId")
    if not project_id:
        return jsonify({"error": "projectId is required"}), 400
    return get_project(project_id)


if __name__ == "__main__":
    app.run(debug=True)
