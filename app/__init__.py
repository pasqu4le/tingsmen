import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
# take configuration keys from environment variables:
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
# database:
db = SQLAlchemy(app)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# imported at the end because of dependencies
from app import database, forms, views
