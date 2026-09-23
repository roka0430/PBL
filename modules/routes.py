import os

from dotenv import load_dotenv
from werkzeug.security import check_password_hash
from flask import Flask, render_template, request, redirect, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    current_user,
    login_required,
)


class User(UserMixin):
    def __init__(self, user_id: str, role: str):
        self.id = user_id
        self.role = role


load_dotenv()
SECRET_KEY = os.environ["SECRET_KEY"]
ADMIN_PASSWORD_HASH = os.environ["ADMIN_PASSWORD_HASH"]
VIEWER_PASSWORD_HASH = os.environ["VIEWER_PASSWORD_HASH"]

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.secret_key = SECRET_KEY

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_get"


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    if user_id == "admin":
        return User("admin", "admin")

    if user_id == "viewer":
        return User("viewer", "viewer")

    return None


@app.get("/login")
def login_get():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    return render_template("login.html")


@app.post("/login")
def login_post():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    role = request.form["role"]
    password = request.form["password"]

    if role == "admin":
        if check_password_hash(ADMIN_PASSWORD_HASH, password):
            login_user(User("admin", "admin"))
            return redirect(url_for("home"))

    elif role == "viewer":
        if check_password_hash(VIEWER_PASSWORD_HASH, password):
            login_user(User("viewer", "viewer"))
            return redirect(url_for("home"))

    return render_template("login.html", error="パスワードが正しくありません")


@app.post("/logout")
def logout():
    logout_user()
    return redirect(url_for("login_get"))


@app.get("/admin")
@login_required
def admin():
    return render_template("admin.html")


@app.get("/")
@login_required
def home():
    return render_template("index.html")


def run_server():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
