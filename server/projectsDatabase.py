"""Project operations for the local JSON database."""


def queryProject(data, project_id):
    return next((project for project in data["projects"] if project["projectId"] == project_id), None)


def createProject(data, project_name, project_id, description, owner_id):
    if queryProject(data, project_id):
        return None
    project = {
        "projectId": project_id,
        "name": project_name,
        "description": description,
        "ownerId": owner_id,
        "members": [owner_id],
    }
    data["projects"].append(project)
    owner = next(user for user in data["users"] if user["userId"] == owner_id)
    owner["projects"].append(project_id)
    return project
