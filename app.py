from flask import Flask, render_template, request , jsonify 
from keras.models import load_model
from PIL import Image
import numpy as np
import io
import base64
import re
from dotenv import load_dotenv
from openai import OpenAI
import os
import requests
from azure.storage.blob import BlobServiceClient
import json  # Assurez-vous d'importer le module json

connect_str = "DefaultEndpointsProtocol=https;AccountName=stockagemodel;AccountKey=07kKsQiv6rWRfehHJ85CZPtF22UIffhvN5dHkv8ZpICq2mJABmL8G9XVJOQH8zRSxo+2vblw5Nw0+AStkw56cA==;EndpointSuffix=core.windows.net"
container_name = "firstcontainer"
blob_name = "Model.h5"
file_path = "./Model.h5"

blob_service_client = BlobServiceClient.from_connection_string(connect_str)
blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

if not os.path.exists(file_path):
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    with open(file_path, "wb") as download_file:
        download_file.write(blob_client.download_blob().readall())

load_dotenv()

app = Flask(__name__)

# Charger le modèle
model = load_model('Model.h5')
class_names=['Apple___Apple_scab', 'Apple___Black_rot', 'Apple___Cedar_apple_rust', 'Apple___healthy', 'Blueberry___healthy', 'Cherry_(including_sour)___Powdery_mildew', 'Cherry_(including_sour)___healthy', 'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot', 'Corn_(maize)___Common_rust_', 'Corn_(maize)___Northern_Leaf_Blight', 'Corn_(maize)___healthy', 'Grape___Black_rot', 'Grape___Esca_(Black_Measles)', 'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)', 'Grape___healthy', 'Orange___Haunglongbing_(Citrus_greening)', 'Peach___Bacterial_spot', 'Peach___healthy', 'Pepper,_bell___Bacterial_spot', 'Pepper,_bell___healthy', 'Potato___Early_blight', 'Potato___Late_blight', 'Potato___healthy', 'Raspberry___healthy', 'Soybean___healthy', 'Squash___Powdery_mildew', 'Strawberry___Leaf_scorch', 'Strawberry___healthy', 'Tomato___Bacterial_spot', 'Tomato___Early_blight', 'Tomato___Late_blight', 'Tomato___Leaf_Mold', 'Tomato___Septoria_leaf_spot', 'Tomato___Spider_mites Two-spotted_spider_mite', 'Tomato___Target_Spot', 'Tomato___Tomato_Yellow_Leaf_Curl_Virus', 'Tomato___Tomato_mosaic_virus', 'Tomato___healthy']

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) 

thread_principal_id = None
assistant_principal_id = None
uploaded_file = None

@app.route('/')
def index_view():
    return render_template('index.html')

@app.route('/chat', methods=['POST','GET'])
def chat():
    return render_template('chat.html')  


@app.route('/get_chatbot_response', methods=['POST','GET'])
def get_chatbot_response():
    user_message_func(request.json['content'])
    return jsonify({"message":  run_func()})

def convertImage(imgData1):
    imgstr = re.search(b'base64,(.*)', imgData1).group(1)
    image_data = base64.b64decode(imgstr)
    img = Image.open(io.BytesIO(image_data))
    if img.mode != "RGB":
        img = img.convert("RGB")
    img = img.resize((256, 256))
    img_array = np.array(img)
    return img_array

@app.route('/predict/', methods=['GET', 'POST'])
def predict():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"})
        file = request.files['file']
        img = Image.open(file.stream)
        if img.mode != "RGB":
            img = img.convert("RGB")
        img = img.resize((256, 256))
        img_array = np.array(img)
        img_array = np.expand_dims(img_array, axis=0)
        out = model.predict(img_array)
        top_3_indices = np.argsort(out[0])[-3:][::-1]
        top_3_probabilities = out[0][top_3_indices]
        top_3_class_names = [class_names[i] for i in top_3_indices]
        response = {
            "predicted_class": class_names[np.argmax(out[0])],
            "top_3_predictions": {top_3_class_names[i]: float(top_3_probabilities[i]) for i in range(3)}
        }
        global thread_principal_id
        thread_principal_id = create_thread()
        
        formatted_json = json.dumps(response, indent=4)  # indent=4 pour une meilleure lisibilité

        # Écrire le JSON formaté dans App_results.txt
        with open('App_results.txt', 'w') as file:
            file.write(formatted_json)

        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')



@app.route('/predict2/', methods=['POST','GET'])
def predict2():
    try:
        # Lire l'image envoyée par l'utilisateur
        file = request.files['file'] 
        in_memory_file = io.BytesIO()
        file.save(in_memory_file)
        data = in_memory_file.getvalue()
        encoded_image = base64.b64encode(data).decode('utf-8')

        # Informations à envoyer
        url = 'https://plant.id/api/v3/identification'
        headers = {
            'Api-Key': os.getenv("PLANT_API_KEY"),
            'Content-Type': 'application/json'
        }
        body = {
            'images': [encoded_image],
            'latitude': 48.866,  # Paris
            'longitude': 2.333,  # Paris
            'similar_images': True
        }

        global thread_principal_id
        thread_principal_id = create_thread()

        response_identification = requests.post(url, json=body, headers=headers)
        identification_result = response_identification.json().get('result', {})
        formatted_identification = json.dumps(identification_result, indent=4)

        with open('App_results.txt', 'w') as file:
            file.write("Plant identification informations : \n "+formatted_identification)

        url = 'https://plant.id/api/v3/health_assessment?language=fr&details=local_name,description,url,treatment,classification,common_names,cause'

        response_health = requests.post(url, json=body, headers=headers)
        health_result = response_health.json().get('result', {})
        formatted_health = json.dumps(health_result, indent=4)

        with open('App_results.txt', 'a') as file:
            file.write("\n\n Plant Health informations : \n " + formatted_health)

        return jsonify({
            'identification': identification_result,
            'health': health_result
        })

    except Exception as e:
        return jsonify({'error': str(e)})
    
def upload_file(file_uploaded):
    global uploaded_file
    uploaded_file = client.files.create(
            file=open(file_uploaded, 'rb'),
            purpose='assistants',
        )
         
def create_thread():
    thread = client.beta.threads.create()
    return thread.id

def user_message_func(user_message):
    global thread_principal_id
    message = client.beta.threads.messages.create(
        thread_id=thread_principal_id,
        role="user",
        content=user_message,
    )
    return message
def run_func():
    global thread_principal_id, assistant_principal_id
    run = client.beta.threads.runs.create(
        thread_id=thread_principal_id,
        assistant_id=assistant_principal_id,
    )
    while True:
        run = client.beta.threads.runs.retrieve(thread_id=thread_principal_id, run_id=run.id)
        if run.status == "completed":
            messages = client.beta.threads.messages.list(thread_id=thread_principal_id)
            latest_message = messages.data[0]
            text = latest_message.content[0].text.value
            break
    return text

@app.route('/create_assistant/', methods=['POST'])
def create_assistant():
    global uploaded_file
    upload_file("App_results.txt")
    try:
        assistant = client.beta.assistants.create(
        name="Plant Expert",
        instructions= "En tant qu'assistant expert en plantes, vous êtes chargé d'aider les particuliers en agriculture autosuffisante, en particulier ceux avec des connaissances limitées en horticulture. Vous utilisez les données du fichier 'App_results.txt', qui contient des informations détaillées sur l'état des plantes de l'utilisateur, y compris l'identification des espèces et la détection des maladies par l'application au préalable. Votre rôle est de présenter ces informations de manière claire et accessible, en fournissant des conseils pratiques sur le traitement des maladies identifiées avec une préférence pour les méthodes naturelles et biologiques. Encouragez l'utilisateur à adopter des pratiques durables dans son jardin et guidez-le vers des ressources complémentaires pour approfondir ses connaissances. Favorisez l'interaction en répondant de manière dynamique aux questions spécifiques, et sollicitez des retours pour améliorer continuellement le service.",
        tools=[{"type": "retrieval"}],
        model="gpt-4-1106-preview",
        file_ids=[uploaded_file.id]
    )
        global assistant_principal_id
        assistant_principal_id = assistant.id
        return jsonify({'assistant_id': assistant_principal_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)
