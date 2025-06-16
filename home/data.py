from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    habits = db.relationship('Habit', backref='user', lazy=True)

    def __init__(self, username, password):
        self.username = username
        self.password = password

class Habit(db.Model): #Need to fix user_id when creating new habit
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    logs = db.relationship('HabitLog', backref='habit', lazy=True)

    def __init__(self, title, category, user_id):
        self.title = title
        self.category = category
        self.user_id = user_id

class HabitLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False)


