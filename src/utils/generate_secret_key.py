"""
Script to generate a secure random key for JWT token signing.
"""

import secrets
import os
import base64


def generate_secure_key(bytes_length=32):
    """Generate a secure random key with the specified byte length"""
    return base64.urlsafe_b64encode(secrets.token_bytes(bytes_length)).decode("utf-8")


def update_env_file(env_file_path=".env"):
    """Update or create the .env file with a new JWT secret key"""
    # Generate a secure key (32 bytes = 256 bits)
    new_secret_key = generate_secure_key(32)

    # Check if .env file exists
    env_exists = os.path.exists(env_file_path)

    # Read existing content if file exists
    existing_content = ""
    if env_exists:
        with open(env_file_path, "r") as f:
            existing_content = f.read()

    # Check if JWT_SECRET_KEY already exists in the file
    if "JWT_SECRET_KEY=" in existing_content:
        # Replace existing key
        lines = existing_content.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("JWT_SECRET_KEY="):
                lines[i] = f"JWT_SECRET_KEY={new_secret_key}"
                break

        # Write updated content back to file
        with open(env_file_path, "w") as f:
            f.write("\n".join(lines))
    else:
        # Append new key to file
        with open(env_file_path, "a") as f:
            if existing_content and not existing_content.endswith("\n"):
                f.write("\n")
            f.write(f"JWT_SECRET_KEY={new_secret_key}\n")

    print(f"JWT_SECRET_KEY updated in {env_file_path}")
    return new_secret_key


if __name__ == "__main__":
    # Get the project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "../.."))
    env_path = os.path.join(project_root, ".env")

    # Update the .env file with a new secret key
    key = update_env_file(env_path)
    print(f"Generated new JWT_SECRET_KEY: {key}")
