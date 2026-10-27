
from flask import Flask, render_template, jsonify
from urllib.request import urlopen
import json

app = Flask(__name__)

API_URL = "https://api.frankfurter.dev/v1/latest?from=EUR"


@app.get("/")
def consignes():
    return render_template("consignes.html")


@app.get("/dashboard")
def dashboard():
    try:
        with urlopen(API_URL, timeout=15) as response:
            donnees = json.loads(response.read().decode("utf-8"))

        return render_template(
            "dashboard.html",
            donnees=donnees,
            erreur=None
        )

    except Exception as e:
        return render_template(
            "dashboard.html",
            donnees=None,
            erreur=str(e)
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
