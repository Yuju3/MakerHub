"""One-time import of the old database.json test data into MongoDB Atlas.

Run from the server folder:  python3 seed.py
Safe to run more than once: existing records are left alone.
"""

import json
from pathlib import Path

from db import get_db

SEED_FILE = Path(__file__).with_name("database.json")


def main():
    db = get_db()
    data = json.loads(SEED_FILE.read_text())
    for user in data.get("users", []):
        result = db.users.update_one({"userId": user["userId"]}, {"$setOnInsert": user}, upsert=True)
        print(("added user " if result.upserted_id else "kept user  ") + user["userId"])
    for project in data.get("projects", []):
        result = db.projects.update_one(
            {"projectId": project["projectId"]}, {"$setOnInsert": project}, upsert=True
        )
        print(("added project " if result.upserted_id else "kept project  ") + project["projectId"])


if __name__ == "__main__":
    main()
