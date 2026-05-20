from flask import Flask
from extensions import db

app = Flask(__name__)
app.config["SECRET_KEY"] = "cyberquest-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cyberquest.db"

db.init_app(app)

from src.game import game_bp
app.register_blueprint(game_bp)

if __name__ == "__main__":
    app.run(debug=True)