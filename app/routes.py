from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_user, logout_user, login_required, current_user
from bson.objectid import ObjectId
from app import db
from .models import User
import datetime
import markdown
import os
# We no longer need cloudinary
from .ai_utils import generate_task_summary, get_ai_chat_response

bp = Blueprint('main', __name__)

# --- AUTHENTICATION, DASHBOARD, AND OTHER ROUTES ---
# ... (No changes in these sections)
@bp.route('/')
def index():
    return redirect(url_for('main.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('username')
        password = request.form.get('password')
        users_collection = db.users
        user_doc = users_collection.find_one({'email': email})
        if user_doc and check_password_hash(user_doc['password'], password):
            user_obj = User(user_doc)
            login_user(user_obj)
            if user_doc.get('email') == os.getenv('ADMIN_EMAIL'):
                return redirect(url_for('main.admin_dashboard'))
            return redirect(url_for('main.dashboard'))
        flash('Invalid email or password. Please try again.')
        return redirect(url_for('main.login'))
    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)
        users_collection = db.users
        users_collection.insert_one({
            "fullname": fullname, "email": email, "password": hashed_password
        })
        flash('Registration successful! Please log in.')
        return redirect(url_for('main.login'))
    return render_template('register.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@bp.route('/dashboard')
@login_required
def dashboard():
    tasks_collection = db.tasks
    user_tasks_cursor = tasks_collection.find(
        {'user_id': ObjectId(current_user.id)}
    ).sort('priority.order', 1)
    user_tasks_list = list(user_tasks_cursor)
    notes_collection = db.notes
    recent_notes = notes_collection.find(
        {'user_id': ObjectId(current_user.id)}
    ).sort('timestamp', -1).limit(3)
    ai_summary = generate_task_summary(user_tasks_list)
    return render_template('user/dashboard.html', tasks=user_tasks_list, notes=recent_notes, ai_summary=ai_summary)

# --- NOTE ROUTES (SIMPLIFIED LOGIC) ---
@bp.route('/notes')
@login_required
def notes():
    notes_collection = db.notes
    user_notes = notes_collection.find(
        {'user_id': ObjectId(current_user.id)}
    ).sort('timestamp', -1)
    return render_template('user/notes.html', notes=user_notes)

@bp.route('/add_note', methods=['POST'])
@login_required
def add_note():
    note_title = request.form.get('note_title')
    note_content = request.form.get('note_content')
    # Get the link from the form instead of a file
    file_url = request.form.get('file_url')

    if note_title and note_content:
        notes_collection = db.notes
        notes_collection.insert_one({
            'user_id': ObjectId(current_user.id),
            'title': note_title,
            'content': note_content,
            'timestamp': datetime.datetime.now(datetime.timezone.utc),
            'file_url': file_url if file_url else None # Save the link if it exists
        })
    return redirect(url_for('main.notes'))

@bp.route('/delete_note/<note_id>')
@login_required
def delete_note(note_id):
    # No need to delete from Cloudinary anymore, just from the database
    notes_collection = db.notes
    notes_collection.delete_one(
        {'_id': ObjectId(note_id), 'user_id': ObjectId(current_user.id)}
    )
    return redirect(url_for('main.notes'))

# --- OTHER ROUTES ---
# ... (all other routes for Tasks, Diary, AI, Admin remain the same)
@bp.route('/add_task', methods=['POST'])
@login_required
def add_task():
    task_content = request.form.get('task_content')
    priority_level = request.form.get('priority', 'Medium')
    priority_map = {"High": 1, "Medium": 2, "Low": 3}
    if task_content:
        tasks_collection = db.tasks
        tasks_collection.insert_one({
            'user_id': ObjectId(current_user.id), 'content': task_content,
            'completed': False, 'priority': {
                'level': priority_level, 'order': priority_map.get(priority_level, 2)
            }
        })
    return redirect(url_for('main.dashboard'))

@bp.route('/complete_task/<task_id>')
@login_required
def complete_task(task_id):
    tasks_collection = db.tasks
    tasks_collection.update_one(
        {'_id': ObjectId(task_id), 'user_id': ObjectId(current_user.id)},
        {'$set': {'completed': True}}
    )
    return redirect(url_for('main.dashboard'))

@bp.route('/delete_task/<task_id>')
@login_required
def delete_task(task_id):
    tasks_collection = db.tasks
    tasks_collection.delete_one(
        {'_id': ObjectId(task_id), 'user_id': ObjectId(current_user.id)}
    )
    return redirect(url_for('main.dashboard'))

@bp.route('/diary')
@login_required
def diary():
    diary_collection = db.diary_entries
    user_entries = diary_collection.find(
        {'user_id': ObjectId(current_user.id)}
    ).sort('timestamp', -1)
    today_date = datetime.datetime.now(datetime.timezone.utc).strftime('%B %d, %Y')
    return render_template('user/diary.html', entries=user_entries, today=today_date)

@bp.route('/add_diary_entry', methods=['POST'])
@login_required
def add_diary_entry():
    content = request.form.get('diary_content')
    if content:
        formatted_content = markdown.markdown(content)
        diary_collection = db.diary_entries
        diary_collection.insert_one({
            'user_id': ObjectId(current_user.id),
            'content': formatted_content,
            'timestamp': datetime.datetime.now(datetime.timezone.utc)
        })
    return redirect(url_for('main.diary'))

@bp.route('/delete_diary_entry/<entry_id>')
@login_required
def delete_diary_entry(entry_id):
    diary_collection = db.diary_entries
    diary_collection.delete_one(
        {'_id': ObjectId(entry_id), 'user_id': ObjectId(current_user.id)}
    )
    return redirect(url_for('main.diary'))

@bp.route('/ai_companion')
@login_required
def ai_companion():
    return render_template('user/ai_companion.html')

@bp.route('/ask_ai', methods=['POST'])
@login_required
def ask_ai():
    data = request.get_json()
    question = data.get('message')
    if not question:
        return jsonify({'response': 'Sorry, I did not receive a question.'}), 400
    notes_collection = db.notes
    user_notes = list(notes_collection.find({'user_id': ObjectId(current_user.id)}))
    tasks_collection = db.tasks
    user_tasks = list(tasks_collection.find({'user_id': ObjectId(current_user.id), 'completed': False}))
    diary_collection = db.diary_entries
    user_diary_entries = list(diary_collection.find({'user_id': ObjectId(current_user.id)}).sort('timestamp', -1).limit(7))
    ai_response = get_ai_chat_response(question, user_notes, user_tasks, user_diary_entries)
    return jsonify({'response': ai_response})

@bp.route('/admin')
@login_required
def admin_dashboard():
    if current_user.email != os.getenv('ADMIN_EMAIL'):
        abort(403)
    stats = {
        'total_users': db.users.count_documents({}),
        'total_tasks': db.tasks.count_documents({}),
        'total_notes': db.notes.count_documents({}),
        'total_diary_entries': db.diary_entries.count_documents({})
    }
    return render_template('admin/dashboard.html', stats=stats)