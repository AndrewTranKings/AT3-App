from flask import Flask, render_template, url_for, redirect, request, jsonify, session
from data import db, User, Habit, HabitLog, Category, UserCategoryProgress, ShopItem, UserInventory
from user import create_new_user, update_user_profile, initialise_user_category_progress, add_xp_to_category, remove_xp_from_category, get_xp_threshold, calculate_level_from_xp
from habit import create_new_habit, edit_a_habit, delete_a_habit
import os
from datetime import datetime
from constants import XP_PER_LOG, COINS_PER_LEVEL

app = Flask(__name__)
app.secret_key = os.urandom(24) #Generate a random session key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app_database_tests.db'
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
            category_id=1,  # Health
            required_level=1
        ),
        ShopItem(
            name="Pro Yoga Mat",
            description="Perfect for intense yoga sessions.",
            price=40,
            category_id=1,  # Health
            required_level=2
        ),
        ShopItem(
            name="Running Shoes",
            description="Boost your running efficiency.",
            price=60,
            category_id=1,  # Health
            required_level=3
        ),
        ShopItem(
            name="Beginner Spellbook",
            description="Casts basic spells for entry-level mages.",
            price=30,
            category_id=2,  # Fitness
            required_level=1
        ),
        ShopItem(
            name="Wizard Hat",
            description="Increases your magical charisma.",
            price=50,
            category_id=2,  # Fitness
            required_level=2
        ),
        ShopItem(
            name="Advanced Spellbook",
            description="Grants access to powerful enchantments.",
            price=80,
            category_id=2,  # Fitness
            required_level=3
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
        user_coins=user_coins
        )

@app.route('/profile', methods=['GET'])
def profile():
    #Session management
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    purchased_items = db.session.query(ShopItem).join(UserInventory).filter(UserInventory.user_id == user.id).all()
    return render_template('profile.html', user=user, purchased_items=purchased_items)

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
    return render_template('community.html')

# routes.py
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
        db.session.add(UserInventory(user_id=user_id, item_id=item.id))
        db.session.commit()
        return jsonify({"success": True})

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
            add_xp_to_category(user_id, habit.category_id, XP_PER_LOG)
    else:
        if log:
            db.session.delete(log)
            remove_xp_from_category(user_id, habit.category_id, XP_PER_LOG)

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
            coins_earned = level_diff * COINS_PER_LEVEL
            user.coins += coins_earned
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
    xp_removed = len(logs_to_delete) * XP_PER_LOG
    for log in logs_to_delete:
        db.session.delete(log)

    #Remove XP from user's progress for that category
    if xp_removed > 0:
        remove_xp_from_category(user_id, habit.category_id, xp_removed)

    db.session.commit()

    #Return informative response
    return jsonify({
        "status": "reset_successful",
        "logs_deleted": len(logs_to_delete),
        "xp_removed": xp_removed
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

