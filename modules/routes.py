from flask import Flask, render_template, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required

app = Flask(__name__, template_folder="../templates")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/")
def home():
    return render_template("index.html")


def run_server():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
