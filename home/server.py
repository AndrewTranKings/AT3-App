from flask import Flask, render_template, url_for, redirect, request, jsonify, session
from data import db, User, Habit, HabitLog
from user import create_new_user, update_user_profile
from habit import create_new_habit
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24) #Generate a random session key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app_database_test.db'
upload_folder = app.config['UPLOAD_FOLDER'] = os.path.join('home', 'static', 'Images', 'profile_pics') #Folder for uploaded profile pictures
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB limit
db.init_app(app)


@app.route('/', methods=['GET'])
def calendar():
    user_id = session.get('user_id') #Find which account is logged in
    if not user_id: #If no accoutn logged in send them to login page
        return redirect(url_for('login'))
    
    all_users = User.query.all()
    all_user_habits = Habit.query.filter_by(user_id=user_id).all()
    return render_template('calendar.html', all_users = all_users, all_user_habits = all_user_habits)

@app.route('/profile', methods=['GET'])
def profile():
    #Session management
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    return render_template('profile.html', user=user)

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

@app.route('/shop')
def shop():
    return render_template('shop.html')

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
        session['user_id'] = new_user.id #Automatically logs in new account

        return redirect(url_for('calendar'))
    
@app.route('/signout')
def signout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/create_habit', methods=['GET', 'POST'])
def create_habit():
    if request.method == 'GET':
        return render_template('create_habit.html')
    elif request.method == 'POST':
        user_id = session.get('user_id') #Check for a valid session first
        if not user_id:
            return redirect(url_for('login'))
        
        #Get data from create_habit.html
        title_input = request.form.get('title')
        category_input = request.form.get('category')
        user_id_input = user_id #Take the user_id directly from the session
        create_new_habit(title_input, category_input, user_id_input)
        return redirect(url_for('calendar'))
    
@app.route('/log_habit', methods=['POST'])
def log_habit():
    data = request.get_json()
    habit_id = int(data['habit_id'])
    date_str = data['date']  # e.g. '6-10-2025'
    completed = data['completed']

    date_obj = datetime.strptime(date_str, "%m-%d-%Y").date()

    log = HabitLog.query.filter_by(habit_id=habit_id, date=date_obj).first()
    if completed:
        if not log:
            log = HabitLog(habit_id=habit_id, date=date_obj)
            db.session.add(log)
    else:
        if log:
            db.session.delete(log)

    db.session.commit()
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

    logs = HabitLog.query.filter_by(habit_id=habit_id).all()
    for log in logs:
        if log.date.month == month and log.date.year == year:
            db.session.delete(log)
    db.session.commit()

    return jsonify({"status": "reset"})



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()

