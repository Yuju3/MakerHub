"""Project operations backed by the MongoDB `projects` collection.

Project document:
{
    "projectId": str,
    "name": str,
    "description": str,
    "ownerId": userId,
    "members": [userId, ...],
    "hwUsage": {hwName: units checked out by this project, ...}
}
"""

from pymongo.errors import DuplicateKeyError

import hardwareDatabase

NO_ID = {"_id": 0}


class HardwareRequestError(Exception):
    """A check-out or check-in that can't be done.

    kind is "invalid", "not_found", "forbidden", or "conflict". The API layer
    turns it into an HTTP status code, so this module knows nothing about HTTP.
    """

    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind
        self.message = message


def withUsageDefaults(project):
    # Projects created before hardware tracking existed have no hwUsage field.
    if project is not None:
        project.setdefault("hwUsage", {})
    return project


def queryProject(db, project_id):
    return withUsageDefaults(db.projects.find_one({"projectId": project_id}, NO_ID))


def createProject(db, project_name, project_id, description, owner_id):
    project = {
        "projectId": project_id,
        "name": project_name,
        "description": description,
        "ownerId": owner_id,
        "members": [owner_id],
        "hwUsage": {},
    }
    try:
        db.projects.insert_one(project)
    except DuplicateKeyError:
        return None
    db.users.update_one({"userId": owner_id}, {"$addToSet": {"projects": project_id}})
    return queryProject(db, project_id)


def _check_request(db, project_id, hw_name, user_id):
    """Shared validation for check-out and check-in. Returns the project."""
    project = queryProject(db, project_id)
    if project is None:
        raise HardwareRequestError("not_found", "project does not exist")
    if user_id not in project["members"]:
        raise HardwareRequestError("forbidden", "only project members can manage its hardware")
    if hardwareDatabase.queryHardwareSet(db, hw_name) is None:
        raise HardwareRequestError("not_found", "hardware set does not exist")
    return project


def _result(db, project_id, hw_name, quantity, message):
    return {
        "message": message,
        "quantity": quantity,
        "hardware": hardwareDatabase.queryHardwareSet(db, hw_name),
        "projectUsage": queryProject(db, project_id)["hwUsage"].get(hw_name, 0),
    }


def checkOutHW(db, project_id, hw_name, quantity, user_id):
    """Check out up to `quantity` units for a project.

    If fewer are available, the project gets what is left and the message
    says so. If none are available, nothing changes.
    """
    _check_request(db, project_id, hw_name, user_id)
    granted = hardwareDatabase.requestSpace(db, hw_name, quantity)
    if granted == 0:
        raise HardwareRequestError("conflict", f"no units of {hw_name} are available")
    # The hardware set's name was validated when it was created, so it is
    # safe to use as a field name here.
    db.projects.update_one({"projectId": project_id}, {"$inc": {f"hwUsage.{hw_name}": granted}})
    if granted < quantity:
        message = f"only {granted} of {quantity} requested units were available; checked out {granted}"
    else:
        message = f"checked out {granted} units of {hw_name}"
    return _result(db, project_id, hw_name, granted, message)


def checkInHW(db, project_id, hw_name, quantity, user_id):
    """Return `quantity` units from a project. The project must hold at least that many."""
    project = _check_request(db, project_id, hw_name, user_id)
    field = f"hwUsage.{hw_name}"
    # Taking the units away from the project first, with a condition that it
    # still holds enough, means a project can never return units it doesn't have.
    result = db.projects.update_one(
        {"projectId": project_id, field: {"$gte": quantity}},
        {"$inc": {field: -quantity}},
    )
    if not result.modified_count:
        held = queryProject(db, project_id)["hwUsage"].get(hw_name, 0)
        raise HardwareRequestError(
            "conflict", f"project only has {held} units of {hw_name} checked out"
        )
    hardwareDatabase.returnSpace(db, hw_name, quantity)
    return _result(db, project_id, hw_name, quantity, f"checked in {quantity} units of {hw_name}")
