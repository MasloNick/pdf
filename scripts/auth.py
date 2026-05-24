"""User authentication module for CourtNinja CRM.

Session-based auth with JSON persistence. Roles: advocate, assistant, client.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Dict, Optional

from flask import flash, redirect, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

ROLES = {
    "advocate": "Адвокат",
    "assistant": "Помічник",
    "client": "Клієнт",
}


@dataclass
class User:
    id: str
    username: str
    email: str
    password_hash: str
    role: str
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class UserManager:
    def __init__(self, data_file: Optional[str] = None) -> None:
        self._data_file = data_file or str(DATA_DIR / "users.json")
        self._users: Dict[str, User] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._data_file):
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    user = User(**item)
                    self._users[user.id] = user
            except (json.JSONDecodeError, TypeError, KeyError):
                self._users = {}

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self._data_file), exist_ok=True)
        with open(self._data_file, "w", encoding="utf-8") as f:
            json.dump(
                [u.to_dict() for u in self._users.values()],
                f,
                ensure_ascii=False,
                indent=2,
            )

    def register(self, username: str, email: str, password: str, role: str = "advocate") -> Optional[User]:
        for u in self._users.values():
            if u.email == email:
                return None
        user = User(
            id=str(uuid.uuid4())[:8],
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=role if role in ROLES else "advocate",
            created_at=datetime.now().isoformat(),
        )
        self._users[user.id] = user
        self._save()
        return user

    def authenticate(self, email: str, password: str) -> Optional[User]:
        for u in self._users.values():
            if u.email == email and check_password_hash(u.password_hash, password):
                return u
        return None

    def get_user(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        for u in self._users.values():
            if u.email == email:
                return u
        return None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Будь ласка, увійдіть до системи", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                flash("Будь ласка, увійдіть до системи", "warning")
                return redirect(url_for("login"))
            if session.get("user_role") not in roles:
                flash("Недостатньо прав для цієї дії", "danger")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return decorated
    return decorator
