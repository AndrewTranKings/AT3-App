from flask import Flask, render_template, url_for, redirect, request
from data import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example_test_db.db'
db.init_app(app)


@app.route('/', methods=['GET'])
def calendar():
    return render_template('calendar.html')

@app.route('/profile', methods=['GET'])
def profile():
    return render_template('profile.html')

@app.route('/community')
def community():
    return render_template('community.html')

@app.route('/shop')
def shop():
    return render_template('shop.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()

