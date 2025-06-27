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
    #Allows one user to have progress for multiple categories
    category_progress = db.relationship('UserCategoryProgress', back_populates='user', lazy=True)

    def __init__(self, username, password):
        self.username = username
        self.password = password

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(100), nullable=False)

    #One category can have multiple habits
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref='habits')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    logs = db.relationship('HabitLog', backref='habit', lazy=True, cascade='all, delete-orphan')

    def __init__(self, title, category_id, user_id):
        self.title = title
        self.category_id = category_id
        self.user_id = user_id

class HabitLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False)

    def _init__(self, date, habit_id):
        self.date = date
        self.habit_id = habit_id

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __init__(self, name):
        self.name = name

class UserCategoryProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

    xp = db.Column(db.Integer, default=0) #Xp for a specific category
    level = db.Column(db.Integer, default=1) #Level for a specific category

    user = db.relationship('User', back_populates='category_progress')
    category = db.relationship('Category')

    #Ensure one progression bar per category
    __table_args__ = (db.UniqueConstraint('user_id', 'category_id', name='uix_user_category'),)

    def __init__(self, user_id, category_id):
        self.user_id = user_id
        self.category_id = category_id
        self.xp = 0
        self.level = 1


