from flask import Flask, render_template, request, jsonify
import spacy
import json
import os

app = Flask(__name__)

# تحميل نموذج spaCy
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model...")
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# قاعدة البيانات الطبية
medical_data = {
    "symptoms": {
        "headache": ["common cold", "flu", "migraine", "tension headache", "sinusitis"],
        "fever": ["common cold", "flu", "infection", "strep throat"],
        "cough": ["common cold", "flu", "bronchitis", "pneumonia", "allergies"],
        "sneezing": ["common cold", "flu", "allergies"],
        "fatigue": ["common cold", "flu", "stress", "lack of sleep", "anemia"],
        "nausea": ["flu", "food poisoning", "stomach virus", "migraine", "pregnancy"],
        "vomiting": ["flu", "food poisoning", "stomach virus", "motion sickness"],
        "diarrhea": ["stomach virus", "food poisoning", "irritable bowel syndrome", "lactose intolerance"],
        "rash": ["allergies", "chickenpox", "measles", "eczema", "poison ivy"],
        "dizziness": ["dehydration", "inner ear infection", "low blood sugar", "vertigo"]
    },
    "recommendations": {
        "common cold": "Rest, stay hydrated, and consider over-the-counter medications for symptom relief.",
        "flu": "Rest, stay hydrated, and consider over-the-counter medications for symptom relief.",
        "migraine": "Rest in a quiet, dark room. Apply a cold compress to your forehead.",
        "tension headache": "Apply a warm compress to your neck and shoulders. Practice stress management.",
        "sinusitis": "Use a humidifier or saline nasal spray. Consider decongestants.",
        "infection": "Consult a doctor for diagnosis and appropriate treatment.",
        "strep throat": "Consult a doctor for diagnosis and antibiotics.",
        "allergies": "Identify and avoid allergens. Consider antihistamines.",
        "bronchitis": "Rest, stay hydrated, and use a humidifier.",
        "pneumonia": "Consult a doctor for diagnosis and appropriate treatment."
    }
}

def extract_symptoms(user_input):
    doc = nlp(user_input)
    extracted_symptoms = []
    for token in doc:
        symptom = token.text.lower()
        if symptom in medical_data["symptoms"] and symptom not in extracted_symptoms:
            extracted_symptoms.append(symptom)
    return extracted_symptoms

def analyze_symptoms(extracted_symptoms):
    possible_conditions = {}
    for symptom in extracted_symptoms:
        if symptom in medical_data["symptoms"]:
            conditions = medical_data["symptoms"][symptom]
            for condition in conditions:
                if condition in possible_conditions:
                    possible_conditions[condition] += 1
                else:
                    possible_conditions[condition] = 1
    return possible_conditions

def generate_response(extracted_symptoms, possible_conditions):
    response = ""
    if extracted_symptoms:
        response += "I understand you have " + ", ".join(extracted_symptoms) + ".<br>"
        response += "<strong>Based on your symptoms, the most likely possibilities are:</strong>"
        
        if possible_conditions:
            sorted_conditions = sorted(possible_conditions.items(), key=lambda item: item[1], reverse=True)
            for condition, count in sorted_conditions:
                response += f"<div class='condition-item'><strong>{condition}</strong> ({count} matching symptom(s))"
                if condition in medical_data["recommendations"]:
                    recommendation = medical_data["recommendations"][condition]
                    response += f"<br><em>💡 Recommendation: {recommendation}</em>"
                response += "</div>"
        else:
            response += "<br>I'm sorry, I don't recognize those symptoms."
    else:
        response = "I'm sorry, I didn't recognize any symptoms in your description."
    
    response += "<br><br><div class='disclaimer'>⚠️ Remember, I am just a chatbot and cannot provide definitive medical advice. Please consult a doctor for proper diagnosis and treatment.</div>"
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json['message']
    
    extracted_symptoms = extract_symptoms(user_input)
    possible_conditions = analyze_symptoms(extracted_symptoms)
    response = generate_response(extracted_symptoms, possible_conditions)
    
    return jsonify({
        'response': response,
        'symptoms_found': extracted_symptoms
    })

if __name__ == '__main__':
    app.run(debug=True)