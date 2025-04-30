from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from routes import api, bcrypt  # import bcrypt from routes
from models import db  # import db from models.py

app = Flask(__name__)

# App Configurations
app.config['SECRET_KEY'] = 'SUPER-SECRET-KEY'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

# Initialize extensions with app
db.init_app(app)
bcrypt.init_app(app)
jwt = JWTManager(app)
api.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
