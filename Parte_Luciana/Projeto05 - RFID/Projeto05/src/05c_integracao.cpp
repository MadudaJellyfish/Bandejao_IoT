#include <Arduino.h>
#include <SPI.h>
#include <MFRC522.h>
#include "certificados.h"
#include <HX711.h>
#include <GxEPD2_BW.h> 
#include <U8g2_for_Adafruit_GFX.h> 
#include <ArduinoJson.h>

U8G2_FOR_ADAFRUIT_GFX fontes; 
GxEPD2_290_T94_V2 modeloTela(10, 14, 15, 16); 
GxEPD2_BW<GxEPD2_290_T94_V2, GxEPD2_290_T94_V2::HEIGHT> tela(modeloTela);

MFRC522 rfid(46, 17);
MFRC522::MIFARE_Key chaveA =
    {{0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF}};

String idCliente = "";
String nomeCliente = "";
String saldoConsumido = "23.75";
String saldoRestante = "200.50";
float saldo_consumido = 23.75;
float saldo_restante = 200.50;
unsigned long tempoUltimaTela = 0;
bool mostrandoNome = false;


bool possui_cadastro = true;

void desenha_welcome() {
  tela.fillScreen(GxEPD_WHITE); 
  fontes.setFont( u8g2_font_helvR18_te );
  fontes.setFontMode(1); 
  fontes.setCursor(25,30); 
  fontes.print("Olá! Tudo bem?"); 
  fontes.setCursor(25,75); 
  fontes.print("Por favor, aproxime");
  fontes.setCursor(25,110); 
  fontes.print("seu id abaixo.");
  tela.display(true); 
}

void desenha_falta_cadastro() {
  tela.fillScreen(GxEPD_WHITE);
  fontes.setFont( u8g2_font_helvR18_te );
  fontes.setFontMode(1); 
  fontes.setCursor(25,30); 
  fontes.print("Não possui cadastro."); 
  fontes.setFont( u8g2_font_helvR12_te );
  fontes.setFontMode(1);
  fontes.setCursor(25,60); 
  fontes.print("Favor, realizar cadastro");
  fontes.setCursor(25,90); 
  fontes.print("na secretaria.");
  tela.display(true); 
}

void desenha_nome() {
  tela.fillScreen(GxEPD_WHITE);
  fontes.setFont( u8g2_font_helvR18_te );
  fontes.setFontMode(1); 
  fontes.setCursor(25,30); 
  fontes.print("Bem-vindo(a),"); 
  fontes.setCursor(25,60); 
  fontes.print(nomeCliente+"!"); 
  fontes.setFont( u8g2_font_helvR12_te );
  fontes.setFontMode(1); 
  fontes.setCursor(25,85); 
  fontes.print("Saldo Consumido: R$ "+saldoConsumido);
  fontes.setCursor(25,105); 
  fontes.print("Saldo Restante: R$ "+saldoRestante);
  tela.display(true); // SEMPRE CHAMAR NO FINAL!

}

String lerRFID() { 
  String id = ""; 
  for (byte i = 0; i < rfid.uid.size; i++) { 
    if (i > 0) { 
      id += " "; 
    } 
    if (rfid.uid.uidByte[i] < 0x10) { 
      id += "0"; 
    } 
    id += String(rfid.uid.uidByte[i], HEX); 
  } 
  id.toUpperCase(); 
  return id; 
}

String lerTextoDoBloco(byte bloco) { 
  byte tamanhoDados = 18; 
  char dados[tamanhoDados]; 
  MFRC522::StatusCode status = rfid.PCD_Authenticate( 
    MFRC522::PICC_CMD_MF_AUTH_KEY_A, 
    bloco, &chaveA, &(rfid.uid) 
  ); 
  if (status != MFRC522::STATUS_OK) { return ""; } 
  status = rfid.MIFARE_Read(bloco, 
              (byte*)dados, &tamanhoDados); 
  if (status != MFRC522::STATUS_OK) { return ""; } 
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
   
  SPI.begin();
  rfid.PCD_Init();
}

void loop()
{

  unsigned long agora = millis();

  // Verifica se um novo cartão foi detectado
  if (rfid.PICC_IsNewCardPresent() &&
      rfid.PICC_ReadCardSerial())
  {
    String id = lerRFID();
    Serial.println("UID: " + id);
    idCliente = id; 
    String id_configurado = "F3 B8 2B E2";
    String texto = lerTextoDoBloco(5);
    Serial.println("Bloco 5: " + texto);
    nomeCliente = texto;
    // Incluir checagem para saber se o aluno/pessoa possui cadastro
    // Ele não está printando isso aqui
    Serial.println(idCliente);
    Serial.println(id_configurado);
    mostrandoNome = true;
    tempoUltimaTela = agora;
    if (idCliente==id_configurado) {
      desenha_nome();
    }
    else {
      desenha_falta_cadastro();
    }

    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
  }

  // Volta para a tela de boas-vindas após 3 segundos
  if (mostrandoNome && (agora - tempoUltimaTela >= 7000)) {
    desenha_welcome();
    mostrandoNome = false;
  }

}

