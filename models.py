def user_to_dict(user):
    return {
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'is_admin': bool(user['is_admin']),
        'created_at': user['created_at'],
    }


def task_to_dict(task):
    return {
        'id': task['id'],
        'user_id': task['user_id'],
        'title': task['title'],
        'description': task['description'],
        'due_date': task['due_date'],
        'priority': task['priority'],
        'status': task['status'],
        'created_at': task['created_at'],
        'updated_at': task['updated_at'],
    }
