from data import db, User, Category, UserCategoryProgress, Friend
import uuid
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} #only file types allowed for pfp

def initialise_user_category_progress(user_id):
    categories = Category.query.all()
    for category in categories:
        # Check if user already has progress record for category
        existing = UserCategoryProgress.query.filter_by(user_id=user_id, category_id=category.id).first()
        if not existing:
            progress = UserCategoryProgress(user_id=user_id, category_id=category.id)
            db.session.add(progress)
    db.session.commit()

def get_xp_threshold(level):
    if level == 1:
        return 0
    return 100 + (level - 2) * 115 # XP needed increases by 15 per level

def add_xp_to_category(user_id, category_id, amount):
    progress = UserCategoryProgress.query.filter_by(user_id=user_id, category_id=category_id).first()

    if not progress:
        progress = UserCategoryProgress(user_id=user_id, category_id=category_id, xp=amount)
        db.session.add(progress)
    else:
        progress.xp += amount

    progress.level = calculate_level_from_xp(progress.xp)
    db.session.commit()

def calculate_level_from_xp(total_xp):
    level = 1
    while total_xp >= get_xp_threshold(level + 1):
        level += 1
    return level

def remove_xp_from_category(user_id, category_id, xp_amount):
    progress = UserCategoryProgress.query.filter_by(user_id=user_id, category_id=category_id).first()

    if progress:
        progress.xp = max(0, progress.xp - xp_amount)
        progress.level = calculate_level_from_xp(progress.xp)
        db.session.commit()
    

def create_new_user(username_input, email_input, dob_input, password_input, role='user'):
    # Check if username already exists
    existing_user = User.query.filter_by(username=username_input).first()
    if existing_user:
        return None  # Or raise an exception or handle it however you want
    
    dob_date = datetime.strptime(dob_input, "%Y-%m-%d").date()

    new_user = User(username=username_input, email=email_input, dob=dob_date, password=password_input, role=role)
    db.session.add(new_user)
    db.session.commit()

    initialise_user_category_progress(new_user.id)
    return new_user

def update_user_profile(user_id, email_input, dob_input, bio_input, pfp_input, upload_folder):
    user = User.query.get(user_id)
    dob_date = datetime.strptime(dob_input, "%Y-%m-%d").date()
    if user:
        user.email = email_input
        user.dob = dob_date
        user.bio = bio_input
        
        # Save new profile picture if uploaded
        if pfp_input and pfp_input.filename != '':
            if allowed_file(pfp_input.filename):

                # Generate unique filename
                filename = secure_filename(pfp_input.filename)
                ext = os.path.splitext(filename)[1]
                unique_filename = f"{uuid.uuid4().hex}{ext}"

                filepath = os.path.join(upload_folder, unique_filename)
                pfp_input.save(filepath)

                user.profile_pic = f"Images/profile_pics/{unique_filename}"
            else:
                print("File type not allowed") #Raise error

        db.session.commit()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_friends_with(self, other_user):
    return Friend.query.filter(
        ((Friend.sender_id == self.id) & (Friend.receiver_id == other_user.id)) |
        ((Friend.sender_id == other_user.id) & (Friend.receiver_id == self.id)),
        Friend.status == 'accepted'
    ).first() is not None

def has_pending_request_with(self, other_user):
    return Friend.query.filter(
        ((Friend.sender_id == self.id) & (Friend.receiver_id == other_user.id)) |
        ((Friend.sender_id == other_user.id) & (Friend.receiver_id == self.id)),
        Friend.status == 'pending'
    ).first() is not None

#MUST ADD A VISUAL ALERT FOR USER TO KNOW FILE TYPE IS INCORRECT
#Switch to HTTPS server