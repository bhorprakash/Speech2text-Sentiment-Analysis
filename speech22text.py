import speech_recognition as sr
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from flask import Flask, render_template, jsonify, request
import threading
from textblob import TextBlob


app = Flask(__name__)

recognizer = sr.Recognizer()
microphone = sr.Microphone()
listening = False
transcribed_text = ""
sentiment = ""
polarity = 0.0
subjectivity = 0.0

def analyze_sentiment(text):
    blob = TextBlob(text)
    
   
    polarity = blob.sentiment.polarity 
    subjectivity = blob.sentiment.subjectivity 
    
    if polarity > 0:
        sentiment = "Positive"
    elif polarity < 0:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"
    
    return sentiment, polarity, subjectivity

def continuous_listen():
    global listening, transcribed_text
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source) 
        print("Microphone is ready. Listening...")

        while listening:
            try:
                print("Listening for input...")
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)  
                text = recognizer.recognize_google(audio)
                print(f"Recognized: {text}")
                transcribed_text += text + " "
            except sr.UnknownValueError:
                print("Could not understand audio, skipping...")
            except sr.RequestError as e:
                print(f"API Error: {e}")
                break
            except Exception as e:
                print(f"Error: {e}")
                break

@app.route("/start", methods=["POST"])
def start_listening():
    global listening
    if listening:
        return jsonify({"success": False, "message": "Already listening!"})
    listening = True
    threading.Thread(target=continuous_listen).start()
    return jsonify({"success": True, "message": "Started listening!"})

@app.route("/stop", methods=["POST"])
def stop_listening():
    global listening
    if not listening:
        return jsonify({"success": False, "message": "Not currently listening!"})
    listening = False
    return jsonify({"success": True, "message": "Stopped listening!"})

@app.route("/save", methods=["POST"])
def save_pdf():
    global transcribed_text, sentiment, polarity, subjectivity
    if not transcribed_text.strip():
        return jsonify({"success": False, "message": "No text to save!"})

    sentiment, polarity, subjectivity = analyze_sentiment(transcribed_text)

    try:
        save_to_pdf(transcribed_text, sentiment, polarity, subjectivity, "static/transcription.pdf")
        return jsonify({"success": True, "message": "PDF saved!", "file_path": "/static/transcription.pdf"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

def save_to_pdf(text, sentiment, polarity, subjectivity, filename="transcription.pdf"):
    pdf = canvas.Canvas(filename, pagesize=A4)
    width, height = A4  

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 50, "Speech2Text Sentiment Analysis:")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 80, f"Sentiment: {sentiment}")
    pdf.drawString(50, height - 100, f"Polarity: {polarity}")
    pdf.drawString(50, height - 120, f"Subjectivity: {subjectivity}")

    y_position = height - 140
    pdf.setFont("Helvetica", 10)
    text_lines = text.splitlines()
    line_height = 12

    for line in text_lines:
        if y_position < 50:  
            pdf.showPage() 
            y_position = height - 50 
            pdf.setFont("Helvetica", 10)

        pdf.drawString(50, y_position, line)
        y_position -= line_height

    
    pdf.save()

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
