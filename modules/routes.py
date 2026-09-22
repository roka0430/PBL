from flask import Flask, render_template, request, redirect, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    current_user,
    login_required,
)
from werkzeug.security import check_password_hash


class Admin(UserMixin):
    id = "admin"


app = Flask(__name__, template_folder="../templates")
app.secret_key = "secret_key"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_get"


@login_manager.user_loader
def load_user(user_id) -> Admin | None:
    if user_id == "admin":
        return Admin()
    return None


@app.get("/login")
def login_get():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    return render_template("login.html")


@app.post("/login")
def login_post():
    if current_user.is_authenticated:
        return redirect(url_for("routes.home"))

    password = request.form["password"]

    if check_password_hash("password_hash", password):
        login_user(Admin())
        return redirect(url_for("routes.home"))

    return render_template("login.html", error="パスワードが正しくありません")


@app.get("/")
@login_required
def home():
    return render_template("index.html")


def run_server():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
