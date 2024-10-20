from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify, g
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import bcrypt
from email_validator import validate_email, EmailNotValidError
import sqlite3
from datetime import datetime, timezone, timedelta
import os
from inference_sdk import InferenceHTTPClient
import requests

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

CLIENT = InferenceHTTPClient(
    api_url="https://classify.roboflow.com",
    api_key="INSERT_KEY_HERE"
)

app = Flask(__name__, static_folder='static')
app.secret_key = 'your_secret_key'
login_manager = LoginManager(app)

## Turn on if we want to use CSRF protection
# from flask_wtf.csrf import CSRFProtect
# csrf = CSRFProtect(app)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('database.db')
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Setup in-memory SQLite database
conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    signup_time TEXT NOT NULL
)
''')

def classify_image(image_path):
    result = CLIENT.infer(image_path, model_id="food-classification-rtszh/4")
    return result

def recipe_search(food_query):
    API_KEY = 'INSERT_KEY_HERE'
    APP_ID  = '2a940906'
    result = requests.get(
    f'https://api.edamam.com/api/recipes/v2?type=public&q={food_query}&app_id={APP_ID}&app_key={API_KEY}')
    data = result.json()
    return data

def get_next_image_name():
    existing_files = os.listdir(UPLOAD_FOLDER)
    index = 0
    while True:
        filename = f'uploaded_image_{index}.png'
        if filename not in existing_files:
            return os.path.join(UPLOAD_FOLDER, filename)
        index += 1

# User Model for Flask-Login (Test user: test@test.com, pass:testtest)
class User(UserMixin):
    def __init__(self, id, email, password, signup_time):
        self.id = id
        self.email = email
        self.password = password
        self.signup_time = signup_time

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        return User(*user_data)
    return None

def validate_email_password(email, password):
    try:
        validate_email(email)
    except EmailNotValidError:
        flash("Invalid email format.", 'error')
        return False
    
    if len(password) < 8:
        flash("Password must be at least 8 characters long.", 'error')
        return False
    
    return True

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        action = request.form.get('action')
        print(action)
        
        db = get_db()
        cursor = db.cursor()

        if action == 'login':
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user_data = cursor.fetchone()
            if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data[2]):
                user = User(user_data[0], user_data[1], user_data[2], user_data[3])
                login_user(user)
                session['user_id'] = user_data[0]
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid login credentials.', 'error')
        
        elif action == 'signup':
            if validate_email_password(email, password):
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                signup_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                try:
                    cursor.execute(
                        'INSERT INTO users (email, password, signup_time) VALUES (?, ?, ?)',
                        (email, hashed_password, signup_time)
                    )
                    db.commit()  
                    flash('Account created! You can now log in.', 'success')
                    return redirect(url_for('home'))
                except sqlite3.IntegrityError:
                    flash('Email already exists.', 'error')
    return render_template('home.html')

@app.route('/dashboard')
@login_required
def dashboard():

    db = get_db()
    cursor = db.cursor()
    cursor.execute('''SELECT *, ENERC_KCAL_kcal as calories, 
                   PROCNT_g as protein, CHOCDF_g as carbs, FAT_g as fat, timestamp FROM diary_meal_entries 
                   WHERE user_id = ? ORDER BY datetime(timestamp) DESC''', (current_user.id,))
    meals = cursor.fetchall()

    # Get the last 7 days of diary entries
    seven_days_ago = datetime.now() - timedelta(days=7)
    cursor.execute('''
        SELECT strftime('%Y-%m-%d', timestamp) AS day, 
               SUM(ENERC_KCAL_kcal) AS calories
        FROM diary_meal_entries 
        WHERE user_id = ? AND timestamp >= ? 
        GROUP BY day 
        ORDER BY day DESC
    ''', (current_user.id, seven_days_ago))
    meals_last_7_days = cursor.fetchall()
    db.close()

    # Pass the meals to the dashboard template
    return render_template('dashboard.html', user=current_user, meals=meals, user_id=current_user.id, meals_last_7_days=meals_last_7_days)

@app.route('/get_user_id')
@login_required
def get_user_id():
    return jsonify({"user_id": session.get('user_id')})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

# About Us page route
@app.route('/about-us')
def about_us():
    return render_template('about_us.html')

# Premium page route
@app.route('/premium')
def premium():
    return render_template('premium.html')

# Contact Us page route
@app.route('/contact-us', methods=['GET', 'POST'])
def contact_us():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('contact_us'))
    return render_template('contact_us.html')

# Submit feedback route
@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']
    flash('Feedback submitted successfully.', 'success')
    return redirect(url_for('contact_us'))

# Route to handle the image upload and prediction
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'})
    
    image_path = get_next_image_name()
    file.save(image_path)
    predictions = [item['class'].replace('_', ' ').title() for item in classify_image(image_path)['predictions'][0:3]]
    return jsonify({
        'status': 'success',
        'image_path': image_path,
        'predictions': predictions
    })

@app.route('/get_image_path')
@login_required
def get_image_path():
    meal_id = request.args.get('meal_id')
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        'SELECT * FROM diary_meal_entries WHERE id = ? LIMIT 1',
        (meal_id,)
    )
    result = cursor.fetchone()
    db.close()

    if result:
        return jsonify({"status": "success", "image_path": result[-2], "image_time": result[-1]})
    else:
        return jsonify({"status": "error", "message": "Image not found"})

# Route to handle the POST request for adding to the diary
@app.route('/add_to_diary', methods=['POST'])
def add_to_diary():
    try:
        data = request.json
        print("Received data:", data)  
        
        user_id = current_user.id
        print("User ID:", user_id)

        meal_name = data.get('meal_name')
        print("Meal name:", meal_name) 

        serving_count = data.get('serving_count')
        print("Serving count:", serving_count) 

        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        print("Timestamp:", timestamp) 

        path_to_image = data.get('path_to_image')
        print("Path to image:", path_to_image)  

        nutritional_data = data.get('nutritional_data')

        print("Parsed data:", meal_name, serving_count, nutritional_data) 

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        scaled_nutritional_data = {key: float(value) * 1 for key, value in nutritional_data.items()}
        
        cursor.execute('''
            INSERT INTO diary_meal_entries (
                user_id, meal_name, SUGAR_added_g, CA_mg, CHOCDF_net_g, CHOCDF_g, CHOLE_mg, 
                ENERC_KCAL_kcal, FAMS_g, FAPU_g, FASAT_g, FATRN_g, FIBTG_g, FOLDFE_microg, FOLFD_microg, 
                FOLAC_microg, FE_mg, MG_mg, NIA_mg, P_mg, K_mg, PROCNT_g, RIBF_mg, NA_mg, SUGAR_ALCOHOL_g, 
                SUGAR_g, THIA_mg, FAT_g, VITA_RAE_microg, VITB12_microg, VITB6A_mg, VITC_mg, VITD_microg, 
                TOCPHA_mg, VITK_microg, WATER_g, ZN_mg, timestamp, path_to_image, serving_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, meal_name, scaled_nutritional_data['SUGAR_added_g'], scaled_nutritional_data['CA_mg'], 
            scaled_nutritional_data['CHOCDF_net_g'], scaled_nutritional_data['CHOCDF_g'], scaled_nutritional_data['CHOLE_mg'], 
            scaled_nutritional_data['ENERC_KCAL_kcal'], scaled_nutritional_data['FAMS_g'], scaled_nutritional_data['FAPU_g'], 
            scaled_nutritional_data['FASAT_g'], scaled_nutritional_data['FATRN_g'], scaled_nutritional_data['FIBTG_g'], 
            scaled_nutritional_data['FOLDFE_microg'], scaled_nutritional_data['FOLFD_microg'], scaled_nutritional_data['FOLAC_microg'], 
            scaled_nutritional_data['FE_mg'], scaled_nutritional_data['MG_mg'], scaled_nutritional_data['NIA_mg'], 
            scaled_nutritional_data['P_mg'], scaled_nutritional_data['K_mg'], scaled_nutritional_data['PROCNT_g'], 
            scaled_nutritional_data['RIBF_mg'], scaled_nutritional_data['NA_mg'], scaled_nutritional_data['SUGAR_ALCOHOL_g'], 
            scaled_nutritional_data['SUGAR_g'], scaled_nutritional_data['THIA_mg'], scaled_nutritional_data['FAT_g'], 
            scaled_nutritional_data['VITA_RAE_microg'], scaled_nutritional_data['VITB12_microg'], 
            scaled_nutritional_data['VITB6A_mg'], scaled_nutritional_data['VITC_mg'], scaled_nutritional_data['VITD_microg'], 
            scaled_nutritional_data['TOCPHA_mg'], scaled_nutritional_data['VITK_microg'], 
            scaled_nutritional_data['WATER_g'], scaled_nutritional_data['ZN_mg'], timestamp, path_to_image, serving_count
        ))
        print("Inserted into database")

        conn.commit()
        conn.close()

        return jsonify({"status": "success", "message": "Meal added to diary!"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    
if __name__ == '__main__':
    app.run(debug=True)