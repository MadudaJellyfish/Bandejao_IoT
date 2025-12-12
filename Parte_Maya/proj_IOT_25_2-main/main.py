from flask import Flask, request, render_template, redirect, url_for, jsonify
from pymongo import MongoClient, ASCENDING, DESCENDING
#from pymongo.server_api import ServerApi
import os
import json 
import ast
from datetime import datetime, time
import requests
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
import threading

rfid_event = threading.Event()
rfid_valor = ""

load_dotenv()

import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool

BROKER = "mqtt.janks.dev.br"     
PORT   = 8883              

client = mqtt.Client(client_id="python-publisher")

client.username_pw_set("aula", "zowmad-tavQez")

client.connect(BROKER, PORT, keepalive=60)

def on_connect(client, userdata, flags, rc):
    print("Conectado com código:", rc)
    client.subscribe("rfidCadastro")  # assina o tópico ao conectar

def on_message(client, userdata, msg):
    global rfid_valor
    print("Chegou mensagem no tópico:", msg.topic)
    payload = msg.payload.decode("utf-8")
    print("Payload bruto:", payload)
    if msg.topic == "rfidCadastro" and payload.startswith('{"r'):
        try:
            data = json.loads(payload)
            rfid_valor = data.get("rfid")
            print("RFID:", rfid_valor)
            rfid_event.set()
        except json.JSONDecodeError:
            print("Payload não é JSON válido")

client.tls_set()  
client.on_connect = on_connect
client.on_message = on_message

# pega do .env
PGHOST = os.getenv("PGHOST")
PGPORT = int(os.getenv("PGPORT", "5432"))
PGDB   = os.getenv("PGDATABASE")
PGUSER = os.getenv("PGUSER")
PGPASS = os.getenv("PGPASSWORD")

pool = SimpleConnectionPool(1, 5,
    host=PGHOST, port=PGPORT, dbname=PGDB, user=PGUSER, password=PGPASS
)

def _conn():
    return pool.getconn()

def _free(c):
    pool.putconn(c)

ARDUINO_IP = ""

def lista_pessoas():
    c = _conn()
    try:
        with c.cursor() as cur:
            cur.execute("""SELECT nome, cpf, saldo
                           FROM base_bandejao
                           ORDER BY created_at DESC, id DESC""")
            return [
                {"nome": r[0], "cpf": r[1], "saldo": r[2]}
                for r in cur.fetchall()
            ]
    finally:
        _free(c)

def busca_por_cpf(cpf):
    c = _conn()
    try:
        with c.cursor() as cur:
            cur.execute("""SELECT nome, saldo, senha, chat_id, rfid
                           FROM base_bandejao WHERE cpf=%s""", (cpf,))
            r = cur.fetchone()
            if not r: return None
            return {"nome": r[0], "saldo": r[1], "chatId": r[3], "rfid": r[4]}
    finally:
        _free(c)

def existe_cpf(cpf):
    c = _conn()
    try:
        with c.cursor() as cur:
            cur.execute("SELECT 1 FROM base_bandejao WHERE cpf=%s", (cpf,))
            return cur.fetchone() is not None
    finally:
        _free(c)

def insere_pessoa(nome, cpf, saldo, chatId, rfid):
    c = _conn()
    try:
        with c.cursor() as cur:
            cur.execute("""INSERT INTO base_bandejao (nome, cpf, saldo, chat_id, rfid)
                           VALUES (%s,%s,%s, %s, %s)""",
                        (nome, cpf, int(saldo or 0), chatId, rfid))
        c.commit()
    finally:
        _free(c)

def atualiza_pessoa(cpf, nome, saldo, chatId, rfid):
    c = _conn()
    try:
        with c.cursor() as cur:
            cur.execute("""UPDATE base_bandejao
                           SET nome=%s, saldo=%s, chat_id=%s, rfid=%s
                           WHERE cpf=%s""",
                        (nome, int(saldo or 0), chatId, rfid, cpf))
        c.commit()
    finally:
        _free(c)

def exclui_por_cpf(cpf):
    c = _conn()
    try:
        with c.cursor() as cur:
            cur.execute("DELETE FROM base_bandejao WHERE cpf=%s", (cpf,))
        c.commit()
    finally:
        _free(c)

UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024 #limite de 16mb
print(app.config)

@app.route("/", methods = ["GET", "POST"]) #mudado
@app.route("/index.html", methods = ["GET", "POST"])
def menu():    
    lPessoas = lista_pessoas()    
    return render_template("index.html", lPessoas = lPessoas)

@app.route("/pedeRfid", methods = ["POST"])
def pedeRfid():    
    global rfid_valor
    rfid_valor = None
    rfid_event.clear()

    retorno = client.publish("rfidCadastro", "ler", qos=0, retain=False)
    print("Publicou com retorno:", retorno)
    if not rfid_event.wait(timeout=120):
        return jsonify({"ok": False, "erro": "timeout"}), 504
    print("Evento de RFID recebido")
    return jsonify({"ok": True, "rfid": rfid_valor})
    #return render_template("cadastramento.html", lCadastro = lCadastro)

@app.route("/favicon.ico", methods = ["GET", "POST"]) #mudado
@app.route("/index/favicon.ico.html", methods = ["GET", "POST"])
def favico():
    return redirect(url_for("menu"))

@app.route("/cadastramento.html", methods = ["GET", "POST"]) #mudado
def cadastra():
    lCadastro = ['', '', '', '', '']  # nome, cpf, saldo, chatId, rfid
    if request.method == "POST":
        nome = request.form.get("fNome")
        cpf = request.form.get("fcpf")
        saldo = request.form.get("fsaldo")
        chatId = request.form.get("fchatId")
        rfid = request.form.get("frfid")
        #foto = request.files.get("fFoto")

        if existe_cpf(cpf):           
            lCadastro[0] = nome
            lCadastro[1] = cpf
            lCadastro[2] = saldo
            lCadastro[3] = chatId
            lCadastro[4] = rfid
            return render_template("cadastramento.html", error = True, lCadastro = lCadastro)
        
        else:
            insere_pessoa(nome, cpf, saldo, chatId, rfid)            
        return redirect(url_for("menu"))
    else:
        return render_template("cadastramento.html", lCadastro = lCadastro)
    
@app.route("/exclui/<num>.html", methods = ["GET", "POST"]) #mudado
def exclui(num):  
    exclui_por_cpf(num)
    return redirect(url_for("menu"))
    
@app.route("/edita/<num>.html", methods = ["GET", "POST"]) #mudado
def edita(num):
    print("entrei na edita")
    print(num)
    pessoa = busca_por_cpf(num)
    print(pessoa)
    lEdita = ["", "", "", ""]
    lEdita[0] = pessoa["nome"]
    lEdita[1] = pessoa["saldo"]
    lEdita[2] = pessoa["chatId"]
    lEdita[3] = pessoa["rfid"]
    print(lEdita[0])

    if request.method == "POST":
        nome = request.form.get("fNome")
        saldo = request.form.get("fsaldo")
        chatId = request.form.get("fchatId")
        rfid = request.form.get("frfid")
        
        print({"cpf" : num}, {"nome": nome, "saldo" : saldo, "chatId": chatId, "rfid": rfid})
        atualiza_pessoa(num, nome, saldo, chatId, rfid)
        print("dentro")
        return redirect(url_for("menu"))
    #return redirect(url_for("edita", lEdita = lEdita, num = num, turma = turma))
    print(lEdita)
    return render_template("edita.html", lEdita = lEdita, num = num)

#if __name__ == '__main__':

client.loop_start()
app.run(port=5002, debug=False)