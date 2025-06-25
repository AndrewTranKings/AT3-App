from data import db, User
import uuid
import os
from werkzeug.utils import secure_filename
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} #only file types allowed for pfp

def create_new_user(username_input, password_input):
    new_user = User(username=username_input, password=password_input)
    db.session.add(new_user)
    db.session.commit()
    return new_user

def update_user_profile(user_id, email_input, bio_input, pfp_input, upload_folder):
    user = User.query.get(user_id)
    if user:
        user.email = email_input
        user.bio = bio_input
        
        # Save new profile picture if uploaded
        if pfp_input and pfp_input.filename != '':
            if allowed_file(pfp_input.filename):

                # Generate unique filename
                filename = secure_filename(pfp_input.filename)
                ext = os.path.splitext(filename)[1]
                unique_filename = f"{uuid.uuid4().hex}{ext}"

                filepath = os.path.join(upload_folder, unique_filename)
                pfp_input.save(filepath)

                user.profile_pic = f"Images/profile_pics/{unique_filename}"
            else:
                print("File type not allowed") #Raise error

        db.session.commit()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#MUST ADD A VISUAL ALERT FOR USER TO KNOW FILE TYPE IS INCORRECT
#Sort out calendar bug where no habit selected displays 31 days
#Work on shop or community