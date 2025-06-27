from data import db, Habit, Category

def create_new_habit(title_input, category_id_input, user_id_input):
    new_habit = Habit(title=title_input, category_id=category_id_input, user_id=user_id_input)
    db.session.add(new_habit)
    db.session.commit()

def edit_a_habit(habit_id, title_input, category_id_input):
    habit = Habit.query.get(habit_id)
    category = Category.query.get(category_id_input)
    if not habit:
        return None
    
    if title_input:
        habit.title = title_input
    if category_id_input:
        habit.category = category
    
    db.session.commit()

def delete_a_habit(habit_id):
    habit = Habit.query.get(habit_id)
    if habit:
        db.session.delete(habit)
        db.session.commit()
        return True
    return False