from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from config import SECRET_KEY
from db import init_db
from auth import auth
import models

app = Flask(__name__)
app.secret_key = SECRET_KEY

app.register_blueprint(auth)

# --- Theme System ---

THEMES = {
    'glass': {'name': 'Glass',  'css': 'css/themes/glass.css',  'preview': 'glass-preview',  'desc': 'Glassmorphism & animated blobs'},
    'neon':  {'name': 'Neon',   'css': 'css/themes/neon.css',   'preview': 'neon-preview',   'desc': 'Cyberpunk with scanlines'},
    'space': {'name': 'Space',  'css': 'css/themes/space.css',  'preview': 'space-preview',  'desc': '3D floating cards in deep space'},
    'paper': {'name': 'Paper',  'css': 'css/themes/paper.css',  'preview': 'paper-preview',  'desc': 'Editorial brutalist ink style'},
}

@app.context_processor
def inject_theme():
    name = session.get('theme', 'glass')
    if name not in THEMES:
        name = 'glass'
    return {'theme': THEMES[name], 'theme_name': name, 'all_themes': THEMES}

@app.route('/theme/<name>', methods=['POST'])
def set_theme(name):
    if name in THEMES:
        session['theme'] = name
    return redirect(request.referrer or url_for('dashboard'))


# --- Decorators ---

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


# --- Main Routes ---

@app.route('/themes')
@login_required
def theme_select():
    return render_template('theme_select.html')

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))


@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    appointments = models.get_all_appointments(user_id)
    stats = models.get_dashboard_stats(user_id)
    return render_template('dashboard.html', appointments=appointments, stats=stats)


@app.route('/appointments/new', methods=['GET', 'POST'])
@login_required
def new_appointment():
    if request.method == 'POST':
        models.create_appointment(request.form, session['user_id'])
        flash('Appointment created.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('appointment_form.html', appointment=None)


@app.route('/appointments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_appointment(id):
    appointment = models.get_appointment(id, session['user_id'])
    if not appointment:
        flash('Appointment not found.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        models.update_appointment(id, request.form, session['user_id'])
        flash('Appointment updated.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('appointment_form.html', appointment=appointment)


@app.route('/appointments/<int:id>/status', methods=['POST'])
@login_required
def update_status(id):
    status = request.form.get('status')
    if status in ('planned', 'done', 'canceled'):
        models.update_status(id, status, session['user_id'])
    return redirect(url_for('dashboard'))


@app.route('/appointments/<int:id>/delete', methods=['POST'])
@login_required
def delete_appointment(id):
    models.delete_appointment(id, session['user_id'])
    flash('Appointment deleted.', 'success')
    return redirect(url_for('dashboard'))


# --- Admin Routes ---

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    users = models.get_all_users()
    appointments = models.get_all_appointments_admin()
    return render_template('admin.html', users=users, appointments=appointments)


@app.route('/admin/appointments/<int:id>/status', methods=['POST'])
@login_required
@admin_required
def admin_update_status(id):
    status = request.form.get('status')
    if status in ('planned', 'done', 'canceled'):
        models.admin_update_status(id, status)
    return redirect(url_for('admin_panel'))


@app.route('/admin/appointments/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_appointment(id):
    models.admin_delete_appointment(id)
    flash('Appointment deleted.', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/users/<int:id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(id):
    if id == session['user_id']:
        flash('You cannot change your own admin status.', 'error')
        return redirect(url_for('admin_panel'))
    result = models.toggle_admin(id)
    status = 'promoted to admin' if result['is_admin'] else 'demoted to regular user'
    flash(f'User {status}.', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/users/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    if id == session['user_id']:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin_panel'))
    models.delete_user(id)
    flash('User and their appointments deleted.', 'success')
    return redirect(url_for('admin_panel'))


# --- Run ---

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5056)
