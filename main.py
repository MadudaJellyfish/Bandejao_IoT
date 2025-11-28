import paho.mqtt.client as mqtt
import numpy as np
import cv2 as cv
import os
import json
import time

from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes
from datetime import datetime
from ultralytics import YOLO


BROKER = "mqtt.janks.dev.br"     
PORT = 8883     

client = mqtt.Client(client_id="bandejao_camera")
client.username_pw_set("aula", "zowmad-tavQez")
client.connect(BROKER, PORT, keepalive=60)

properties=Properties(PacketTypes.PUBLISH)
properties.MessageExpiryInterval=120 

model = YOLO('yolov8l-pose.pt')

total_pessoas_media = 0
qtd_imagens = 0 #a cada duas imagens recebidas eu calculo a média de pessoas com base nestas duas fotos

def on_connect(client, userdata, flags, rc):
    print("Código conectado:", rc)
    client.subscribe("foto_bandejao")
    client.subscribe("qtdBandejao")
    client.subscribe("qtdFila")

def posture_analise(keypoints):
    if len(keypoints) < 17:
        return "Desconhecido"
    
    left_hip = keypoints[11]
    right_hip = keypoints[12]
    left_ankle = keypoints[15]
    right_ankle = keypoints[16]
    left_knee = keypoints[13]
    right_knee = keypoints[14]
    
    if (left_hip[0] > 0 and left_hip[1] > 0 and 
        right_hip[0] > 0 and right_hip[1] > 0 and 
        left_ankle[0] > 0 and left_ankle[1] > 0 and 
        right_ankle[0] > 0 and right_ankle[1] > 0):
        
        hip_y = (left_hip[1] + right_hip[1]) / 2
        ankle_y = (left_ankle[1] + right_ankle[1]) / 2
        knee_y = (left_knee[1] + right_knee[1]) / 2
        
        if hip_y < ankle_y - 100:
            return "Em pé"
        elif hip_y > knee_y - 50:
            return "Sentado"
    
    return "Desconhecido"

def count_people_in_image(image_name):   
  
  img = cv.imread(image_name)
  img = cv.resize(img, (640, 480))
  
  results = model(img)
  people_count = {"em_pe": 0, "sentado": 0, "desconhecido": 0}
  
  for res in results:
      keypoints = res.keypoints.xy.numpy()  
      for person_idx, person_kpts in enumerate(keypoints):
          posture = posture_analise(person_kpts) 
          
          if posture == "Em pé":
              people_count["em_pe"] += 1
              color = (0, 255, 0)  
          elif posture == "Sentado":
              people_count["sentado"] += 1
              color = (0, 0, 255)  
          else:
              people_count["desconhecido"] += 1
              color = (0, 255, 255) 
      
          valid_points = [(int(kpt[0]), int(kpt[1])) for kpt in person_kpts 
                if kpt[0] > 0 and kpt[1] > 0]
          
          if valid_points:
            x_coords = [p[0] for p in valid_points]
            y_coords = [p[1] for p in valid_points]
            
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            
            cv.rectangle(img, (x_min - 10, y_min - 10), (x_max + 10, y_max + 10), color, 2)
    
    
  # Escrever resumo
  total_pessoas = people_count['em_pe'] + people_count['sentado'] + people_count['desconhecido']

  global total_pessoas_media
  global qtd_imagens
  total_pessoas_media += total_pessoas
  qtd_imagens+=1

  summary = f"Total pessoas {total_pessoas}"
  cv.putText(img, summary, (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
  
  print(f"Resultado: {summary}")
  
  cv.imshow("Camera Bandejao", img)
  cv.waitKey(1)

def delete_old_images():
    print("Deletando imagens mais antigas....\n")

    

def process_foto(msg):
    print("Foto recebida!")
    image_data = msg.payload
    data_e_hora_str = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
    image_name = "image_bandejao.png"

    try:
        with open(image_name, "wb") as f:
            f.write(image_data)
        print("Imagem recebida salva!")
    except Exception as e:
        print(f"Erro ao salvar imagem: {e}")
        return
    count_people_in_image(image_name)

def process_telegram(msg):
    print("chegou mensagem do tópico " + msg.topic)
    print("conteudo:\n")
    print(msg.payload)
    payload = msg.payload.decode("utf-8")

    if(payload.startswith('{"c')):
        try:
            msg_data = json.loads(payload)

            content = msg_data.get("content") #qtdBandejao ou qtdFila
            chatId = msg_data.get("chatId")
            qtd_pessoa_media = total_pessoas_media // qtd_imagens

            print("Enviando mensagem para o canal " + msg.topic + " ....")
            return_message = {
                "qtd": qtd_pessoa_media,
                "chatId" : chatId
            }

            json_ret_msg = json.dumps(return_message)
            client.publish(msg.topic, json_ret_msg, qos = 2, properties=properties)

        except json.JSONDecodeError:
            print("Payload com Json inválido!!!")

    
def on_message(client, userdata, msg):
    if msg.topic == "foto_bandejao":
        process_foto(msg)
    else:
        process_telegram(msg)

        
client.tls_set()
client.on_connect = on_connect
client.on_message = on_message

client.loop_start()

try:
    print("Aguardando imagens MQTT...")
    while True:
        import time
        time.sleep(1)
except KeyboardInterrupt:
    print("Desconectando...")
    client.loop_stop()
    client.disconnect()