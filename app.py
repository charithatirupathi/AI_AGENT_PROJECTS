from flask import Flask, request, render_template, send_file, jsonify
import os
import uuid
from pydub import AudioSegment
import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS

# Create Flask app
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Convert MP3 to WAV
def convert_mp3_to_wav(mp3_path, wav_path):
    audio = AudioSegment.from_mp3(mp3_path)
    audio.export(wav_path, format='wav')

# Recognize and auto-detect Telugu or English
def recognize_speech(wav_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language='te-IN')
            return text, 'te', 'en'
        except sr.UnknownValueError:
            text = recognizer.recognize_google(audio_data, language='en-IN')
            return text, 'en', 'te'

# Translate text
def translate_text(text, src_lang, dest_lang):
    translator = Translator()
    translated = translator.translate(text, src=src_lang, dest=dest_lang)
    return translated.text

# Convert text to speech
def text_to_speech(text, lang, output_path):
    tts = gTTS(text=text, lang=lang)
    tts.save(output_path)

# Homepage
@app.route('/')
def home():
    return render_template('index.html')

# Handle translation
@app.route('/translate', methods=['POST'])
def translate_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file uploaded'}), 400

    file = request.files['audio']
    unique_id = uuid.uuid4().hex
    mp3_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}.mp3")
    wav_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}.wav")
    output_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}_translated.mp3")

    file.save(mp3_path)

    try:
        convert_mp3_to_wav(mp3_path, wav_path)
        text, src_lang, dest_lang = recognize_speech(wav_path)
        translated_text = translate_text(text, src_lang, dest_lang)
        text_to_speech(translated_text, dest_lang, output_path)
        return send_file(output_path, as_attachment=False)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        for path in [mp3_path, wav_path]:
            if os.path.exists(path):
                os.remove(path)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
