import os
from flask import Flask
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask_login import LoginManager
import cloudinary # Import cloudinary

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client.get_database('student_companion_db')

login_manager = LoginManager()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_default_secret_key_for_development')
    app.config['ADMIN_EMAIL'] = os.getenv('ADMIN_EMAIL')


    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        users_collection = db.users
        user_doc = users_collection.find_one({'_id': ObjectId(user_id)})
        if user_doc:
            return User(user_doc)
        return None

    try:
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB Atlas. Error: {e}")

    from . import routes
    app.register_blueprint(routes.bp)

    return app