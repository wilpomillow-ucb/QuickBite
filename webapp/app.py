from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    session,
    jsonify,
    g,
)
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
import bcrypt
from email_validator import validate_email, EmailNotValidError
from datetime import datetime, timezone, timedelta
import os
from inference_sdk import InferenceHTTPClient
import requests
from dotenv import load_dotenv
import json
from openai import OpenAI
import base64
from io import BytesIO
from pydantic import BaseModel
from enum import Enum
from PIL import Image
from aws_advanced_python_wrapper import AwsWrapperConnection
from mysql.connector import Connect

# Load environment variables from .env file
load_dotenv()

# Retrieve the API key from the environment variable
rb_api_key = os.environ.get("ROBOFLOW_API_KEY")
edamam_api_key = os.environ.get("EDAMAM_API_KEY")
openai_api_key = os.environ.get("OPENAI_API_KEY")
ENABLE_DEIT = True

# Check if the API key is set
if not (rb_api_key and edamam_api_key):
    raise ValueError("Please check that api keys were set in environment variable.")

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

CLIENT = InferenceHTTPClient(
    api_url="https://classify.roboflow.com", api_key=rb_api_key
)

# GPT-4o setup
OPENAI_CLIENT = OpenAI(api_key=openai_api_key)

CLASSES = [
    "chocolate_mousse",
    "panna_cotta",
    "churro",
    "creme_brulee",
    "dumpling",
    "macaroni_and_cheese",
    "boiled_egg",
    "risotto",
    "gnocchi",
    "macaron",
    "cannoli",
    "linguine",
    "eggs_benedict",
    "burrito",
    "apple_pie",
    "grilled_cheese_sandwich",
    "onion_rings",
    "ice_cream",
    "edamame",
    "fried_rice",
    "filet_mignon",
    "tempura",
    "lasagna",
    "donut",
    "pancake",
]

classes_text = "\n".join(CLASSES)

PROMPT = f"""
Classify the following image into one of the following categories. Return the category name.
{classes_text}
"""

PROMPT_NO_CLASSES = "What meal is in this image? Keep your answer to less than a few words, I want just the meal name."

PREFERENCES = [
    "Vegetarian",
    "Vegan",
    "Gluten-Free",
    "Peanut-Free",
]
DEFAULT_PREFERENCES = {preference: False for preference in PREFERENCES}

GOALS = ["Calories", "Carbs", "Proteins", "Fats"]

DEFAULT_GOALS = {goal: 0 for goal in GOALS}

app = Flask(__name__, static_folder="static")
app.secret_key = "your_secret_key"
login_manager = LoginManager(app)

## Turn on if we want to use CSRF protection
# from flask_wtf.csrf import CSRFProtect
# csrf = CSRFProtect(app)

# Connect to turso and setup a local replica of the database
DB_HOST = os.environ.get("DB_HOST")
DB_USERNAME = os.environ.get("DB_USERNAME")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_CONNECTION = AwsWrapperConnection.connect(
    Connect,
    f"host={DB_HOST} database=quickbite user={DB_USERNAME} password={DB_PASSWORD}",
    plugins="failover",
    wrapper_dialect="aurora-mysql",
    autocommit=True,
)


def get_db():
    return DB_CONNECTION


# Setup database
conn = get_db()
cursor = conn.cursor()
cursor.execute(
    f"""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    signup_time VARCHAR(255) NOT NULL,
    nutrition_preferences TEXT
    goals TEXT DEFAULT '{json.dumps(DEFAULT_GOALS)}'
)
"""
)
# DEFAULT '{json.dumps(DEFAULT_PREFERENCES)}'
cursor.execute(
    """
CREATE TABLE if not exists diary_meal_entries (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id         INTEGER NOT NULL,
    meal_name       VARCHAR(255)    NOT NULL,
    SUGAR_added_g   INTEGER,
    CA_mg           INTEGER,
    CHOCDF_net_g    INTEGER,
    CHOCDF_g        INTEGER,
    CHOLE_mg        INTEGER,
    ENERC_KCAL_kcal INTEGER,
    FAMS_g          INTEGER,
    FAPU_g          INTEGER,
    FASAT_g         INTEGER,
    FATRN_g         INTEGER,
    FIBTG_g         INTEGER,
    FOLDFE_microg   INTEGER,
    FOLFD_microg    INTEGER,
    FOLAC_microg    INTEGER,
    FE_mg           INTEGER,
    MG_mg           INTEGER,
    NIA_mg          INTEGER,
    P_mg            INTEGER,
    K_mg            INTEGER,
    PROCNT_g        INTEGER,
    RIBF_mg         INTEGER,
    NA_mg           INTEGER,
    SUGAR_ALCOHOL_g INTEGER,
    SUGAR_g         INTEGER,
    THIA_mg         INTEGER,
    FAT_g           INTEGER,
    VITA_RAE_microg INTEGER,
    VITB12_microg   INTEGER,
    VITB6A_mg       INTEGER,
    VITC_mg         INTEGER,
    VITD_microg     INTEGER,
    TOCPHA_mg       INTEGER,
    VITK_microg     INTEGER,
    WATER_g         INTEGER,
    ZN_mg           INTEGER,
    timestamp       VARCHAR(255)    NOT NULL,
    path_to_image   VARCHAR(255),
    serving_count   INTEGER
);
"""
)
conn.commit()


def classify_image_yolov8(image_path):
    result = CLIENT.infer(image_path, model_id="food-classification-rtszh/4")
    return result


FoodCategory = Enum("FoodCategory", CLASSES)


class ClassificationOutput(BaseModel):
    category_name: str


def encode_image(image):
    # resize to 512x512
    image = image.resize((512, 512))

    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    image_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/jpeg;base64,{image_str}"


def classify_image_gpt_4o(image_path):
    image = Image.open(image_path)

    response = OPENAI_CLIENT.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": encode_image(image),
                            "detail": "high",
                        },
                    },
                ],
            }
        ],
        max_tokens=300,
        response_format=ClassificationOutput,
    )

    return {
        "predictions": [{"class": response.choices[0].message.parsed.category_name}]
    }


def classify_image_gpt_4o_no_classes(image_path):
    image = Image.open(image_path)

    response = OPENAI_CLIENT.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT_NO_CLASSES},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": encode_image(image),
                            "detail": "high",
                        },
                    },
                ],
            }
        ],
        max_tokens=300,
    )

    print(response)

    return {"predictions": [{"class": response.choices[0].message.content}]}


# Init deit model
if ENABLE_DEIT:
    import torch
    from PIL import Image
    import numpy as np
    from torchvision import transforms

    deit_model = torch.load("../data/models/deit_model.pth", weights_only=False)
    deit_model.eval()

    transform = transforms.Normalize(
        mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
    )

    # Load classes for the deit model
    with open("./class_list.txt") as f:
        deit_classes = f.readlines()
        deit_classes = {
            int(a): b for [a, b] in [line.strip().split(" ") for line in deit_classes]
        }


def classify_image_deit(image_path):
    img = Image.open("../data/edamame.png")
    img = img.resize((224, 224))
    img = img.convert("RGB")
    img = np.array(img)
    img = img / 255.0
    img = np.transpose(img, (2, 0, 1))
    img = torch.tensor(img, dtype=torch.float32)
    img = transform(img)
    img = img.unsqueeze(0)

    output = deit_model(img)
    top3_indices = torch.topk(output, 3).indices.squeeze(0).tolist()
    top3_classes = [deit_classes[idx].replace("_", " ").title() for idx in top3_indices]

    return {"predictions": [{"class": cls} for cls in top3_classes]}


def recipe_search(food_query):
    API_KEY = edamam_api_key
    APP_ID = "2a940906"
    result = requests.get(
        f"https://api.edamam.com/api/recipes/v2?type=public&q={food_query}&app_id={APP_ID}&app_key={API_KEY}"
    )
    data = result.json()
    return data


def get_next_image_name():
    existing_files = os.listdir(UPLOAD_FOLDER)
    index = 0
    while True:
        filename = f"uploaded_image_{index}.png"
        if filename not in existing_files:
            return os.path.join(UPLOAD_FOLDER, filename)
        index += 1


def get_nutrition_preferences(db, user_id):
    cursor = db.cursor()
    cursor.execute("SELECT nutrition_preferences FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    raw_preferences = json.loads(user_data[0]) if user_data[0] else {}
    return {
        preference: raw_preferences.get(preference, False) is not False
        for preference in PREFERENCES
    }


def get_goals(db, user_id):
    cursor = db.cursor()
    cursor.execute("SELECT goals FROM users WHERE id = ?", (user_id,))
    user_data = cursor.fetchone()
    raw_goals = json.loads(user_data[0]) if user_data[0] else {}
    return {goal: raw_goals.get(goal, "0") for goal in GOALS}


# User Model for Flask-Login (Test user: test@test.com, pass:testtest)
class User(UserMixin):
    def __init__(self, id, email, password, signup_time, nutrition_preferences, goals):
        self.id = id
        self.email = email
        self.password = password
        self.signup_time = signup_time
        self.nutrition_preferences = nutrition_preferences
        self.goals = goals


@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    cursor = db.cursor()
    print("User ID:", user_id)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        return User(*user_data)
    return None


def validate_email_password(email, password):
    try:
        validate_email(email)
    except EmailNotValidError:
        flash("Invalid email format.", "error")
        return False

    if len(password) < 8:
        flash("Password must be at least 8 characters long.", "error")
        return False

    return True


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        action = request.form.get("action")
        print(action)

        db = get_db()
        cursor = db.cursor()

        if action == "login":
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user_data = cursor.fetchone()
            if user_data and bcrypt.checkpw(
                password.encode("utf-8"), user_data[2].encode("utf-8")
            ):
                user = User(
                    user_data[0],
                    user_data[1],
                    user_data[2],
                    user_data[3],
                    user_data[4],
                    user_data[5],
                )
                login_user(user)
                session["user_id"] = user_data[0]
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid login credentials.", "error")

        elif action == "signup":
            if validate_email_password(email, password):
                hashed_password = bcrypt.hashpw(
                    password.encode("utf-8"), bcrypt.gensalt()
                )
                signup_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                try:
                    cursor.execute(
                        "INSERT INTO users (email, password, signup_time) VALUES (%s, %s, %s)",
                        (email, hashed_password, signup_time),
                    )
                    db.commit()
                    flash("Account created! You can now log in.", "success")
                    return redirect(url_for("home"))
                except ValueError:  # TODO: check the exception type
                    flash("Email already exists.", "error")
                except Exception as e:
                    flash("An error occurred. Please try again.", "error")
                    print(e)
    return render_template("home.html")


@app.route("/dashboard")
@login_required
def dashboard():

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """SELECT *, ENERC_KCAL_kcal as calories, 
                   PROCNT_g as protein, CHOCDF_g as carbs, FAT_g as fat, timestamp FROM diary_meal_entries 
                   WHERE user_id = %s ORDER BY datetime(timestamp) DESC""",
        (current_user.id,),
    )
    meals = cursor.fetchall()

    # Get the last 7 days of diary entries
    seven_days_ago = datetime.now() - timedelta(days=7)
    cursor.execute(
        """
        SELECT strftime('%Y-%m-%d', timestamp) AS day, 
               SUM(ENERC_KCAL_kcal) AS calories,
               SUM(PROCNT_g) as protein, 
               SUM(CHOCDF_g) as carbs, 
               SUM(FAT_g) as fat
        FROM diary_meal_entries 
        WHERE user_id = %s AND timestamp >= %s 
        GROUP BY day 
        ORDER BY day DESC
    """,
        (current_user.id, seven_days_ago),
    )
    meals_last_7_days = cursor.fetchall()

    # Get the nutrients of all meals of the day
    # nedd to match DATE(TIMESTAMP) to python version of "date"
    # today = datetime.now().date()
    cursor.execute(
        """
        WITH current_user_diary_meal_entries AS (
        SELECT * FROM diary_meal_entries 
        WHERE user_id = ? AND DATE(timestamp) = DATE()
        )
        , current_user_table as (
        SELECT * FROM users
        WHERE id = ?
        )
        , today_nutrients AS (
        SELECT
        'Calories' AS nutrients, 
        SUM(ENERC_KCAL_kcal) AS daily_calories
        FROM current_user_diary_meal_entries
        GROUP BY 1 
        UNION
        SELECT
        'Proteins' AS nutrients, 
        SUM(PROCNT_g)*4/SUM(ENERC_KCAL_kcal)*100 as daily_protein_pct
        FROM current_user_diary_meal_entries 
        GROUP BY 1
        UNION
        SELECT
        'Carbs' AS nutrients, 
        SUM(CHOCDF_g)*4/SUM(ENERC_KCAL_kcal)*100 as daily_carbs_pct
        FROM current_user_diary_meal_entries 
        GROUP BY 1
        UNION 
        SELECT
        'Fats' AS nutrients, 
        SUM(FAT_g)*9/SUM(ENERC_KCAL_kcal)*100 as daily_fat_pct
        FROM current_user_diary_meal_entries
        GROUP BY 1
        ) 
        , daily_goals as (
        SELECT KEY AS nutrients, value AS set_goals
        FROM current_user_table, json_each(goals)
        ) 
        SELECT b.nutrients, 
        ROUND(COALESCE(a.daily_calories,0),2) AS daily_calories, 
        CAST(b.set_goals AS INTEGER) AS set_goals,
        ROUND(COALESCE(a.daily_calories,0)/NULLIF(CAST(b.set_goals AS INTEGER),0)*100,2) AS pct_of_goal
        FROM daily_goals b  
        LEFT JOIN today_nutrients a ON
            a.nutrients = b.nutrients 
    """,
        (
            current_user.id,
            current_user.id,
        ),
    )
    goals = cursor.fetchall()

    # Pass the meals to the dashboard template
    return render_template(
        "dashboard.html",
        user=current_user,
        meals=meals,
        user_id=current_user.id,
        meals_last_7_days=json.dumps(meals_last_7_days),
        goals=json.dumps(goals),
    )


PREFERENCES = [
    "Vegetarian",
    "Vegan",
    "Gluten-Free",
    "Peanut-Free",
]


@app.route("/preferences", methods=["GET", "POST"])
@login_required
def preferences():
    db = get_db()

    if request.method == "POST":
        preferences_form = request.form.to_dict()
        preferences = {
            preference: preferences_form.get(preference) == "on"
            for preference in PREFERENCES
        }

        print("Saving preferences:", preferences)

        # Save the user's preferences
        cursor = db.cursor()
        cursor.execute(
            "UPDATE users SET nutrition_preferences = %s WHERE id = %s",
            (json.dumps(preferences), current_user.id),
        )
        db.commit()

        flash("Preferences saved!", "success")

    # Load the user's preferences
    preferences = get_nutrition_preferences(db, current_user.id)
    print("Loaded preferences:", preferences)

    return render_template("preferences.html", preferences=preferences)


GOALS = ["Calories", "Carbs", "Proteins", "Fats"]


@app.route("/goals", methods=["GET", "POST"])
@login_required
def goals():
    db = get_db()

    if request.method == "POST":
        goals_form = request.form.to_dict()
        print("GOALS FORM:", goals_form)
        goals = {goal: goals_form.get(goal) for goal in GOALS}

        print("Saving goals:", goals)

        # Save the user's goals
        cursor = db.cursor()
        cursor.execute(
            "UPDATE users SET goals = ? WHERE id = ?",
            (json.dumps(goals), current_user.id),
        )
        db.commit()

        # flash("Goals saved!", "success")

    # # Load the user's goals
    goals = get_goals(db, current_user.id)
    # goals = {}
    print("Loaded goals:", goals)
    db.close()

    return render_template("goals.html", goals=goals)


@app.route("/get_user_id")
@login_required
def get_user_id():
    return jsonify({"user_id": session.get("user_id")})


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


# About Us page route
@app.route("/about-us")
def about_us():
    return render_template("about_us.html")


# Premium page route
@app.route("/premium")
def premium():
    return render_template("premium.html")


# Contact Us page route
@app.route("/contact-us", methods=["GET", "POST"])
def contact_us():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        message = request.form["message"]
        flash("Thank you for your feedback!", "success")
        return redirect(url_for("contact_us"))
    return render_template("contact_us.html")


# Submit feedback route
@app.route("/submit-feedback", methods=["POST"])
def submit_feedback():
    name = request.form["name"]
    email = request.form["email"]
    message = request.form["message"]
    flash("Feedback submitted successfully.", "success")
    return redirect(url_for("contact_us"))


# Route to handle the image upload and prediction
@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file part"})

    model = request.form["model"]
    if model == "yolov8":
        classify_image = classify_image_yolov8
    elif model == "deit":
        classify_image = classify_image_deit
    elif model == "gpt-4o":
        classify_image = classify_image_gpt_4o
    elif model == "gpt-4o-no-classes":
        classify_image = classify_image_gpt_4o_no_classes
    else:
        return jsonify({"status": "error", "message": "Invalid model"})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "No selected file"})

    image_path = get_next_image_name()
    file.save(image_path)
    predictions = [
        item["class"].replace("_", " ").title()
        for item in classify_image(image_path)["predictions"][0:3]
    ]
    return jsonify(
        {"status": "success", "image_path": image_path, "predictions": predictions}
    )


@app.route("/get_image_path")
@login_required
def get_image_path():
    meal_id = request.args.get("meal_id")
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM diary_meal_entries WHERE id = %s LIMIT 1", (meal_id,))
    result = cursor.fetchone()

    if result:
        return jsonify(
            {"status": "success", "image_path": result[-2], "image_time": result[-1]}
        )
    else:
        return jsonify({"status": "error", "message": "Image not found"})


# Route to handle the POST request for adding to the diary
@app.route("/add_to_diary", methods=["POST"])
def add_to_diary():
    try:
        data = request.json
        print("Received data:", data)

        user_id = current_user.id
        print("User ID:", user_id)

        meal_name = data.get("meal_name")
        print("Meal name:", meal_name)

        serving_count = data.get("serving_count")
        print("Serving count:", serving_count)

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        print("Timestamp:", timestamp)

        path_to_image = data.get("path_to_image")
        print("Path to image:", path_to_image)

        nutritional_data = data.get("nutritional_data")

        print("Parsed data:", meal_name, serving_count, nutritional_data)

        conn = get_db()
        cursor = conn.cursor()

        scaled_nutritional_data = {
            key: float(value) * 1 for key, value in nutritional_data.items()
        }

        cursor.execute(
            """
            INSERT INTO diary_meal_entries (
                user_id, meal_name, SUGAR_added_g, CA_mg, CHOCDF_net_g, CHOCDF_g, CHOLE_mg, 
                ENERC_KCAL_kcal, FAMS_g, FAPU_g, FASAT_g, FATRN_g, FIBTG_g, FOLDFE_microg, FOLFD_microg, 
                FOLAC_microg, FE_mg, MG_mg, NIA_mg, P_mg, K_mg, PROCNT_g, RIBF_mg, NA_mg, SUGAR_ALCOHOL_g, 
                SUGAR_g, THIA_mg, FAT_g, VITA_RAE_microg, VITB12_microg, VITB6A_mg, VITC_mg, VITD_microg, 
                TOCPHA_mg, VITK_microg, WATER_g, ZN_mg, timestamp, path_to_image, serving_count
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
            (
                user_id,
                meal_name,
                scaled_nutritional_data["SUGAR_added_g"],
                scaled_nutritional_data["CA_mg"],
                scaled_nutritional_data["CHOCDF_net_g"],
                scaled_nutritional_data["CHOCDF_g"],
                scaled_nutritional_data["CHOLE_mg"],
                scaled_nutritional_data["ENERC_KCAL_kcal"],
                scaled_nutritional_data["FAMS_g"],
                scaled_nutritional_data["FAPU_g"],
                scaled_nutritional_data["FASAT_g"],
                scaled_nutritional_data["FATRN_g"],
                scaled_nutritional_data["FIBTG_g"],
                scaled_nutritional_data["FOLDFE_microg"],
                scaled_nutritional_data["FOLFD_microg"],
                scaled_nutritional_data["FOLAC_microg"],
                scaled_nutritional_data["FE_mg"],
                scaled_nutritional_data["MG_mg"],
                scaled_nutritional_data["NIA_mg"],
                scaled_nutritional_data["P_mg"],
                scaled_nutritional_data["K_mg"],
                scaled_nutritional_data["PROCNT_g"],
                scaled_nutritional_data["RIBF_mg"],
                scaled_nutritional_data["NA_mg"],
                scaled_nutritional_data["SUGAR_ALCOHOL_g"],
                scaled_nutritional_data["SUGAR_g"],
                scaled_nutritional_data["THIA_mg"],
                scaled_nutritional_data["FAT_g"],
                scaled_nutritional_data["VITA_RAE_microg"],
                scaled_nutritional_data["VITB12_microg"],
                scaled_nutritional_data["VITB6A_mg"],
                scaled_nutritional_data["VITC_mg"],
                scaled_nutritional_data["VITD_microg"],
                scaled_nutritional_data["TOCPHA_mg"],
                scaled_nutritional_data["VITK_microg"],
                scaled_nutritional_data["WATER_g"],
                scaled_nutritional_data["ZN_mg"],
                timestamp,
                path_to_image,
                serving_count,
            ),
        )
        print("Inserted into database")

        conn.commit()

        return jsonify({"status": "success", "message": "Meal added to diary!"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
