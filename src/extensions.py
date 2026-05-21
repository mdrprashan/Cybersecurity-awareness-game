"""
extensions.py — Shared Flask extension instances
ICT932 – Cybersecurity Testing and Assurance

Centralises db, login_manager, and bcrypt here so every other
module can import from this file without causing circular imports.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

db            = SQLAlchemy()
login_manager = LoginManager()
bcrypt        = Bcrypt()
