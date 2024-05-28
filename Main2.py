from flask import Flask, render_template, request, jsonify
from random import sample
import base64
import openai
import speech_recognition as sr
import pyttsx3
import os
from werkzeug.utils import secure_filename
from PIL import Image
from io import BytesIO
import sys
from elevenlabs.client import ElevenLabs
from elevenlabs import play
sys.stdout.reconfigure(encoding='utf-8')

# Declarando nombre de la aplicación e inicializando
app = Flask(__name__)
api_key = "OpenAi_Api_Key"
eleven_Api_key = "Eleven_Api_Key"

openai.api_key = api_key
client = ElevenLabs(
    api_key=eleven_Api_key
)

bucle = True

def text_to_speech(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 125)
    engine.setProperty('volume', 0.8)
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[3].id)
    engine.say(text)
    engine.runAndWait()

def encode_image(image_path):
    # Redimensionar la imagen si es demasiado grande y convertirla a modo RGB
    max_size = (512, 512)  # Tamaño máximo (ancho, alto)
    with Image.open(image_path) as img:
        img = img.convert("RGB")  # Convertir a modo RGB
        img.thumbnail(max_size)
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

def transcribe_audio_to_text(filename):
    recogizer = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio = recogizer.record(source)
    try:
        return recogizer.recognize_google(audio, language="es")
    except Exception as e:
        print(f"Error transcribiendo audio: {e}")
        return None
    

def generate_response(prompt, image_path):
    base64_image = encode_image(image_path)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages= [
            {"role": "system", "content": "Eres arrogante, molesta, clasista"},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
            max_tokens=300,  # Limitar el número de tokens en la respuesta
        )
        assistant_response = response['choices'][0]['message']['content']
        return assistant_response
    except Exception as e:
        print(f"Error al generar la respuesta: {e}")
        return "Lo siento, hubo un problema al generar la respuesta."

def decirEleven(decir):
    audio = client.generate(
        text = decir,
        voice =  "9F4C8ztpNUmXkdDDbz3J",
        #voice =  "Ky9j3wxFbp3dSAdrkOEv",
        model = "eleven_multilingual_v2"
    )
    play(audio)
    

@app.errorhandler(404)
def not_found(error):
    return 'Ruta no encontrada'

def stringAleatorio():
    string_aleatorio = "0123456789abcdefghijklmnopqrstuvwxyz_"
    longitud = 20
    secuencia = string_aleatorio.upper()
    resultado_aleatorio = sample(secuencia, longitud)
    string_aleatorio = "".join(resultado_aleatorio)
    return string_aleatorio

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('index.html')

@app.route('/registrar-archivo', methods=['GET', 'POST'])
def registarArchivo():
    global bucle
    if request.method == 'POST':
        bucle = True
        file = request.files['archivo']
        basepath = os.path.dirname(__file__)
        filename = secure_filename(file.filename)
        extension = os.path.splitext(filename)[1]
        nuevoNombreFile = stringAleatorio() + extension
        upload_path = os.path.join(basepath, 'static/archivos', nuevoNombreFile)
        file.save(upload_path)
        print("Iniciando")

        with sr.Microphone() as source:
            recognizer = sr.Recognizer()
            audio = recognizer.listen(source)
            try:
                transcription = recognizer.recognize_google(audio, language="es")
                filename = "input.wav"
                print("Buenas")
                decirEleven("Buenas")
                while bucle:
                    with sr.Microphone() as source:
                        recognizer = sr.Recognizer()
                        source.pause_threshold = 1
                        audio = recognizer.listen(source, phrase_time_limit=None, timeout=None)
                        with open(filename, "wb") as f:
                            f.write(audio.get_wav_data())

                    text = transcribe_audio_to_text(filename)
                    if text:
                        print(f"Prompt: {text}")
                        response = generate_response(text, upload_path)
                        if response:
                            respuesta_normal = response.encode('utf-8').decode('unicode-escape')
                            print(f"El bot ese dice: {respuesta_normal}")
                            decirEleven(respuesta_normal)

            except Exception as e:
                print(f"Ahhhhhh erroor : {e}")
    return render_template('index.html')

@app.route('/stop-loop', methods=['POST'])
def stop_loop():
    global bucle
    bucle = False
    return jsonify({"message": "Loop stopped"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
