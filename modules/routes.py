import os
import time
from functools import wraps

from dotenv import load_dotenv
from werkzeug.security import check_password_hash
from flask import (
    Flask,
    jsonify,
    abort,
    render_template,
    request,
    Response,
    redirect,
    url_for,
)
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    current_user,
    login_required,
)

from .enums import SystemStatus, WateringRequestResult


class User(UserMixin):
    def __init__(self, user_id: str, role: str):
        self.id = user_id
        self.role = role


PORT = 5000

# ---------- 環境変数 ----------
load_dotenv()
SECRET_KEY = os.environ["SECRET_KEY"]
ADMIN_PASSWORD_HASH = os.environ["ADMIN_PASSWORD_HASH"]
VIEWER_PASSWORD_HASH = os.environ["VIEWER_PASSWORD_HASH"]

# ---------- Flask ----------
app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.secret_key = SECRET_KEY

# ---------- Flask-Login ----------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_get"


# ==================================================
# キャッシュ制御
# ==================================================


@app.after_request
def add_no_cache(response):
    if request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=3600"
    else:
        response.headers["Cache-Control"] = "no-store"

    return response


# ==================================================
# 管理者権限
# ==================================================


def admin_required(func):
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if getattr(current_user, "role", None) != "admin":
            return redirect(url_for("home"))

        return func(*args, **kwargs)

    return wrapper


def admin_api_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)

        if getattr(current_user, "role", None) != "admin":
            abort(403)

        return func(*args, **kwargs)

    return wrapper


# ==================================================
# ログイン・ログアウト処理
# ==================================================


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    if user_id == "admin":
        return User("admin", "admin")

    if user_id == "viewer":
        return User("viewer", "viewer")

    return None


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


# ==================================================
# ページ表示
# ==================================================


@app.get("/")
@login_required
def home():
    return render_template("index.html", cache_buster=time.time())


@app.get("/login")
def login_get():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    return render_template("login.html", cache_buster=time.time())


@app.get("/admin")
@admin_required
def admin():
    return render_template("admin.html", cache_buster=time.time())


# ==================================================
# API
# ==================================================


@app.get("/api/watering-history")
@login_required
def get_watering_history():
    limit = request.args.get("limit", default=10, type=int)
    limit = max(1, min(limit, 100))

    history = [
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
        {"watering_at": "2026-10-06T05:32:10", "amount_ml": 180},
    ]

    return jsonify(
        {
            "history": history[0:limit],
            "total_count": len(history),
        }
    )


@app.get("/api/sensors")
@login_required
def get_sensor_values():
    values = app.system.get_sensor_values()
    return values.to_dict()


@app.get("/api/image")
@login_required
def get_image():
    image = app.system.get_image()

    response = Response(image.data, mimetype="image/jpeg")
    response.headers["MizuMori-Captured-At"] = image.captured_at.isoformat()

    return response


@app.post("/api/watering")
@admin_api_required
def watering():
    amount_ml = request.form["amount"]
    result, duration = app.system.request_watering(amount_ml)

    if result == WateringRequestResult.ACCEPTED:
        return jsonify({"success": True, "duration": duration}), 202

    if result == WateringRequestResult.INVALID_AMOUNT:
        return jsonify({"success": False, "error": "invalid_amount"}), 400

    if result == WateringRequestResult.TOO_SOON:
        return jsonify({"success": False, "error": "too_soon"}), 429

    if result == WateringRequestResult.NOT_IDLE:
        return jsonify({"success": False, "error": "not_idle"}), 409


# ==================================================
# 起動
# ==================================================


def run_server(system):
    app.system = system
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
