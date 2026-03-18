"""Authentication configuration"""

# Allowed users list
ALLOWED_USERS = [
    "ayush.mittal@artesian.io"
]

# OAuth scopes
OAUTH_SCOPES = ["User.Read"]

# Default redirect URI (for local dev)
DEFAULT_REDIRECT_URI = "http://localhost:8501/oauth2callback"

