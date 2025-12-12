import os
from dotenv import load_dotenv
import json
import paho.mqtt.client as mqtt


BROKER = "mqtt.janks.dev.br"     
PORT   = 8883              

client = mqtt.Client(client_id="python-publisher")

client.username_pw_set("aula", "zowmad-tavQez")

client.connect(BROKER, PORT, keepalive=60)

def on_connect(client, userdata, flags, rc):
    print("Conectado com código:", rc)
    client.subscribe("rfidCadastro")  # assina o tópico ao conectar

def on_message(client, userdata, msg):
    print("Chegou mensagem no tópico:", msg.topic)
    payload = msg.payload.decode("utf-8")
    print("Payload bruto:", payload)
    if payload.startswith("r"):
        try:
            data = json.loads(payload)
            cpf  = data.get("cpf")
            rfid = data.get("rfid")


        except json.JSONDecodeError:
            print("Payload não é JSON válido")

client.on_connect = on_connect
client.on_message = on_message


client.publish("rfidCadastro", 17, qos=0, retain=False)