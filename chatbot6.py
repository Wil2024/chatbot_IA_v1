from flask import Flask, request, render_template, session, redirect, url_for, jsonify
from flask_session import Session  # Asegúrate de importar Session de flask_session
import json
import nltk
from nltk.stem import WordNetLemmatizer
import random

app = Flask(__name__)
app.secret_key = "tu_secreto_muy_secreto"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

nltk.download('punkt')
nltk.download('wordnet')
lemmatizer = WordNetLemmatizer()

with open("intenciones.json", encoding='utf-8') as file:
    data = json.load(file)

def find_response(message):
    message = message.lower()
    message_words = nltk.word_tokenize(message)
    message_lemmas = [lemmatizer.lemmatize(word) for word in message_words]

    best_match = {"tag": "desconocido", "score": 0}
    for intent in data["intents"]:
        for pattern in intent.get("patterns", []):
            pattern_words = nltk.word_tokenize(pattern)
            pattern_lemmas = set([lemmatizer.lemmatize(word) for word in pattern_words])
            score = sum(1 for lemma in message_lemmas if lemma in pattern_lemmas)
            if score > best_match["score"]:
                best_match = {"tag": intent["tag"], "score": score}

    if best_match["tag"] == "desconocido":
        response = random.choice(["Lo siento, no entiendo tu pregunta. ¿Puedes reformularla?"])
    else:
        response = random.choice([resp for intent in data["intents"] if intent["tag"] == best_match["tag"] for resp in intent["responses"]])
    
    # Reemplaza los saltos de línea por <br> para HTML
    response = response.replace("\n", "<br>")
    return response

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'historial' not in session:
        session['historial'] = []

    if request.method == 'POST':
        message = request.form['message']
        response = find_response(message)
        
        # Aquí revisamos si es una solicitud AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Devuelve la respuesta del chatbot en formato JSON
            return jsonify({'respuesta': response})
        else:
            # Para solicitudes normales, agrega al historial y sigue el flujo existente
            session['historial'].append({'pregunta': message, 'respuesta': response})
            session.modified = True

    return render_template('chat_interface.html', historial=session['historial'])

@app.route('/reset', methods=['POST'])
def reset():
    session.pop('historial', None)
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
