import secrets
from getpass import getpass
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

secret_key = secrets.token_hex(32)
admin_password_hash = generate_password_hash(admin_password)
viewer_password_hash = generate_password_hash(viewer_password)

print("")
print("\033[31mSECRET_KEY=\033[0m" + secret_key)
print("\033[31mADMIN_PASSWORD_HASH=\033[0m" + admin_password_hash)
print("\033[31mVIEWER_PASSWORD_HASH=\033[0m" + viewer_password_hash)
