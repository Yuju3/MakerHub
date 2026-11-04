"""Project operations backed by the MongoDB `projects` collection.

Project document:
{
    "projectId": str,
    "name": str,
    "description": str,
    "ownerId": userId,
    "members": [userId, ...]
}
"""

from pymongo.errors import DuplicateKeyError

NO_ID = {"_id": 0}


def queryProject(db, project_id):
    return db.projects.find_one({"projectId": project_id}, NO_ID)


def createProject(db, project_name, project_id, description, owner_id):
    project = {
        "projectId": project_id,
        "name": project_name,
        "description": description,
        "ownerId": owner_id,
        "members": [owner_id],
    }
    try:
        db.projects.insert_one(project)
    except DuplicateKeyError:
        return None
    db.users.update_one({"userId": owner_id}, {"$addToSet": {"projects": project_id}})
    return queryProject(db, project_id)
