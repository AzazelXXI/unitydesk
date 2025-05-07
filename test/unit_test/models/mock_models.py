# File: d:\projects\CSA\csa-hello\test\unit_test\user\mock_models.py
"""Mock models for testing without SQLAlchemy relationships complexity"""


class MockUser:
    """Mock User model for testing"""

    def __init__(self, username, email, password, is_active=True, is_verified=False):
        # Validate required fields
        if username is None:
            raise ValueError("Username cannot be None")
        if email is None:
            raise ValueError("Email cannot be None")
        if password is None:
            raise ValueError("Password cannot be None")

        # Validate email format
        if "@" not in email or "." not in email:
            raise ValueError("Invalid email format")

        self.id = None  # would be set by DB
        self.username = username
        self.email = email
        self.password = password  # In real model this would be hashed
        self.is_active = is_active
        self.is_verified = is_verified
        self.created_at = None  # would be set by DB
        self.updated_at = None  # would be set by DB

    def __str__(self):
        return f"User: {self.username} ({self.email})"


class MockUserProfile:
    """Mock UserProfile model for testing"""

    def __init__(self, user, first_name=None, last_name=None, bio=None):
        # Validate required fields
        if user is None:
            raise ValueError("User cannot be None")

        self.id = None  # would be set by DB
        self.user = user
        self.user_id = user.id if user else None
        self.first_name = first_name
        self.last_name = last_name
        self.bio = bio
        self.created_at = None  # would be set by DB
        self.updated_at = None  # would be set by DB

    def __str__(self):
        return f"Profile: {self.first_name} {self.last_name}"
