from flask import Flask, render_template, url_for, redirect, request, jsonify, session
from data import db, User, Habit
from user import create_new_user
from habit import create_new_habit
import os

app = Flask(__name__)
app.secret_key = os.urandom(24) #Generate a random session key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app_database.db'
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
    return render_template('profile.html')

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

#FIX PROBLEM: ONCE SIGNING UP, THE USER STILL IS LOGGED IN WITH OLD ACCOUNT
@app.route('/signup', methods=['GET', 'POST'])
def signup(): #The same as the login route without verification as the user is creating a new account
    if request.method == 'GET':
        return render_template('signup.html')
    elif request.method == 'POST':
        username_input = request.form.get('username')
        password_input = request.form.get('password')
        create_new_user(username_input, password_input)
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
        user_id_input = request.form.get('user_id')
        create_new_habit(title_input, category_input, user_id_input)
        return redirect(url_for('calendar'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()

