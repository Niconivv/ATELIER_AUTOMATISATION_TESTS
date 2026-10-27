
from flask import Flask, render_template
from urllib.request import urlopen
from urllib.error import HTTPError
import json
import time

app = Flask(__name__)

API_URL = "https://api.frankfurter.dev/v1"


def appeler_api(url):
    debut = time.perf_counter()

    try:
        with urlopen(url, timeout=15) as response:
            statut = response.status
            contenu = response.read().decode("utf-8")

    except HTTPError as erreur:
        statut = erreur.code
        contenu = erreur.read().decode("utf-8", errors="replace")

    duree = round((time.perf_counter() - debut) * 1000)

    try:
        donnees = json.loads(contenu)
    except (json.JSONDecodeError, ValueError):
        donnees = {}

    return statut, donnees, duree


def executer_test(nom, url, verification):
    try:
        statut, donnees, duree = appeler_api(url)
        succes, message = verification(statut, donnees, duree)

        return {
            "nom": nom,
            "succes": succes,
            "statut": statut,
            "temps_ms": duree,
            "message": message
        }

    except Exception as erreur:
        return {
            "nom": nom,
            "succes": False,
            "statut": None,
            "temps_ms": None,
            "message": str(erreur)
        }


def verifier_eur(statut, donnees, duree):
    rates = donnees.get("rates", {})

    valide = (
        statut == 200
        and donnees.get("base") == "EUR"
        and bool(donnees.get("date"))
        and isinstance(rates, dict)
        and bool(rates)
        and all(
            isinstance(taux, (int, float))
            and not isinstance(taux, bool)
            and taux > 0
            for taux in rates.values()
        )
    )

    return valide, (
        f"{len(rates)} devises reçues avec des taux valides"
        if valide else "Réponse ou taux invalides"
    )


def verifier_usd(statut, donnees, duree):
    rates = donnees.get("rates", {})

    valide = (
        statut == 200
        and donnees.get("base") == "USD"
        and "EUR" in rates
        and "GBP" in rates
    )

    return valide, (
        "Taux USD vers EUR et GBP présents"
        if valide else "Taux attendus absents ou réponse invalide"
    )


def verifier_historique(statut, donnees, duree):
    valide = (
        statut == 200
        and donnees.get("base") == "EUR"
        and donnees.get("date") == "2020-01-02"
        and "USD" in donnees.get("rates", {})
    )

    return valide, (
        "Taux historiques reçus pour le 02/01/2020"
        if valide else "Réponse historique invalide"
    )

def verifier_devise_invalide(statut, donnees, duree):
    valide = statut >= 400

    return valide, (
        "L'API refuse correctement la devise inconnue"
        if valide else f"L'API a renvoyé HTTP {statut} au lieu d'une erreur"
    )


def verifier_performance(statut, donnees, duree):
    valide = (
        statut == 200
        and donnees.get("base") == "EUR"
        and duree < 3000
    )

    return valide, (
        "Réponse reçue en moins de 3000 ms"
        if valide else f"Réponse trop lente ou invalide ({duree} ms)"
    )


def lancer_tests():
    return [
        executer_test(
            "Taux EUR et validité des données",
            f"{API_URL}/latest?from=EUR",
            verifier_eur
        ),
        executer_test(
            "Taux USD vers EUR et GBP",
            f"{API_URL}/latest?from=USD&to=EUR,GBP",
            verifier_usd
        ),
        executer_test(
            "Taux historiques",
            f"{API_URL}/2020-01-02?from=EUR&to=USD",
            verifier_historique
        ),
        executer_test(
            "Gestion d'une devise inconnue",
            f"{API_URL}/latest?from=XXX",
            verifier_devise_invalide
        ),
        executer_test(
            "Performance de l'API",
            f"{API_URL}/latest?from=EUR",
            verifier_performance
        )
    ]


@app.get("/")
def consignes():
    return render_template("consignes.html")


@app.get("/dashboard")
def dashboard():
    donnees = None
    erreur = None
    tests = []

    try:
        statut, donnees, duree = appeler_api(
            f"{API_URL}/latest?from=EUR"
        )

        if statut != 200:
            erreur = f"L'API a répondu avec le statut HTTP {statut}"
            donnees = None
        elif (
            not isinstance(donnees.get("rates"), dict)
            or not donnees["rates"]
        ):
            erreur = "La réponse de l'API est invalide"
            donnees = None

    except Exception as e:
        erreur = str(e)

    tests = lancer_tests()

    return render_template(
        "dashboard.html",
        donnees=donnees,
        erreur=erreur,
        tests=tests
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
