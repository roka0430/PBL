import secrets
from getpass import getpass
from werkzeug.security import generate_password_hash

while True:
    password = getpass("Admin password: ")
    confirm = getpass("Confirm password: ")

    if password == confirm:
        break

    print("Passwords do not match. Try again.")

secret_key = secrets.token_hex(32)
password_hash = generate_password_hash(password)

print("\nSECRET_KEY=" + secret_key)
print("ADMIN_PASSWORD_HASH=" + password_hash)
