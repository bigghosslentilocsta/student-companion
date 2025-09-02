from flask_login import UserMixin
from app import db

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.email = user_data['email']
        self.fullname = user_data['fullname']
        self.password_hash = user_data['password']

    @staticmethod
    def get(user_id):
        users_collection = db.users
        user_data = users_collection.find_one({'_id': user_id})
        if user_data:
            return User(user_data)
        return None