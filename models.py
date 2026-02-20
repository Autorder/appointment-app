from db import get_cursor


def get_all_appointments(user_id):
    with get_cursor() as cur:
        cur.execute("""
            SELECT * FROM appointments
            WHERE owner_id = %s
            ORDER BY date ASC, time ASC
        """, (user_id,))
        return cur.fetchall()


def get_appointment(appointment_id, user_id):
    with get_cursor() as cur:
        cur.execute("""
            SELECT * FROM appointments
            WHERE id = %s AND owner_id = %s
        """, (appointment_id, user_id))
        return cur.fetchone()


def create_appointment(data, user_id):
    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO appointments (title, date, time, location, notes, category, owner_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            data['title'],
            data['date'],
            data['time'],
            data.get('location', ''),
            data.get('notes', ''),
            data.get('category', 'general'),
            user_id
        ))


def update_appointment(appointment_id, data, user_id):
    with get_cursor() as cur:
        cur.execute("""
            UPDATE appointments
            SET title = %s, date = %s, time = %s, location = %s,
                notes = %s, category = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND owner_id = %s
        """, (
            data['title'],
            data['date'],
            data['time'],
            data.get('location', ''),
            data.get('notes', ''),
            data.get('category', 'general'),
            appointment_id,
            user_id
        ))


def update_status(appointment_id, status, user_id):
    with get_cursor() as cur:
        cur.execute("""
            UPDATE appointments
            SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND owner_id = %s
        """, (status, appointment_id, user_id))


def delete_appointment(appointment_id, user_id):
    with get_cursor() as cur:
        cur.execute("""
            DELETE FROM appointments
            WHERE id = %s AND owner_id = %s
        """, (appointment_id, user_id))


def admin_update_status(appointment_id, status):
    with get_cursor() as cur:
        cur.execute("""
            UPDATE appointments
            SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (status, appointment_id))


def admin_delete_appointment(appointment_id):
    with get_cursor() as cur:
        cur.execute("DELETE FROM appointments WHERE id = %s", (appointment_id,))


def get_all_users():
    with get_cursor() as cur:
        cur.execute("SELECT id, name, email, is_admin, created_at FROM users ORDER BY created_at DESC")
        return cur.fetchall()


def toggle_admin(user_id):
    with get_cursor() as cur:
        cur.execute("""
            UPDATE users SET is_admin = NOT is_admin WHERE id = %s
            RETURNING is_admin
        """, (user_id,))
        return cur.fetchone()


def delete_user(user_id):
    with get_cursor() as cur:
        cur.execute("DELETE FROM appointments WHERE owner_id = %s", (user_id,))
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))


def get_all_appointments_admin():
    with get_cursor() as cur:
        cur.execute("""
            SELECT a.*, u.name as owner_name, u.email as owner_email
            FROM appointments a
            JOIN users u ON a.owner_id = u.id
            ORDER BY a.date ASC, a.time ASC
        """)
        return cur.fetchall()


def get_dashboard_stats(user_id):
    with get_cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'planned') as planned,
                COUNT(*) FILTER (WHERE status = 'done') as done,
                COUNT(*) FILTER (WHERE status = 'canceled') as canceled,
                COUNT(*) as total
            FROM appointments
            WHERE owner_id = %s
        """, (user_id,))
        return cur.fetchone()
