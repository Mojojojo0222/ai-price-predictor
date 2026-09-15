"""Regression tests for auth user normalization.

supabase-auth >= 2.x returns pydantic ``User`` models rather than plain dicts.
The app stores users in session state and accesses them via ``.get()`` and ``[]``,
so the user object must be normalized to a dict at the auth boundary.
"""

import types

from auth import _user_to_dict


class PydanticStyleUser:
    """Mimic the supabase-auth pydantic User model surface."""

    def __init__(self):
        self.id = "uuid-123"
        self.email = "test@example.com"
        self.user_metadata = {"full_name": "Test User"}

    def model_dump(self):
        return {
            "id": self.id,
            "email": self.email,
            "user_metadata": self.user_metadata,
        }


def test_user_to_dict_with_pydantic_style_model():
    user = _user_to_dict(PydanticStyleUser())
    assert isinstance(user, dict)
    assert user["id"] == "uuid-123"
    assert user.get("email") == "test@example.com"


def test_user_to_dict_passthrough_for_plain_dict():
    original = {"id": "x", "email": "a@b.com"}
    assert _user_to_dict(original) == original


def test_user_to_dict_fallback_for_plain_object():
    obj = types.SimpleNamespace(id="z", email="z@z.com", user_metadata={})
    user = _user_to_dict(obj)
    assert isinstance(user, dict)
    assert user["id"] == "z"
    assert user.get("email") == "z@z.com"


def test_user_to_dict_none():
    assert _user_to_dict(None) is None
