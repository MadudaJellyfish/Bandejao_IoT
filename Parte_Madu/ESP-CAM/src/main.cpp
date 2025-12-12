#include <Arduino.h>
#include <esp_camera.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include "certificados.h"
#include <MQTT.h>

unsigned long instanteAnterior = 0;


WiFiClientSecure conexaoSegura; 
MQTTClient mqtt(1000);

camera_config_t config = { 
  .pin_pwdn = -1, .pin_reset = -1, 
  .pin_xclk = 15, .pin_sscb_sda = 4, 
  .pin_sscb_scl = 5, 
  .pin_d7 = 16, .pin_d6 = 17, 
  .pin_d5 = 18, .pin_d4 = 12, 
  .pin_d3 = 10, .pin_d2 = 8, 
  .pin_d1 = 9, .pin_d0 = 11, 
  .pin_vsync = 6, .pin_href = 7, 
  .pin_pclk = 13, 
  .xclk_freq_hz = 20000000, 
  .ledc_timer = LEDC_TIMER_0, 
  .ledc_channel = LEDC_CHANNEL_0, 
  .pixel_format = PIXFORMAT_JPEG, 
  .frame_size = FRAMESIZE_SVGA, 
  .jpeg_quality = 10, .fb_count = 2, 
  .grab_mode = CAMERA_GRAB_LATEST 
};

void reconectarWiFi() { 
  if (WiFi.status() != WL_CONNECTED) { 
    WiFi.begin("Projeto", "2022-11-07"); 
    Serial.print("Conectando ao WiFi..."); 
    while (WiFi.status() != WL_CONNECTED) { 
      Serial.print("."); 
      delay(1000); 
    } 
    Serial.print("conectado!\nEndereço IP: "); 
    Serial.println(WiFi.localIP()); 
  } 
} 

void reconectarMQTT() { 
  if (!mqtt.connected()) { 
    Serial.print("Conectando MQTT..."); 
    while(!mqtt.connected()) { 
      mqtt.connect("madu", "aula", "zowmad-tavQez"); 
      Serial.print("."); 
      delay(1000); 
    } 
    Serial.println(" conectado!"); 
    mqtt.subscribe("foto_bandejao");           
  } 
}

void tirarFotoEEnviarParaMQTT () { 
  camera_fb_t* foto = esp_camera_fb_get(); 
  if (mqtt.publish( "foto_bandejao", 
       (const char*)foto->buf, foto->len)) { 
    Serial.println("Foto enviada com sucesso"); 
  } else { 
    Serial.println("Falha ao enviar foto"); 
  } 
   
  esp_camera_fb_return(foto); // libera memória 
}

void setup()
{
   Serial.begin(115200); delay(500);
   Serial.println("Camera do Bandejão inicializada!!!");

    reconectarWiFi(); 
    conexaoSegura.setCACert(certificado1); 
    mqtt.begin("mqtt.janks.dev.br", 8883, conexaoSegura); 
    mqtt.setKeepAlive(10); 
    mqtt.setWill("tópico da desconexão", "conteúdo"); 

   esp_err_t err = esp_camera_init(&config); 
   if (err != ESP_OK) 
   { 
      Serial.printf("Erro na câmera: 0x%x", err); 
      while (true); 
   }

   reconectarMQTT();
}

void loop() {
  reconectarWiFi(); 
  reconectarMQTT(); 
  mqtt.loop();

  unsigned long instanteAtual = millis(); 
  if (instanteAtual > instanteAnterior + 1000) { 
    Serial.println("+1 segundos"); 
    Serial.println("Enviando imagem...");
    tirarFotoEEnviarParaMQTT();
    instanteAnterior = instanteAtual;
  }
}