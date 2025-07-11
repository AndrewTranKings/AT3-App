from flask import Flask, render_template, url_for, redirect, request, jsonify, session, flash, abort
from data import db, User, Habit, HabitLog, Category, UserCategoryProgress, ShopItem, UserInventory, ActiveEffect, Friend
from user import create_new_user, update_user_profile, initialise_user_category_progress, add_xp_to_category, remove_xp_from_category, get_xp_threshold, calculate_level_from_xp
from habit import create_new_habit, edit_a_habit, delete_a_habit
from active_effect import apply_effect
import os
from datetime import datetime, timedelta
from constants import XP_PER_LOG, COINS_PER_LEVEL
from collections import defaultdict
from sqlalchemy import func, desc

app = Flask(__name__)
app.secret_key = os.urandom(24) #Generate a random session key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app_database_habits2.db'
upload_folder = app.config['UPLOAD_FOLDER'] = os.path.join('home', 'static', 'Images', 'profile_pics') #Folder for uploaded profile pictures
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB limit
db.init_app(app)

#Helper function for creating habits off app start
def seed_categories():
    if Category.query.count() == 0:
        default_categories = ['Health', 'Fitness', 'Productivity', 'Learning', 'Spirituality', 'Creativity']
        for name in default_categories:
            db.session.add(Category(name=name))
        db.session.commit()

def seed_shop_items():
    test_items = [
    ShopItem(
        name="Basic Dumbbells",
        description="A starter set of dumbbells to build strength.",
        price=25,
        category_id=1,
        required_level=1,
        effect_type=None,
        effect_value=None,
        effect_duration_hours=None
    ),
    ShopItem(
        name="Pro Yoga Mat",
        description="Perfect for intense yoga sessions.",
        price=40,
        category_id=1,
        required_level=2,
        effect_type=None,
        effect_value=None,
        effect_duration_hours=None
    ),
    ShopItem(
        name="Running Shoes",
        description="Boosts XP gain by 10% for 6 hours after a workout.",
        price=60,
        category_id=1,
        required_level=3,
        effect_type="xp_boost",
        effect_value=0.10,
        effect_duration_hours=6
    ),
    ShopItem(
        name="Golden Water Bottle",
        description="Multiplies coin rewards by 25% for 4 hours.",
        price=75,
        category_id=1,
        required_level=4,
        effect_type="coin_multiplier",
        effect_value=0.25,
        effect_duration_hours=4
    ),

    ShopItem(
        name="Beginner Spellbook",
        description="Casts basic spells for entry-level mages.",
        price=30,
        category_id=2,
        required_level=1,
        effect_type=None,
        effect_value=None,
        effect_duration_hours=None
    ),
    ShopItem(
        name="Wizard Hat",
        description="Grants 15% extra XP for 12 hours due to increased magical focus.",
        price=50,
        category_id=2,
        required_level=2,
        effect_type="xp_boost",
        effect_value=0.15,
        effect_duration_hours=12
    ),
    ShopItem(
        name="Advanced Spellbook",
        description="Doubles XP for 1 hour — but use it wisely!",
        price=80,
        category_id=2,
        required_level=3,
        effect_type="xp_boost",
        effect_value=1.0,
        effect_duration_hours=1
    ),
    ShopItem(
        name="Lucky Wand",
        description="Coin rewards are boosted by 50% for 2 hours.",
        price=90,
        category_id=2,
        required_level=4,
        effect_type="coin_multiplier",
        effect_value=0.5,
        effect_duration_hours=2
    )
]

    # Insert items into database
    for item in test_items:
        db.session.add(item)

    db.session.commit()
    print("✅ Seeded test shop items successfully.")

@app.context_processor
def inject_user_data():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user:
            return {
                'user_coins': user.coins
                #Add extra variables here if necessary
                }
    return {
        'user_coins': 0
        #Same for here too
        }


@app.route('/', methods=['GET'])
def calendar():
    user_id = session.get('user_id') #Find which account is logged in
    if not user_id: #If no accoutn logged in send them to login page
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    user_coins = user.coins if user else 0
    
    all_users = User.query.all()
    all_user_habits = Habit.query.filter_by(user_id=user_id).all()
    return render_template(
        'calendar.html', 
        all_users = all_users, 
        all_user_habits = all_user_habits,
        user_coins=user_coins,
        user=user
        )

@app.route('/profile', methods=['GET'])
def profile():
    #Session management
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = User.query.get(user_id)

    purchased_items = UserInventory.query.filter_by(user_id=user_id).all()
    active_effects = ActiveEffect.query.filter_by(user_id=user_id).filter(ActiveEffect.expires_at > datetime.utcnow()).all()

    #Get user's friends
    accepted_friends = Friend.query.filter(
        ((Friend.sender_id == user_id) | (Friend.receiver_id == user_id)) &
        (Friend.status == 'accepted')
    ).all()

    #Get the user object for each friend account
    friend_users = []
    for f in accepted_friends:
        friend_id = f.receiver_id if f.sender_id == user_id else f.sender_id
        friend = User.query.get(friend_id)
        if friend:
            friend_users.append(friend)

    #Get top 3 habits for each friend (by log count)
    friend_top_habits = {}
    for friend in friend_users:
        top_habits = (
            db.session.query(Habit)
            .join(HabitLog, Habit.id == HabitLog.habit_id)
            .filter(Habit.user_id == friend.id)
            .group_by(Habit.id)
            .order_by(db.func.count(HabitLog.id).desc())
            .limit(3)
            .all()
        )
        friend_top_habits[friend.id] = top_habits

    return render_template(
        'profile.html', 
        user=user, 
        purchased_items=purchased_items,
        active_effects=active_effects,
        friend_users=friend_users,
        friend_top_habits=friend_top_habits
        )

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    user_id = session.get('user_id') #Check for a valid session first
    if not user_id:
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        return render_template('edit_profile.html', user=user_id) 
    elif request.method == 'POST':
        
        #Get data from edit_profile.html
        email_input = request.form.get('email')
        bio_input = request.form.get('bio')
        pfp_input = request.files.get('profile_pic') #request.file for files
        update_user_profile(user_id, email_input, bio_input, pfp_input, upload_folder)
        #pass in the uploads folder for access in helper function ^
        return redirect(url_for('profile'))

@app.route('/community')
def community():
    #Session management
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = User.query.get(user_id)
    users = User.query.filter(User.id != user.id).all()

    #Track the status of friend requests
    friendships = Friend.query.filter(
        ((Friend.sender_id == user_id) | (Friend.receiver_id == user_id))
    ).all()

    friend_status = {}
    for f in friendships:
        other_id = f.receiver_id if f.sender_id == user_id else f.sender_id
        friend_status[other_id] = f.status

    #Get an account's top 3 habits (ranked by logs)
    users_with_habits = []

    for user in users:
        # Query to get top 3 habits for this user by habit log count
        top_habits = (
            db.session.query(Habit, func.count(HabitLog.id).label('log_count'))
            .join(HabitLog, Habit.id == HabitLog.habit_id)
            .filter(Habit.user_id == user.id)
            .group_by(Habit.id)
            .order_by(desc('log_count'))
            .limit(3)
            .all()
        )
        
        #Pass in habit object
        top_habits = [habit for habit, count in top_habits]

        users_with_habits.append({
            'user': user,
            'top_habits': top_habits
        })

    return render_template('community.html', users_with_habits=users_with_habits, friend_status=friend_status)

#Used in community.js
@app.route('/send_friend_request/<int:receiver_id>', methods=['POST'])
def send_friend_request(receiver_id):
    #Session management
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    existing = Friend.query.filter_by(sender_id=user_id, receiver_id=receiver_id).first()
    if not existing:
        new_request = Friend(sender_id=user_id, receiver_id=receiver_id, status='pending')
        db.session.add(new_request)
        db.session.commit()
    return jsonify({'status': 'request_sent'})

#Used in inbox.js
@app.route('/respond_friend_request/<int:request_id>', methods=['POST'])
def respond_friend_request(request_id):
    #Session management
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    action = request.json.get('action')
    friend_request = Friend.query.get_or_404(request_id)
    if friend_request.receiver_id != user_id:
        abort(403)
    
    if action == 'accept':
        friend_request.status = 'accepted'
    elif action == 'reject':
        friend_request.status = 'rejected'
    
    db.session.commit()
    return jsonify({'status': f'{action}ed'})

@app.route('/inbox')
def inbox():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    #Retrieve all pending friend requests
    incoming_requests = Friend.query.filter_by(receiver_id=user_id, status='pending').all()
    #Retrieve all sender accounts of those friend requests
    senders = [User.query.get(req.sender_id) for req in incoming_requests]
    #Zip requests and senders together as a list of tuples
    requests_and_senders = list(zip(incoming_requests, senders))

    return render_template('inbox.html', requests_and_senders=requests_and_senders)


@app.route('/shop')
def shop():
    #Session management
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = User.query.get(user_id)
    
    # Get user's levels in each category
    category_progress = db.session.query(
        UserCategoryProgress.category_id,
        UserCategoryProgress.level
    ).filter_by(user_id=user_id).all()
    category_level_map = {c.category_id: c.level for c in category_progress}

    # Get all shop items the user can afford AND has unlocked
    items = ShopItem.query.all()
    unlocked_items = [
        item for item in items
        if category_level_map.get(item.category_id, 0) >= item.required_level
    ]

    return render_template('shop.html', items=unlocked_items, user_coins=user.coins)

@app.route('/buy_item/<int:item_id>', methods=['POST'])
def buy_item(item_id):    
    #Session management
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = User.query.get(user_id)
    
    if request.method == 'POST':
        item = ShopItem.query.get_or_404(item_id)

        # Check user's level in the item's category
        progress = UserCategoryProgress.query.filter_by(
            user_id=user_id,
            category_id=item.category_id
        ).first()

        if not progress or progress.level < item.required_level:
            return jsonify({"success": False, "message": "Level too low."}), 403

        if user.coins < item.price:
            return jsonify({"success": False, "message": "Not enough coins."}), 403
        user.coins -= item.price

        # Check if user already has this item in inventory
        inventory_entry = UserInventory.query.filter_by(user_id=user_id, item_id=item_id).first()
        if inventory_entry:
            # If user already owns item increase quantity by one
            inventory_entry.quantity += 1
        else:
            # If not already owned add item to inventory
            inventory_entry = UserInventory(user_id=user_id, item_id=item_id, quantity=1)
            db.session.add(inventory_entry)
        
        db.session.commit()
        flash(f"You successfully purchased {item.name}!", "success")
        return redirect(url_for('calendar'))
    
@app.route('/use_item/<int:item_id>', methods=['POST'])
def use_item(item_id):
    #Session management
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    # Find item in user's inventory
    inventory_entry = UserInventory.query.filter_by(user_id=user_id, item_id=item_id).first()
    if not inventory_entry:
        flash("You don't own this item.")
        return redirect(url_for('profile'))

    item = ShopItem.query.get(item_id)

    # Check if item has effect fields
    if item.effect_type and item.effect_value and item.effect_duration_hours:
        expires_at = datetime.utcnow() + timedelta(hours=item.effect_duration_hours)
        effect = ActiveEffect(
            user_id=user_id,
            item_id=item.id,
            effect_type=item.effect_type,
            effect_value=item.effect_value,
            expires_at=expires_at
        )
        db.session.add(effect)
        flash(f"{item.name} activated: {item.effect_type} +{int(item.effect_value * 100)}% for {item.effect_duration_hours}h")
    else:
        flash("This item cannot be used.")

    # Decrement quantity and delete if zero
    inventory_entry.quantity -= 1
    if inventory_entry.quantity <= 0:
        db.session.delete(inventory_entry)

    db.session.commit()
    return redirect(url_for('profile'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        username_input = request.form.get('username')
        password_input = request.form.get('password')
        
        #Verify the username and password:
        user = User.query.filter_by(username=username_input).first()
        if user and user.password == password_input:
            session['user_id'] = user.id  # store user id in session
            return redirect(url_for('calendar'))
        else:
            return "Invalid username or password", 401

@app.route('/signup', methods=['GET', 'POST'])
def signup(): #The same as the login route without verification as the user is creating a new account
    if request.method == 'GET':
        return render_template('signup.html')
    elif request.method == 'POST':
        username_input = request.form.get('username')
        password_input = request.form.get('password')

        new_user = create_new_user(username_input, password_input)
        if new_user is None:
            return "Username already taken, please choose another.", 400
        
        session['user_id'] = new_user.id #Automatically logs in new account
        initialise_user_category_progress(new_user.id) #Create the progress bar per category

        return redirect(url_for('calendar'))
    
@app.route('/signout')
def signout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/create_habit', methods=['GET', 'POST'])
def create_habit():
    if request.method == 'GET':
        all_categories = Category.query.all()
        return render_template('create_habit.html', categories=all_categories)
    elif request.method == 'POST':
        user_id = session.get('user_id') #Check for a valid session first
        if not user_id:
            return redirect(url_for('login'))
        
        #Get data from create_habit.html
        title_input = request.form.get('title')
        category_id_input = int(request.form.get('category_id'))
        user_id_input = user_id #Take the user_id directly from the session
        create_new_habit(title_input, category_id_input, user_id_input)
        return redirect(url_for('calendar'))
    
@app.route('/edit_habit/<int:habit_id>', methods=['GET', 'POST'])
def edit_habit(habit_id):
    habit = Habit.query.get(habit_id)
    if not habit:
        return "Habit not found", 404
    
    all_categories = Category.query.all()
    
    if request.method == 'POST':
        title_input = request.form.get('title')
        category_id_input = int(request.form.get('category_id'))
        user_id = session.get('user_id')

        #Check if the category is actually changing
        old_category_id = habit.category_id
        new_category_id = category_id_input

        if new_category_id != old_category_id:
            #Calculate XP to transfer based on how many times habit was logged
            log_count = HabitLog.query.filter_by(habit_id=habit_id).count()
            xp_change = log_count * XP_PER_LOG  # XP per log (change as needed)

            #Subtract XP from old category progress
            old_progress = UserCategoryProgress.query.filter_by(
                user_id=user_id,
                category_id=old_category_id
            ).first()
            if old_progress:
                old_progress.xp = max(0, old_progress.xp - xp_change)

            #Add XP to new category progress (create if doesn't exist)
            new_progress = UserCategoryProgress.query.filter_by(
                user_id=user_id,
                category_id=new_category_id
            ).first()
            if not new_progress:
                new_progress = UserCategoryProgress(
                    user_id=user_id,
                    category_id=new_category_id,
                    xp=0
                )
                db.session.add(new_progress)

            new_progress.xp += xp_change

        edit_a_habit(habit_id, title_input, category_id_input)
        return redirect(url_for('calendar'))

    return render_template('edit_habit.html', habit=habit, categories=all_categories)   

@app.route('/delete_habit/<int:habit_id>', methods=['POST'])
def delete_habit(habit_id):
    #Only logged in user can delete their habit
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    habit = Habit.query.get(habit_id)
    if not habit or habit.user_id != user_id:
        return "Habit not found or unauthorized", 404
    
    #Remove XP per log
    logs = HabitLog.query.filter_by(habit_id=habit_id).all()
    xp_to_remove = XP_PER_LOG * len(logs)  # Assumes 10 XP per log
    category_id = habit.category_id

    #Update UserCategoryProgress when deleting XP
    progress = UserCategoryProgress.query.filter_by(user_id=user_id, category_id=category_id).first()
    if progress:
        progress.xp = max(0, progress.xp - xp_to_remove)
    
    success = delete_a_habit(habit_id)
    if not success:
        return "Habit not found", 404
    db.session.commit()
    return redirect(url_for('calendar'))

@app.route('/log_habit', methods=['POST'])
def log_habit():
    user_id = session.get('user_id') #Find which account is logged in
    data = request.get_json()
    habit_id = int(data['habit_id'])
    date_str = data['date']  # e.g. '6-10-2025'
    completed = data['completed']

    date_obj = datetime.strptime(date_str, "%m-%d-%Y").date()
    log = HabitLog.query.filter_by(habit_id=habit_id, date=date_obj).first()
    habit = Habit.query.get(habit_id)

    if completed:
        if not log:
            log = HabitLog(habit_id=habit_id, date=date_obj)
            db.session.add(log)

            #Adds any xp boosters onto the given value
            adjusted_xp = int(apply_effect(user_id, XP_PER_LOG, 'xp_boost'))
            add_xp_to_category(user_id, habit.category_id, adjusted_xp)
            print(f"XP logged: {adjusted_xp}")
    else:
        if log:
            db.session.delete(log)
            adjusted_xp = int(apply_effect(user_id, XP_PER_LOG, 'xp_boost'))
            remove_xp_from_category(user_id, habit.category_id, adjusted_xp)
            print(f"XP removed: {adjusted_xp}")

    db.session.commit()

    #Award coins for levelling up
    user = User.query.get(user_id)
    progress = UserCategoryProgress.query.filter_by(user_id=user_id, category_id=habit.category_id).first()

    if progress:
        total_xp = progress.xp
        new_level = calculate_level_from_xp(total_xp)

        session_key = f'level_category_{habit.category_id}'
        previous_level = session.get(session_key, calculate_level_from_xp(total_xp - XP_PER_LOG))
        if new_level > previous_level:
            level_diff = new_level - previous_level
            base_coins_earned = level_diff * COINS_PER_LEVEL
            #Add a coin multiplier to coins earnt (if any active)
            adjusted_coins = int(apply_effect(user_id, base_coins_earned, 'coin_multiplier'))
            user.coins += adjusted_coins
            db.session.commit()
            session[session_key] = new_level  # Prevent duplicate rewards

    return jsonify({"status": "success"})

@app.route('/get_habit_logs')
def get_habit_logs():
    habit_id = int(request.args.get('habit_id'))
    month = int(request.args.get('month'))
    year = int(request.args.get('year'))

    logs = HabitLog.query.filter_by(habit_id=habit_id).all()

    result = []
    for log in logs:
        if log.date.month == month and log.date.year == year:
            result.append(f"{log.date.month}-{log.date.day}-{log.date.year}")

    return jsonify(result)

@app.route('/reset_habit_logs', methods=['POST'])
def reset_habit_logs():
    data = request.get_json()
    habit_id = int(data['habit_id'])
    month = int(data['month'])
    year = int(data['year'])

    #Get the habit and validate user
    user_id = session.get('user_id')
    habit = Habit.query.get(habit_id)
    if not habit or habit.user_id != user_id:
        return jsonify({"error": "Habit not found or unauthorized"}), 403

    #Only fetch logs for that month/year
    logs_to_delete = HabitLog.query.filter(
        HabitLog.habit_id == habit_id,
        db.extract('month', HabitLog.date) == month,
        db.extract('year', HabitLog.date) == year
    ).all()

    #Remove XP per log
    base_xp_removed = len(logs_to_delete) * XP_PER_LOG

    # Adjust XP removal based on active XP boost effects
    now = datetime.utcnow()
    active_xp_boosts = ActiveEffect.query.filter_by(
        user_id=user_id,
        effect_type='xp_boost'
    ).filter(ActiveEffect.expires_at > now).all()

    # Add all active boosts onto each other
    total_boost = sum(effect.effect_value for effect in active_xp_boosts)

    # Adjust XP removed considering boosts (divide base XP by (1 + total_boost))
    adjusted_xp_removed = round(base_xp_removed / (1 + total_boost)) if total_boost > 0 else base_xp_removed

    for log in logs_to_delete:
        db.session.delete(log)

    #Remove XP from user's progress for that category
    if adjusted_xp_removed > 0:
        remove_xp_from_category(user_id, habit.category_id, adjusted_xp_removed)
        print(f"Total xp removed: {adjusted_xp_removed}")

    db.session.commit()

    #Return informative response
    return jsonify({
        "status": "reset_successful",
        "logs_deleted": len(logs_to_delete),
        "xp_removed": adjusted_xp_removed
    })

@app.route('/get_category_progress/<int:category_id>')
def get_category_progress(category_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    progress = UserCategoryProgress.query.filter_by(user_id=user_id, category_id=category_id).first()
    category = Category.query.get(category_id)

    total_xp = progress.xp if progress else 0
    level = calculate_level_from_xp(total_xp)

    # Cumalitve XP required for the next level
    xp_to_next_level = get_xp_threshold(level + 1)

    return jsonify({
        "category_name": category.name if category else "Unknown",
        "current_xp": total_xp,
        "xp_to_next_level": xp_to_next_level,
        "level": level
    })

@app.route('/get_user_coins')
def get_user_coins():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"coins": 0})
    user = User.query.get(user_id)
    return jsonify({"coins": user.coins})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_categories()
        #seed_shop_items()
    app.run()

