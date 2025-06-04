from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    priority = db.Column(db.Integer, default=0)
    is_complete = db.Column(db.Boolean, default=False)

    def __init__(self, title, description=None, priority=0):
        self.title = title
        self.description = description
        self.priority = priority
        self.is_complete = False


