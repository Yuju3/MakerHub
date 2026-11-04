"""MongoDB Atlas connection shared by the whole backend.

The connection string comes from the MONGODB_URI environment variable
(loaded from server/.env during local development), so no credentials
live in the code or the repository.
"""

import os

from dotenv import load_dotenv
from pymongo import ASCENDING, MongoClient

load_dotenv()

_client = None
_db = None


def get_db():
    """Return the app's database, connecting on first use."""
    global _client, _db
    if _db is None:
        uri = os.environ.get("MONGODB_URI")
        if not uri:
            raise RuntimeError(
                "MONGODB_URI is not set. Copy server/.env.example to server/.env "
                "and paste in your Atlas connection string."
            )
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        _db = _client[os.environ.get("MONGODB_DB", "makerhub")]
        ensure_indexes(_db)
    return _db


def ensure_indexes(db):
    """Unique indexes make the database itself reject duplicate IDs.

    create_index is idempotent, so running this on every startup is safe.
    """
    db.users.create_index([("username", ASCENDING)], unique=True)
    db.users.create_index([("userId", ASCENDING)], unique=True)
    db.projects.create_index([("projectId", ASCENDING)], unique=True)
    db.hardwareSets.create_index([("hwName", ASCENDING)], unique=True)
