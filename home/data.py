from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_pic = db.Column(db.String(200), nullable=True) #String stores path to image
    habits = db.relationship('Habit', backref='user', lazy=True)

    def __init__(self, username, password):
        self.username = username
        self.password = password

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    logs = db.relationship('HabitLog', backref='habit', lazy=True, cascade='all, delete-orphan')

    def __init__(self, title, category, user_id):
        self.title = title
        self.category = category
        self.user_id = user_id

class HabitLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False)

    def _init__(self, date, habit_id):
        self.date = date
        self.habit_id = habit_id

