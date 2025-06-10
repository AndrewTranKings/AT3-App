from flask import Flask, render_template, url_for, redirect, request
from data import db, User
from user import create_new_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example_test_db.db'
db.init_app(app)


@app.route('/', methods=['GET'])
def calendar():
    all_users = User.query.all()
    return render_template('calendar.html', all_users = all_users)

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
        create_new_user(username_input, password_input)
        return redirect(url_for('calendar'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()

