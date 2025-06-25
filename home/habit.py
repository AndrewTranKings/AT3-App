from data import db, Habit

def create_new_habit(title_input, category_input, user_id_input):
    new_habit = Habit(title=title_input, category=category_input, user_id=user_id_input)
    db.session.add(new_habit)
    db.session.commit()

def edit_a_habit(habit_id, title_input, category_input):
    habit = Habit.query.get(habit_id)
    if not habit:
        return None
    
    if title_input:
        habit.title = title_input
    if category_input:
        habit.category = category_input
    
    db.session.commit()

def delete_a_habit(habit_id):
    habit = Habit.query.get(habit_id)
    if habit:
        db.session.delete(habit)
        db.session.commit()
        return True
    return False