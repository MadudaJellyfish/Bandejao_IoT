#include <Arduino.h>
#include <SPI.h>
#include <MFRC522.h>
#include "certificados.h"
#include <HX711.h>
#include <GxEPD2_BW.h>
#include <U8g2_for_Adafruit_GFX.h>
#include <ArduinoJson.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <MQTT.h>

#define BUZZER_PIN 1        // GPIO do buzzer (ajuste se necessário)
#define BUZZER_RES 10       // resolução do PWM (bits)

WiFiClientSecure conexaoSegura;
MQTTClient mqtt(1000);

U8G2_FOR_ADAFRUIT_GFX fontes;
GxEPD2_290_T94_V2 modeloTela(10, 14, 15, 16);
GxEPD2_BW<GxEPD2_290_T94_V2, GxEPD2_290_T94_V2::HEIGHT> tela(modeloTela);

MFRC522 rfid(46, 17);
MFRC522::MIFARE_Key chaveA =
    {{0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF}};

String idCliente = "";
String nomeCliente = "";
float saldoAnterior = 0;
float saldoRestante = 0;
unsigned long tempoUltimaTela = 0;
bool mostrandoNome = false;
bool possui_cadastro = true;
String rfid_enviado = "";

void desenha_falta_cadastro()
{
  tela.fillScreen(GxEPD_WHITE);
  fontes.setFont(u8g2_font_helvR18_te);
  fontes.setFontMode(1);
  fontes.setCursor(25, 30);
  fontes.print("Não possui cadastro.");
  fontes.setFont(u8g2_font_helvR12_te);
  fontes.setFontMode(1);
  fontes.setCursor(25, 60);
  fontes.print("Favor, realizar cadastro");
  fontes.setCursor(25, 90);
  fontes.print("na secretaria.");
  tela.display(true);
}

void desenha_nome()
{
  tela.fillScreen(GxEPD_WHITE);
  fontes.setFont(u8g2_font_helvR18_te);
  fontes.setFontMode(1);
  fontes.setCursor(25, 30);
  fontes.print("Bem-vindo(a),");
  fontes.setCursor(25, 60);
  fontes.print(nomeCliente + "!");
  fontes.setFont(u8g2_font_helvR12_te);
  fontes.setFontMode(1);
  fontes.setCursor(25, 85);
  fontes.print("Saldo Anterior: R$ " + String(saldoAnterior));
  fontes.setCursor(25, 105);
  fontes.print("Saldo Restante: R$ " + String(saldoRestante));
  tela.display(true); // SEMPRE CHAMAR NO FINAL!
}

void reconectarMQTT()
{
  if (!mqtt.connected())
  {
    Serial.print("Conectando MQTT...");
    while (!mqtt.connected())
    {
      mqtt.connect("lulu", "aula", "zowmad-tavQez");
      Serial.print(".");
      delay(1000);
    }
    Serial.println(" conectado!");

    mqtt.subscribe("possui-cadastro");
    mqtt.subscribe("falta-cadastro");
    mqtt.subscribe("check-cadastro");
    mqtt.subscribe("rfidCadastro");
  }
}

void reconectarWiFi()
{
  if (WiFi.status() != WL_CONNECTED)
  {
    WiFi.begin("Projeto", "2022-11-07");
    Serial.print("Conectando ao WiFi...");
    while (WiFi.status() != WL_CONNECTED)
    {
      Serial.print(".");
      delay(1000);
    }
    Serial.print("conectado!\nEndereço IP: ");
    Serial.println(WiFi.localIP());
  }
}

void recebeuMensagem(String topico, String conteudo)
{
  digitalWrite(1, HIGH);
  delay(200);
  digitalWrite(1, LOW);
  Serial.println(topico + ": " + conteudo);
  if (topico.startsWith("possui-cadastro"))
  {
    possui_cadastro = true;

    JsonDocument dados_aluno;
    DeserializationError err = deserializeJson(dados_aluno, conteudo);
    if (err)
    {
      Serial.print("Erro deserializeJson: ");
      Serial.println(err.c_str());
      return;
    }

    JsonObject aluno = dados_aluno[0].as<JsonObject>();
    if (aluno.isNull())
    {
      Serial.println("doc[0] veio null (array vazio ou formato diferente)");
      return;
    }

    String recebe_nomeCliente = aluno["nome"];
    nomeCliente = recebe_nomeCliente;
    Serial.println(nomeCliente);
    float recebe_saldoAnterior = aluno["saldo"];
    saldoAnterior = recebe_saldoAnterior;
    Serial.println(saldoAnterior);
    saldoRestante = saldoAnterior - 20;
    Serial.println(saldoRestante);
    desenha_nome();
    Serial.println("Usuário possui cadastro");

    JsonDocument novo_saldo;
    novo_saldo["rfid"] = aluno["rfid"];
    novo_saldo["saldo"] = saldoRestante;
    novo_saldo["valor"] = -13;

    String envia_saldo;
    serializeJson(novo_saldo, envia_saldo);
    mqtt.publish("mudaSaldo", envia_saldo);
  }

  if (topico.startsWith("falta-cadastro"))
  {
    possui_cadastro = false;
    desenha_falta_cadastro();
    Serial.println("Usuário não possui cadastro");
  }

  if ((topico.startsWith("rfidCadastro")) && conteudo.startsWith("ler"))
  {
    Serial.println("Pedindo RFID");
    JsonDocument dados_rfid;
    dados_rfid["rfid"] = rfid_enviado;
    String textoJson;
    serializeJson(dados_rfid, textoJson);
    mqtt.publish("rfidCadastro", textoJson);
  }
}

void desenha_welcome()
{
  tela.fillScreen(GxEPD_WHITE);
  fontes.setFont(u8g2_font_helvR18_te);
  fontes.setFontMode(1);
  fontes.setCursor(25, 30);
  fontes.print("Olá! Tudo bem?");
  fontes.setCursor(25, 75);
  fontes.print("Por favor, aproxime");
  fontes.setCursor(25, 110);
  fontes.print("seu id abaixo.");
  tela.display(true);
}

String lerRFID()
{
  String id = "";
  for (byte i = 0; i < rfid.uid.size; i++)
  {
    if (i > 0)
    {
      id += " ";
    }
    if (rfid.uid.uidByte[i] < 0x10)
    {
      id += "0";
    }
    id += String(rfid.uid.uidByte[i], HEX);
  }
  id.toUpperCase();
  return id;
}

String lerTextoDoBloco(byte bloco)
{
  byte tamanhoDados = 18;
  char dados[tamanhoDados];
  MFRC522::StatusCode status = rfid.PCD_Authenticate(
      MFRC522::PICC_CMD_MF_AUTH_KEY_A,
      bloco, &chaveA, &(rfid.uid));
  if (status != MFRC522::STATUS_OK)
  {
    return "";
  }
  status = rfid.MIFARE_Read(bloco,
                            (byte *)dados, &tamanhoDados);
  if (status != MFRC522::STATUS_OK)
  {
    return "";
  }
  dados[tamanhoDados - 2] = '\0';
  return String(dados);
}

void setup()
{
  Serial.begin(115200);
  delay(500);
  Serial.println("Semana 1 - Testes Luciana");

  tela.init();
  tela.setRotation(3);
  tela.fillScreen(GxEPD_WHITE);
  fontes.begin(tela);
  fontes.setForegroundColor(GxEPD_BLACK);
  desenha_welcome();

  reconectarWiFi();
  conexaoSegura.setCACert(certificado1);

  mqtt.begin("mqtt.janks.dev.br", 8883, conexaoSegura);
  mqtt.onMessage(recebeuMensagem);
  mqtt.setKeepAlive(10);
  reconectarMQTT();

  SPI.begin();
  rfid.PCD_Init();
  rgbLedWrite(RGB_BUILTIN, 0, 0, 0);

  pinMode(1, OUTPUT); //campainha
}

void loop()
{

  unsigned long agora = millis();

  // Verifica se um novo cartão foi detectado
  if (rfid.PICC_IsNewCardPresent() &&
      rfid.PICC_ReadCardSerial())
  {
    String id = lerRFID();
    Serial.println("Tentando ler");
    Serial.println("UID: " + id);
    idCliente = id;
    // Atribuindo id "agora" a uma variavel global p enviar p Maya
    rfid_enviado = id;

    // Vamos tirar isso aqui depois
    // Deletar depois
    // String texto = lerTextoDoBloco(5);
    // Serial.println("Bloco 5: " + texto);
    // nomeCliente = texto;

    Serial.println(idCliente);
    mostrandoNome = true;
    tempoUltimaTela = agora;

    // Incluir check com banco de dados
    mqtt.publish("check-cadastro", idCliente);
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
  }

  // Volta para a tela de boas-vindas após 3 segundos
  if (mostrandoNome && (agora - tempoUltimaTela >= 7000))
  {
    desenha_welcome();
    mostrandoNome = false;
  }

  reconectarWiFi();
  reconectarMQTT();
  mqtt.loop();
}
