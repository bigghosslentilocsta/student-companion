from pymongo import MongoClient
from werkzeug.security import generate_password_hash

# Replace with your actual MongoDB URI
MONGO_URI = "mongodb+srv://student_app_user:tJ7GpbYVuS1SQvmu@studentcompanioncluster.xsd2riq.mongodb.net/?retryWrites=true&w=majority&appName=StudentCompanionCluster"
client = MongoClient(MONGO_URI)

# Connect to your database
db = client.get_database("student_companion_db")

# Create admin credentials
admin_email = "admin@gmail.com"
admin_password = generate_password_hash("admin")

# Insert admin user
db.users.insert_one({
    "fullname": "Admin",
    "email": admin_email,
    "password": admin_password
})

print("✅ Admin user created successfully!")