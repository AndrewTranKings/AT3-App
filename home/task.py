from data import db, Task

def user_create_task(title, description, priority):
    new_task = Task(title=title, description=description, priority=priority)
    db.session.add(new_task)
    db.session.commit()
    return new_task

def user_update_task(task_id, is_complete=True):
    task = Task.query.get(task_id)
    if task:
        task.is_complete = is_complete
        db.session.commit()

def user_delete_task(task_id):
    task = Task.query.get(task_id)
    if task:
        db.session.delete(task)
        db.session.commit()
