from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime, timedelta

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_pic = db.Column(db.String(200), nullable=True) #String stores path to image
    coins = db.Column(db.Integer, default=0)
    habits = db.relationship('Habit', backref='user', lazy=True)
    #Allows one user to have progress for multiple categories
    category_progress = db.relationship('UserCategoryProgress', back_populates='user', lazy=True)

    def __init__(self, username, password):
        self.username = username
        self.password = password

class Friend(db.Model): #For friend requesting other accounts
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending') #E.g. pending, accepted, rejected, blocked
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    #Prevent duplicate friend requests
    __table_args__ = (db.UniqueConstraint('sender_id', 'receiver_id', name='unique_friendship'),)


class Habit(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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

    def __init__(self, user_id, category_id, xp=0, level=1):
        self.user_id = user_id
        self.category_id = category_id
        self.xp = xp
        self.level = level

class UserInventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('shop_item.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    shop_item = db.relationship("ShopItem")

class ShopItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    required_level = db.Column(db.Integer, nullable=False)

    #Effects allow items to have in-game impact
    effect_type = db.Column(db.String(50)) # e.g. 'xp_boost', 'coin_multiplier'
    effect_value = db.Column(db.Float) # e.g. 0.15 for 15%
    effect_duration_hours = db.Column(db.Integer) #e.g. 24 for 24 hours

class ActiveEffect(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('shop_item.id'), nullable=False)
    effect_type = db.Column(db.String(50), nullable=False)
    effect_value = db.Column(db.Float, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    user = db.relationship("User", backref="active_effects")
    item = db.relationship("ShopItem")
