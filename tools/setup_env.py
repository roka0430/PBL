import secrets
from getpass import getpass
from pathlib import Path
from werkzeug.security import generate_password_hash

while True:
    print("<Admin>")
    admin_password = getpass("Input password: ")
    confirm = getpass("Confirm password: ")

    if admin_password == confirm:
        break

    print("\033[31mPasswords do not match. Try again.\033[0m\n")

print("")

while True:
    print("<Viewer>")
    viewer_password = getpass("Input password: ")
    confirm = getpass("Confirm password: ")

    if viewer_password == confirm:
        break

    print("\033[31mPasswords do not match. Try again.\033[0m\n")

print("")

secret_key = secrets.token_hex(32)
admin_password_hash = generate_password_hash(admin_password)
viewer_password_hash = generate_password_hash(viewer_password)

env_content = f"""SECRET_KEY={secret_key}
ADMIN_PASSWORD_HASH={admin_password_hash}
VIEWER_PASSWORD_HASH={viewer_password_hash}
"""

env_path = Path(".env")

if env_path.exists():
    answer = input(".env already exists. Overwrite? [y/N]: ")

    if answer.lower() == "y":
        env_path.write_text(env_content, encoding="utf-8")
        print(".env overwritten successfully.")
    else:
        print(".env was not changed.")
else:
    env_path.write_text(env_content, encoding="utf-8")
    print(".env generated successfully.")
