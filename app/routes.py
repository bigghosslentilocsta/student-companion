from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from bson.objectid import ObjectId
from app import db
from .models import User
import datetime
import markdown
from .ai_utils import generate_task_summary, get_ai_chat_response

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return redirect(url_for('main.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('username')
        password = request.form.get('password')
        mode = request.form.get('mode')  # 'user' or 'admin'

        print("Login mode:", mode)
        print("Entered email:", email)
        print("Admin email from config:", current_app.config['ADMIN_EMAIL'])

        users_collection = db.users
        user_doc = users_collection.find_one({'email': email})

        if user_doc and check_password_hash(user_doc['password'], password):
            user_obj = User(user_doc)
            login_user(user_obj)

            # Redirect based on mode and admin email match
            if mode == 'admin':
                if user_doc.get('email') == current_app.config['ADMIN_EMAIL']:
                    print("Redirecting to admin dashboard")
                    return redirect(url_for('main.admin_dashboard'))
                else:
                    flash('Access denied: Not an admin email.')
                    return redirect(url_for('main.login'))

            print("Redirecting to user dashboard")
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
        db.users.insert_one({
            "fullname": fullname,
            "email": email,
            "password": hashed_password
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
    tasks = list(db.tasks.find({'user_id': ObjectId(current_user.id)}).sort('priority.order', 1))
    notes = db.notes.find({'user_id': ObjectId(current_user.id)}).sort('timestamp', -1).limit(3)
    ai_summary = generate_task_summary(tasks)
    return render_template('user/dashboard.html', tasks=tasks, notes=notes, ai_summary=ai_summary)

@bp.route('/notes')
@login_required
def notes():
    user_notes = db.notes.find({'user_id': ObjectId(current_user.id)}).sort('timestamp', -1)
    return render_template('user/notes.html', notes=user_notes)

@bp.route('/add_note', methods=['POST'])
@login_required
def add_note():
    title = request.form.get('note_title')
    content = request.form.get('note_content')
    file_url = request.form.get('file_url')
    if title and content:
        db.notes.insert_one({
            'user_id': ObjectId(current_user.id),
            'title': title,
            'content': content,
            'timestamp': datetime.datetime.now(datetime.timezone.utc),
            'file_url': file_url or None
        })
    return redirect(url_for('main.notes'))

@bp.route('/delete_note/<note_id>')
@login_required
def delete_note(note_id):
    db.notes.delete_one({'_id': ObjectId(note_id), 'user_id': ObjectId(current_user.id)})
    return redirect(url_for('main.notes'))

@bp.route('/add_task', methods=['POST'])
@login_required
def add_task():
    content = request.form.get('task_content')
    priority = request.form.get('priority', 'Medium')
    priority_map = {"High": 1, "Medium": 2, "Low": 3}
    if content:
        db.tasks.insert_one({
            'user_id': ObjectId(current_user.id),
            'content': content,
            'completed': False,
            'priority': {
                'level': priority,
                'order': priority_map.get(priority, 2)
            }
        })
    return redirect(url_for('main.dashboard'))

@bp.route('/complete_task/<task_id>')
@login_required
def complete_task(task_id):
    db.tasks.update_one(
        {'_id': ObjectId(task_id), 'user_id': ObjectId(current_user.id)},
        {'$set': {'completed': True}}
    )
    return redirect(url_for('main.dashboard'))

@bp.route('/delete_task/<task_id>')
@login_required
def delete_task(task_id):
    db.tasks.delete_one({'_id': ObjectId(task_id), 'user_id': ObjectId(current_user.id)})
    return redirect(url_for('main.dashboard'))

@bp.route('/diary')
@login_required
def diary():
    entries = db.diary_entries.find({'user_id': ObjectId(current_user.id)}).sort('timestamp', -1)
    today = datetime.datetime.now(datetime.timezone.utc).strftime('%B %d, %Y')
    return render_template('user/diary.html', entries=entries, today=today)

@bp.route('/add_diary_entry', methods=['POST'])
@login_required
def add_diary_entry():
    content = request.form.get('diary_content')
    if content:
        formatted = markdown.markdown(content)
        db.diary_entries.insert_one({
            'user_id': ObjectId(current_user.id),
            'content': formatted,
            'timestamp': datetime.datetime.now(datetime.timezone.utc)
        })
    return redirect(url_for('main.diary'))

@bp.route('/delete_diary_entry/<entry_id>')
@login_required
def delete_diary_entry(entry_id):
    db.diary_entries.delete_one({'_id': ObjectId(entry_id), 'user_id': ObjectId(current_user.id)})
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
    notes = list(db.notes.find({'user_id': ObjectId(current_user.id)}))
    tasks = list(db.tasks.find({'user_id': ObjectId(current_user.id), 'completed': False}))
    diary_entries = list(db.diary_entries.find({'user_id': ObjectId(current_user.id)}).sort('timestamp', -1).limit(7))
    response = get_ai_chat_response(question, notes, tasks, diary_entries)
    return jsonify({'response': response})

@bp.route('/admin')
@login_required
def admin_dashboard():
    if current_user.email != current_app.config['ADMIN_EMAIL']:
        abort(403)
    stats = {
        'total_users': 5,
        'total_tasks': 85,
        'total_notes': 20,
        'total_diary_entries': 15,
        'storage_used': '0.3 GB',
        'storage_limit': '10 GB',
        'system_status': 'All services operational'
    }
    return render_template('admin/dashboard.html', stats=stats)