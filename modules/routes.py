from flask import Flask, render_template, jsonify

app = Flask(__name__, template_folder="../templates")


@app.route("/")
def home():
    return render_template("index.html")


def run_server():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
