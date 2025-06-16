from data import db, Habit

def create_new_habit(title_input, category_input, user_id_input):
    new_habit = Habit(title=title_input, category=category_input, user_id=user_id_input)
    db.session.add(new_habit)
    db.session.commit()