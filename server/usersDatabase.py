"""User operations backed by the MongoDB `users` collection.

User document:
{
    "username": str,
    "userId": str,
    "password": str,      # bcrypt hash
    "projects": [projectId, ...]
}
"""

import bcrypt
from pymongo.errors import DuplicateKeyError

# Projections: never send Mongo's internal _id (not JSON serializable)
# or the password back to the client.
PUBLIC_USER = {"_id": 0, "password": 0}
NO_ID = {"_id": 0}


def _hash_password(password):
    """Return a bcrypt hash of the plain-text password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _check_password(password, hashed):
    """Return True if the plain-text password matches the bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def addUser(db, username, user_id, password):
    user = {"username": username, "userId": user_id, "password": _hash_password(password), "projects": []}
    try:
        db.users.insert_one(user)
    except DuplicateKeyError:
        # The unique indexes on username and userId caught a duplicate.
        return None
    return db.users.find_one({"userId": user_id}, PUBLIC_USER)


def login(db, username, password):
    # Fetch the user by username only, then verify the password against the hash.
    user = db.users.find_one({"username": username})
    if not user:
        return None
    if not _check_password(password, user["password"]):
        return None
    # Strip _id and password before returning.
    return {k: v for k, v in user.items() if k not in ("_id", "password")}


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
