from flask import Flask, request, render_template, redirect, url_for, jsonify
from pymongo import MongoClient, ASCENDING, DESCENDING
#from pymongo.server_api import ServerApi
import os
import json 
import ast
from datetime import datetime, time
import requests

ARDUINO_IP = ""

uri = "mongodb+srv://rrddamazio:vQ4lM2M1zErxlIFY@bdprojfinalmic.rgwiall.mongodb.net/?retryWrites=true&w=majority&appName=bdProjFinalMic"
cliente = MongoClient(uri, 27017)
'''
try:
    cliente = MongoClient(uri, 27017)
    banco = cliente["banco_proj_final"]
    colecao = banco["alunos"]
    print("Conexão estabelecida com sucesso.")
    for doc in colecao.find():
        print(doc)
except Exception as e:
    print(f"Erro ao conectar com MongoDB: {e}")
'''

banco = cliente["banco_proj_final"]

colecao = banco["alunos"]
colecaoDias = banco["aulas"]

turmaAtual = "33B"
NomeAtual = "Micro"

"""
def atualizaColecao():
    global colecaoDias
    colecaoDias = banco[aula]
"""

#lAlunos = []

UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024 #limite de 16mb
print(app.config)
# nome, matricula, curso, foto            


@app.route("/", methods = ["GET", "POST"]) #mudado
def menu1():
    global turmaAtual
    return redirect(url_for("menu", turma = turmaAtual))


@app.route("/<turma>", methods = ["GET", "POST"]) #mudado
@app.route("/index/<turma>.html", methods = ["GET", "POST"])
def menu(turma):    
    global turmaAtual
    turmaAtual = turma
    #atualizaColecao()
    lAlunos = []
    lTurmas = []
    for elem in colecaoDias.find():
        lTurmas.append(elem["codigo"])

    
    for aluno in colecao.find():
        if aluno["turma"] == turmaAtual:
            lAlunos.append(aluno)

    if request.method == "POST":
        codigo= request.form.get("fTurmas")
        turmaAtual = codigo
        return redirect(url_for("menu", turma = turmaAtual))
    
    return render_template("index.html", lAlunos = lAlunos, turmaAtualP = turmaAtual, lTurmas = lTurmas)

@app.route("/favicon.ico", methods = ["GET", "POST"]) #mudado
@app.route("/index/favicon.ico.html", methods = ["GET", "POST"])
def favico():
    global turmaAtual
    return redirect(url_for("menu", turma = turmaAtual))

@app.route("/cadastramento.html", methods = ["GET", "POST"]) #mudado
def cadastra():
    global turmaAtual
    lCadastro = ["", "", "", ""]
    if request.method == "POST":
        nome = request.form.get("fNome")
        matricula = request.form.get("fMatricula")
        curso = request.form.get("fCurso")
        turmaAluno = request.form.get("fTurma")
        foto = request.files.get("fFoto")

        ind = colecao.find_one({"matricula" : matricula})
        print(ind)
        print(type(ind))
        print(turmaAtual)

        if ind != None and turmaAluno == ind["turma"]:           
            lCadastro[0] = nome
            lCadastro[1] = matricula
            lCadastro[2] = curso
            lCadastro[3] = turmaAluno
            return render_template("cadastramento.html", error = True, lCadastro = lCadastro, turma = turmaAtual)

        elif foto:
            # Salvar a foto no diretório de uploads
            foto_path = os.path.join(app.config['UPLOAD_FOLDER'], foto.filename)
            foto.save(foto_path)          
            colecao.insert_one({"nome":nome, "matricula" : matricula, "curso" : curso, "turma" : turmaAluno, "foto" : foto.filename, "presenca" : [], "uid" : ""})
        else:
            colecao.insert_one({"nome":nome, "matricula" : matricula, "curso" : curso, "turma" : turmaAluno, "foto" : None, "presenca" : [], "uid" : ""})
        return redirect(url_for("menu", turma = turmaAtual))
    else:
        print(turmaAtual)

        return render_template("cadastramento.html", lCadastro = lCadastro, turma = turmaAtual)
    
@app.route("/exclui/<num>.html", methods = ["GET", "POST"]) #mudado
def exclui(num):  
    global turmaAtual
    colecao.delete_one({"matricula" : num, "turma" : turmaAtual})
    return redirect(url_for("menu", turma = turmaAtual))
    
@app.route("/edita/<num>.html", methods = ["GET", "POST"]) #mudado
def edita(num):
    print("entrei na edita")
    global turmaAtual
    print(num)
    aluno = colecao.find_one({"matricula" : num, "turma" : turmaAtual})
    print(aluno)
    lEdita = ["", "", ""]
    lEdita[0] = aluno["nome"]
    lEdita[1] = aluno["turma"]
    print(lEdita[0])
    if aluno["curso"] ==  "não informado":
        lEdita[2] = "Engenharia"
    else:
        lEdita[2] = aluno["curso"]

    if request.method == "POST":
        nome = request.form.get("fNome")
        curso = request.form.get("fCurso")
        turma = request.form.get("fTurma")
        try:
            foto = request.files.get("fFoto")
            foto_path = os.path.join(app.config['UPLOAD_FOLDER'], foto.filename)
            foto.save(foto_path)
        except Exception as e:
            print(f"Erro ao fazer upload da foto: {e}")
            colecao.update_one({"matricula" : num, "turma" : turmaAtual}, {"$set":{"nome": nome, "curso" : curso, "turma" : turma, "foto" : None}})
        
        if foto:
            
            
            print({"matricula" : num}, {"nome": nome, "curso" : curso, "foto" : foto.filename})
            colecao.update_one({"matricula" : num, "turma" : turmaAtual}, {"$set":{"nome": nome, "curso" : curso, "turma" : turma, "foto" : foto.filename}})
        else:    
            print({"matricula" : num}, {"nome": nome,"curso" : curso, "foto" : None})
            colecao.update_one({"matricula" : num, "turma" : turmaAtual}, {"$set":{"nome": nome, "curso" : curso, "foto" : None}})
        print("dentro")
        print(turmaAtual)
        return redirect(url_for("menu", turma = turmaAtual))
    #return redirect(url_for("edita", lEdita = lEdita, num = num, turma = turma))
    print(lEdita)
    return render_template("edita.html", lEdita = lEdita, num = num, turma = turmaAtual)

@app.route("/presenca/<num>.html", methods = ["GET", "POST"]) #mudado
def presenca(num):
    global turmaAtual
    aluno = colecao.find_one({"matricula" : num, "turma" : turmaAtual})
    lpresenca = aluno["presenca"]
    return render_template("presenca.html", lpresenca = lpresenca, turma = turmaAtual) 

@app.route("/criaAula", methods = ["GET", "POST"])
def criaAula():
    global turmaAtual
    if request.method == "POST":
        data = request.form.get("fData")
        hora = request.form.get("fHora")
        #arqJson = json.loads(arqJson)
        data = datetime.strptime(data, "%Y-%m-%d").strftime("%d-%m-%Y")
        ind = colecaoDias.find_one({"codigo": turmaAtual})
        print(ind["datas"])
        lDias = ind["datas"]
        print(lDias)
        lDias.append({"data" : data, "hora" : hora})
        print(lDias)
        colecaoDias.update_one({"codigo": turmaAtual}, {"$set" : {"datas" : lDias}})
        return redirect(url_for("menu", turma = turmaAtual))
    return render_template("criaAula.html", turma = turmaAtual)

@app.route("/recebePresenca", methods = ["GET", "POST"]) #testada
def passaPresenca():
    if request.method == "POST":
        arqJson = request.get_json() # {"data : xx-xx-xxxx, "presencas" : [{"matricula" : xxx, "hora" : "xx:xx:xx", "turma" : "YYY"}]}
    #arqJson = json.dumps({"data": "23-05-2024", "presencas": [{"matricula": 2210833, "hora": "23:59:05"}]})
    #arqJson = json.loads(arqJson)

        arqJson = arqJson[0]["presenca"]
        print(arqJson)
        print(type(arqJson))

        
        lMatriculas = []
        lHoras = []
        lTurma = []
        data = arqJson["data"]
        data= datetime.strptime(arqJson["data"], "%d-%m-%Y")
        data = data.strftime("%d-%m-%Y")
        for aluno in arqJson["presencas"]:
            lMatriculas.append(aluno["matricula"])
            lHoras.append(datetime.strptime(aluno["hora"], "%H:%M:%S").time())
            lTurma.append(aluno["turma"])

        for aluno in colecao.find():
            lAlunoPresenca = aluno["presenca"]
            horaOficial = None
            presencaAluno = []
            print(aluno)
            print(aluno["matricula"])
            print(lMatriculas)
            print(aluno["turma"])
            print(lTurma)
            if int(aluno["matricula"]) in lMatriculas and aluno["turma"] in lTurma:
                ind = lMatriculas.index(int(aluno["matricula"]))
                print(ind)
                horaAluno = lHoras[ind] 
                print(horaAluno)
                print(colecaoDias.find_one({"codigo" : aluno["turma"]}))
                lHorarios = colecaoDias.find_one({"codigo" : aluno["turma"]})["datas"]
                print(lHorarios)
                if lHorarios == None:
                    return "Dia não cadastrado"
                for dia in lHorarios:
                    if dia["data"] == data:
                        horaOficial = dia["hora"]
                
                if horaOficial == None:
                    return "Aula não cadastrada"
                print(horaOficial)
                horaAula = datetime.strptime(horaOficial, "%H:%M:%S").time()
                
                if horaAluno <= horaAula:
                 presencaAluno = [data, "presente", "pontual"]
                else:
                  presencaAluno = [data, "presente", "atrasado"]
                lAlunoPresenca.append(presencaAluno)
                
            else:
                lHorarios = colecaoDias.find_one({"codigo" : aluno["turma"]})["datas"]
                if lHorarios == None:
                    return "Dia não cadastrado"
                for dia in lHorarios:
                    if dia["data"] == data:
                        horaOficial = dia["hora"]
                if horaOficial != None:                
                    presencaAluno = [data, "faltou", "-"]
                    lAlunoPresenca.append(presencaAluno)

            print(presencaAluno)
            
            print(lAlunoPresenca)
            colecao.update_one({"matricula" : aluno["matricula"], "turma" : aluno["turma"]}, {"$set":{"presenca" : lAlunoPresenca}})
        return "foi"
    return "não foi"

@app.route("/passaInfo", methods = ["GET", "POST"]) #Testada
def passaInfo():
    lAlunos = []
    for aluno in colecao.find():
        
        lAlunos.append({"nome" : aluno["nome"], "matricula" : aluno["matricula"], "uid" : aluno["uid"], "turma" : aluno["turma"]})
    print(lAlunos)
    arqJson = json.dumps({"alunos" : lAlunos})
    print(arqJson)
    return jsonify({"alunos" : lAlunos})

@app.route("/recebeCadastro", methods = ["GET", "POST"])
def recebeCadastro():
    if request.method == "POST":
        arqJson = request.get_json() #{"uid": "anlifu", "nome" : "hdjfsakl", "matricula" : xxxxxx}
        #arqJson = json.dumps({"uid": "45649", "nome" : "hdjfsakl", "matricula" : 2210833})
        #arqJson = json.loads(arqJson)
        print(arqJson)
        arqJson = arqJson[0]["alunos"]
        for aluno in arqJson["alunos"]:
            print(aluno)
            alunoExiste = colecao.find_one({"matricula" : str(aluno["matricula"]), "turma": aluno["turma"]})
            print(alunoExiste)
            if alunoExiste != None:
                colecao.update_one({"matricula" : str(aluno["matricula"]), "turma": aluno["turma"]}, {"$set":{"uid" : aluno["uid"]}})
            else:
                colecao.insert_one({"nome":"não informado",
                                    "matricula" : str(aluno["matricula"]),
                                    "curso" : "não informado",
                                    "turma" : aluno["turma"],
                                    "foto" : None,
                                    "presenca" : [],
                                    "uid" : aluno["uid"],
                                    })
        return "foi"
    return "não recebi nada"

@app.route("/criaTurma", methods = ["GET", "POST"]) #testada
def criaTurma():
    print("entrei aqui")
    global turmaAtual
    lCria = ["", ""]
    if request.method == "POST":
        nome = request.form.get("fNome")
        codigo = request.form.get("fCodigo")

        busca = {"nome" : nome, "codigo" : codigo}
        ind = colecaoDias.find_one(busca)

        if ind != None:
            lCria[0] = codigo
            lCria[1] = nome
            return render_template("criaTurma.html", error = True, lCria = lCria, turmaAtualP = turmaAtual)        
        colecaoDias.insert_one({"nome" : nome, "codigo" : codigo, "datas" : []})
        return redirect(url_for("menu", turma = turmaAtual))
    return render_template("criaTurma.html", lCria = lCria, turmaAtualP = turmaAtual)

#if __name__ == '__main__':
app.run(port=5002, debug=False)