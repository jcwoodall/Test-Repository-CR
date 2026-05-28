import csv
import io

from flask import Blueprint, Response, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from database import get_db
from models import task_to_dict

TASK_COLUMNS = {'id', 'title', 'due_date', 'priority', 'status', 'created_at', 'updated_at'}

tasks_bp = Blueprint('tasks', __name__)


@tasks_bp.route('', methods=['GET'])
@jwt_required()
def list_tasks():
    user_id = get_jwt_identity()
    db = get_db()
    try:
        tasks = db.execute('SELECT * FROM tasks WHERE user_id = ?', (user_id,)).fetchall()
        return jsonify([task_to_dict(t) for t in tasks])
    finally:
        db.close()


@tasks_bp.route('', methods=['POST'])
@jwt_required()
def create_task():
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    if not data.get('title'):
        return jsonify({'error': 'title is required'}), 400

    db = get_db()
    try:
        cursor = db.execute(
            'INSERT INTO tasks (user_id, title, description, due_date, priority, status) VALUES (?, ?, ?, ?, ?, ?)',
            (
                user_id,
                data['title'],
                data.get('description'),
                data.get('due_date'),
                data.get('priority', 'medium'),
                data.get('status', 'pending'),
            ),
        )
        db.commit()
        task = db.execute('SELECT * FROM tasks WHERE id = ?', (cursor.lastrowid,)).fetchone()
        return jsonify(task_to_dict(task)), 201
    finally:
        db.close()


@tasks_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    user_id = get_jwt_identity()
    db = get_db()
    try:
        task = db.execute(
            'SELECT * FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id)
        ).fetchone()
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        return jsonify(task_to_dict(task))
    finally:
        db.close()


@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    db = get_db()
    try:
        task = db.execute(
            'SELECT * FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id)
        ).fetchone()
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        db.execute(
            '''UPDATE tasks
               SET title=?, description=?, due_date=?, priority=?, status=?,
                   updated_at=CURRENT_TIMESTAMP
               WHERE id=? AND user_id=?''',
            (
                data.get('title', task['title']),
                data.get('description', task['description']),
                data.get('due_date', task['due_date']),
                data.get('priority', task['priority']),
                data.get('status', task['status']),
                task_id,
                user_id,
            ),
        )
        db.commit()
        task = db.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
        return jsonify(task_to_dict(task))
    finally:
        db.close()


@tasks_bp.route('/admin/search', methods=['GET'])
@jwt_required()
def admin_search():
    user_id = get_jwt_identity()
    db = get_db()
    try:
        user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user or not user['is_admin']:
            return jsonify({'error': 'Forbidden'}), 403

        keyword = request.args.get('q', '')
        sort_by = request.args.get('sort_by', 'created_at')
        order = request.args.get('order', 'desc').upper()

        # Column names can't be parameterized — use an allowlist instead
        if sort_by not in TASK_COLUMNS:
            sort_by = 'created_at'
        if order not in ('ASC', 'DESC'):
            order = 'DESC'

        tasks = db.execute(
            f'SELECT * FROM tasks WHERE title LIKE ? OR description LIKE ? ORDER BY {sort_by} {order}',
            (f'%{keyword}%', f'%{keyword}%'),
        ).fetchall()

        if request.args.get('format') == 'csv':
            out = io.StringIO()
            writer = csv.writer(out)
            writer.writerow(['id', 'user_id', 'title', 'description', 'due_date',
                             'priority', 'status', 'created_at', 'updated_at'])
            for t in tasks:
                writer.writerow([t['id'], t['user_id'], t['title'], t['description'],
                                 t['due_date'], t['priority'], t['status'],
                                 t['created_at'], t['updated_at']])
            return Response(
                out.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=tasks.csv'},
            )

        return jsonify([task_to_dict(t) for t in tasks])
    finally:
        db.close()


@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    user_id = get_jwt_identity()
    db = get_db()
    try:
        task = db.execute(
            'SELECT * FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id)
        ).fetchone()
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        db.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
        db.commit()
        return jsonify({'message': 'Task deleted'})
    finally:
        db.close()
