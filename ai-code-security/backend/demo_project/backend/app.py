"""FairShare — expense sharing application entry point."""

from flask import Flask, jsonify, request

from backend.api import auth_api, expenses_api, health_api, users_api
from backend.middleware import request_logger

app = Flask(__name__)
app.register_blueprint(health_api.bp)
app.register_blueprint(auth_api.bp)
app.register_blueprint(users_api.bp)
app.register_blueprint(expenses_api.bp)
app.before_request(request_logger)


@app.route("/api/calculate", methods=["POST"])
def calculate():
    """Evaluate a client-provided arithmetic expression."""
    payload = request.get_json(silent=True) or {}
    user_expression = payload.get("expression", "0")
    result = eval(user_expression)
    return jsonify({"result": result})


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "not found"}), 404


if __name__ == "__main__":
    app.run(debug=True)
