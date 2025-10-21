from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import spacy
import json
import os
import sqlite3
from datetime import datetime, timedelta
import requests
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'medical-chatbot-secret-key-2024'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

# Database initialization
def init_db():
    conn = sqlite3.connect('medical_chat.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  language TEXT DEFAULT 'en',
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Chat history table
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  user_input TEXT,
                  bot_response TEXT,
                  symptoms_detected TEXT,
                  conditions_found TEXT,
                  language TEXT DEFAULT 'en',
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Appointments table
    c.execute('''CREATE TABLE IF NOT EXISTS appointments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  doctor_name TEXT,
                  appointment_date DATETIME,
                  reason TEXT,
                  status TEXT DEFAULT 'pending',
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Create default admin user
    try:
        c.execute('INSERT OR IGNORE INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                 ('admin', 'admin@medical.com', generate_password_hash('admin123')))
    except:
        pass
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('medical_chat.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return User(id=user[0], username=user[1], email=user[2])
    return None

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model...")
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Enhanced medical database with symptom weights
medical_data = {
    "symptoms": {
        "headache": {
            "conditions": ["common cold", "flu", "migraine", "tension headache", "sinusitis"],
            "weight": 1
        },
        "fever": {
            "conditions": ["common cold", "flu", "infection", "strep throat", "pneumonia"],
            "weight": 2
        },
        "cough": {
            "conditions": ["common cold", "flu", "bronchitis", "pneumonia", "allergies", "covid"],
            "weight": 1
        },
        "sneezing": {
            "conditions": ["common cold", "flu", "allergies"],
            "weight": 1
        },
        "fatigue": {
            "conditions": ["common cold", "flu", "stress", "lack of sleep", "anemia", "covid"],
            "weight": 1
        },
        "nausea": {
            "conditions": ["flu", "food poisoning", "stomach virus", "migraine", "pregnancy"],
            "weight": 2
        },
        "vomiting": {
            "conditions": ["flu", "food poisoning", "stomach virus", "motion sickness"],
            "weight": 2
        },
        "diarrhea": {
            "conditions": ["stomach virus", "food poisoning", "irritable bowel syndrome", "lactose intolerance"],
            "weight": 2
        },
        "rash": {
            "conditions": ["allergies", "chickenpox", "measles", "eczema", "poison ivy"],
            "weight": 2
        },
        "dizziness": {
            "conditions": ["dehydration", "inner ear infection", "low blood sugar", "vertigo"],
            "weight": 2
        },
        "shortness of breath": {
            "conditions": ["asthma", "pneumonia", "covid", "heart problems"],
            "weight": 3
        },
        "chest pain": {
            "conditions": ["heart attack", "angina", "pneumonia", "anxiety"],
            "weight": 3
        }
    },
    "recommendations": {
        "common cold": "Rest, stay hydrated, and consider over-the-counter medications for symptom relief.",
        "flu": "Rest, stay hydrated, and consider over-the-counter medications for symptom relief.",
        "migraine": "Rest in a quiet, dark room. Apply a cold compress to your forehead.",
        "tension headache": "Apply a warm compress to your neck and shoulders. Practice stress management techniques.",
        "sinusitis": "Use a humidifier or saline nasal spray. Consider decongestants.",
        "infection": "Consult a doctor for diagnosis and appropriate treatment.",
        "strep throat": "Consult a doctor for diagnosis and antibiotics.",
        "allergies": "Identify and avoid allergens. Consider antihistamines.",
        "bronchitis": "Rest, stay hydrated, and use a humidifier.",
        "pneumonia": "Consult a doctor for diagnosis and appropriate treatment.",
        "covid": "Self-isolate, consult a doctor, and monitor symptoms.",
        "heart attack": "Seek immediate medical attention! Call emergency services.",
        "asthma": "Use your prescribed inhaler. Avoid triggers."
    },
    "emergency_conditions": ["heart attack", "pneumonia", "covid"]
}

# Medical assistant functions
def extract_symptoms(user_input):
    doc = nlp(user_input)
    extracted_symptoms = []
    
    # Check for single word symptoms
    for token in doc:
        symptom = token.text.lower()
        if symptom in medical_data["symptoms"] and symptom not in extracted_symptoms:
            extracted_symptoms.append(symptom)
    
    # Check for multi-word symptoms
    for symptom in medical_data["symptoms"]:
        if ' ' in symptom and symptom in user_input.lower():
            if symptom not in extracted_symptoms:
                extracted_symptoms.append(symptom)
    
    return extracted_symptoms

def analyze_symptoms(extracted_symptoms):
    possible_conditions = {}
    for symptom in extracted_symptoms:
        if symptom in medical_data["symptoms"]:
            conditions = medical_data["symptoms"][symptom]["conditions"]
            weight = medical_data["symptoms"][symptom]["weight"]
            
            for condition in conditions:
                if condition in possible_conditions:
                    possible_conditions[condition] += weight
                else:
                    possible_conditions[condition] = weight
    return possible_conditions

def generate_response(extracted_symptoms, possible_conditions, language='en'):
    response = ""
    
    # Check for emergency conditions
    emergency_found = any(condition in medical_data["emergency_conditions"] 
                         for condition in possible_conditions.keys())
    
    if emergency_found:
        if language == 'ar':
            response += "<div class='emergency-alert'>🚨 حالة طارئة! يرجى طلب المساعدة الطبية فوراً!</div><br>"
        else:
            response += "<div class='emergency-alert'>🚨 Emergency! Please seek immediate medical attention!</div><br>"
    
    if extracted_symptoms:
        if language == 'ar':
            response += f"<strong>الأعراض المكتشفة:</strong> {', '.join(extracted_symptoms)}<br>"
            response += "<strong>الاحتمالات:</strong>"
        else:
            response += f"<strong>Detected Symptoms:</strong> {', '.join(extracted_symptoms)}<br>"
            response += "<strong>Possible Conditions:</strong>"
        
        if possible_conditions:
            sorted_conditions = sorted(possible_conditions.items(), key=lambda item: item[1], reverse=True)
            for condition, score in sorted_conditions[:5]:
                response += f"<div class='condition-item'>"
                response += f"<strong>{condition}</strong> (confidence score: {score})"
                if condition in medical_data["recommendations"]:
                    recommendation = medical_data["recommendations"][condition]
                    response += f"<br><em>💡 {recommendation}</em>"
                response += "</div>"
        else:
            if language == 'ar':
                response += "<br>لم أتعرف على هذه الأعراض."
            else:
                response += "<br>I don't recognize these symptoms."
    else:
        if language == 'ar':
            response = "لم أتعرف على أي أعراض في وصفك."
        else:
            response = "I didn't recognize any symptoms in your description."
    
    if language == 'ar':
        response += "<br><div class='disclaimer'>⚠️ تذكير: أنا مجرد مساعد ذكي ولا أستطيع تقديم تشخيص طبي نهائي. يرجى استشارة طبيب للتشخيص والعلاج المناسب.</div>"
    else:
        response += "<br><div class='disclaimer'>⚠️ Remember: I am just an AI assistant and cannot provide definitive medical advice. Please consult a doctor for proper diagnosis and treatment.</div>"
    
    return response

def save_chat_history(user_id, user_input, bot_response, symptoms, conditions, language='en'):
    conn = sqlite3.connect('medical_chat.db')
    c = conn.cursor()
    c.execute('''INSERT INTO chat_history 
                 (user_id, user_input, bot_response, symptoms_detected, conditions_found, language) 
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (user_id, user_input, bot_response, ','.join(symptoms), ','.join(conditions.keys()), language))
    conn.commit()
    conn.close()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ar')
def index_ar():
    return render_template('arabic/index_ar.html')

@app.route('/set_language/<lang>')
def set_language(lang):
    session['language'] = lang
    return redirect(request.referrer or url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        language = request.form.get('language', 'en')
        
        conn = sqlite3.connect('medical_chat.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):
            user_obj = User(id=user[0], username=user[1], email=user[2])
            login_user(user_obj)
            
            # Update user language preference
            conn = sqlite3.connect('medical_chat.db')
            c = conn.cursor()
            c.execute('UPDATE users SET language = ? WHERE id = ?', (language, user[0]))
            conn.commit()
            conn.close()
            
            return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        language = request.form.get('language', 'en')
        
        conn = sqlite3.connect('medical_chat.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, email, password_hash, language) VALUES (?, ?, ?, ?)',
                     (username, email, generate_password_hash(password), language))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            return "Username or email already exists"
    
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user language preference
    conn = sqlite3.connect('medical_chat.db')
    c = conn.cursor()
    c.execute('SELECT language FROM users WHERE id = ?', (current_user.id,))
    user_language = c.fetchone()[0]
    
    # Get chat history
    c.execute('SELECT * FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10', (current_user.id,))
    chat_history = c.fetchall()
    
    # Get appointments
    c.execute('SELECT * FROM appointments WHERE user_id = ? ORDER BY appointment_date DESC', (current_user.id,))
    appointments = c.fetchall()
    conn.close()
    
    if user_language == 'ar':
        return render_template('arabic/dashboard_ar.html', 
                             chat_history=chat_history, 
                             appointments=appointments,
                             username=current_user.username)
    else:
        return render_template('dashboard.html', 
                             chat_history=chat_history, 
                             appointments=appointments,
                             username=current_user.username)

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    user_input = request.json['message']
    language = request.json.get('language', 'en')
    
    extracted_symptoms = extract_symptoms(user_input)
    possible_conditions = analyze_symptoms(extracted_symptoms)
    response = generate_response(extracted_symptoms, possible_conditions, language)
    
    # Save to database
    save_chat_history(current_user.id, user_input, response, extracted_symptoms, possible_conditions, language)
    
    return jsonify({
        'response': response,
        'symptoms_found': extracted_symptoms,
        'conditions_found': list(possible_conditions.keys())
    })

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json()
    user_input = data.get('message', '')
    language = data.get('language', 'en')
    
    extracted_symptoms = extract_symptoms(user_input)
    possible_conditions = analyze_symptoms(extracted_symptoms)
    response = generate_response(extracted_symptoms, possible_conditions, language)
    
    return jsonify({
        'diagnosis': response,
        'symptoms': extracted_symptoms,
        'conditions': possible_conditions,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/book_appointment', methods=['POST'])
@login_required
def book_appointment():
    doctor_name = request.form['doctor_name']
    appointment_date = request.form['appointment_date']
    reason = request.form['reason']
    
    conn = sqlite3.connect('medical_chat.db')
    c = conn.cursor()
    c.execute('INSERT INTO appointments (user_id, doctor_name, appointment_date, reason) VALUES (?, ?, ?, ?)',
              (current_user.id, doctor_name, appointment_date, reason))
    conn.commit()
    conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)