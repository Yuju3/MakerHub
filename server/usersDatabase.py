"""User operations for the local JSON database."""


def addUser(data, username, user_id, password):
    if any(user["username"] == username or user["userId"] == user_id for user in data["users"]):
        return None
    user = {"username": username, "userId": user_id, "password": password, "projects": []}
    data["users"].append(user)
    return public_user(user)


def login(data, username, password):
    user = next(
        (user for user in data["users"] if user["username"] == username and user["password"] == password),
        None,
    )
    return public_user(user) if user else None


def joinProject(data, user_id, project_id):
    user = next((user for user in data["users"] if user["userId"] == user_id), None)
    project = next((project for project in data["projects"] if project["projectId"] == project_id), None)
    if not user or not project:
        return None
    if project_id not in user["projects"]:
        user["projects"].append(project_id)
    if user_id not in project["members"]:
        project["members"].append(user_id)
    return project


def getUserProjectsList(data, user_id):
    user = next((user for user in data["users"] if user["userId"] == user_id), None)
    if not user:
        return None
    return [project for project in data["projects"] if project["projectId"] in user["projects"]]


def public_user(user):
    return {key: value for key, value in user.items() if key != "password"}
