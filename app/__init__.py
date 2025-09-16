import os
from flask import Flask
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_login import LoginManager
import cloudinary
import certifi # Import the certifi library

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')

# --- THIS IS THE CORRECTED DATABASE CONNECTION ---
# We are telling MongoClient to use certifi's certificates for a secure connection
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database('student_companion_db')
# --- END OF CORRECTION ---

login_manager = LoginManager()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_default_secret_key_for_development')
    app.config['ADMIN_EMAIL'] = os.getenv('ADMIN_EMAIL')

    # Cloudinary Config
    cloudinary.config(
        cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key = os.getenv('CLOUDINARY_API_KEY'),
        api_secret = os.getenv('CLOUDINARY_API_SECRET'),
        secure = True
    )

    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    from .models import User
    from bson.objectid import ObjectId

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
