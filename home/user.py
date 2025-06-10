from data import db, User

def create_new_user(username_input, password_input):
    new_user = User(username=username_input, password=password_input)
    db.session.add(new_user)
    db.session.commit()