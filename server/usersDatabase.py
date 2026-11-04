"""User operations backed by the MongoDB `users` collection.

User document:
{
    "username": str,
    "userId": str,
    "password": str,      # still plain text; encryption is the next step (SR3)
    "projects": [projectId, ...]
}
"""

from pymongo.errors import DuplicateKeyError

# Projections: never send Mongo's internal _id (not JSON serializable)
# or the password back to the client.
PUBLIC_USER = {"_id": 0, "password": 0}
NO_ID = {"_id": 0}


def addUser(db, username, user_id, password):
    user = {"username": username, "userId": user_id, "password": password, "projects": []}
    try:
        db.users.insert_one(user)
    except DuplicateKeyError:
        # The unique indexes on username and userId caught a duplicate.
        return None
    return db.users.find_one({"userId": user_id}, PUBLIC_USER)


def login(db, username, password):
    return db.users.find_one({"username": username, "password": password}, PUBLIC_USER)


def joinProject(db, user_id, project_id):
    if not db.users.find_one({"userId": user_id}, {"_id": 1}):
        return None
    if not db.projects.find_one({"projectId": project_id}, {"_id": 1}):
        return None
    # $addToSet only adds the value if it isn't already in the array,
    # so joining twice is harmless and two simultaneous joins can't clash.
    db.users.update_one({"userId": user_id}, {"$addToSet": {"projects": project_id}})
    db.projects.update_one({"projectId": project_id}, {"$addToSet": {"members": user_id}})
    return db.projects.find_one({"projectId": project_id}, NO_ID)


def getUserProjectsList(db, user_id):
    user = db.users.find_one({"userId": user_id}, {"_id": 0, "projects": 1})
    if not user:
        return None
    return list(db.projects.find({"projectId": {"$in": user["projects"]}}, NO_ID))
