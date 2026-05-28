import os
from datetime import timedelta

from flask import Flask
from flask_jwt_extended import JWTManager

from auth import auth_bp
from database import init_db
from tasks import tasks_bp

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

JWTManager(app)

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(tasks_bp, url_prefix='/tasks')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
