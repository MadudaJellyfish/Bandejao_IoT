# Bandejao_IoT
Esse repositório contém os códigos que estão relacionados ao controle de lotação do Bandejão da PUC-Rio
//Luciana
//Maria Eduarda
//Mayara

Luciana:


Esse código implementa um sistema em ESP32-S3 que integra leitura de cartão RFID, comunicação via Wi-Fi/MQTT e exibição de informações em uma tela e-paper. Quando um cartão RFID é aproximado, o ESP32 lê o UID e envia esse identificador para um servidor via MQTT, que verifica se o usuário possui cadastro.

Se o usuário estiver cadastrado, o sistema recebe os dados (nome e saldo), exibe uma mensagem de boas-vindas na tela com o saldo anterior e o saldo restante após o desconto, e envia a atualização de saldo de volta ao servidor. Caso o usuário não possua cadastro, a tela exibe uma mensagem informando que é necessário realizar o cadastro.

Além disso, o código aciona uma campainha simples (buzzer) sempre que uma mensagem MQTT é recebida, fornece uma tela inicial solicitando a aproximação do cartão e mantém a conexão Wi-Fi e MQTT ativa durante toda a execução.


Maria Eduarda:

Esse repositório contém os códigos que estão relacionados com o processamento de imagens capturadas pela câmera do ESP32 pela biblioteca YOLO
A aplicação consiste em um programa sendo executado dentro da placa ESP32-S3-CAM capturando imagens e essas imagens são recebidas por a aplicação em python main.py através do protocolo MQTT de mensagens. Dentro da aplicação main.py a biblioteca YOLO foi utilizada para contabilizar a média de pessoas no stream de imagens em um ambiente.

Mayara: 

Essa parte dos códigos é responsável pelo servidor. Ele faz o site funcionar, se conectando ao banco de dados, tem o node-red que se comunica com o código da Maria Eduarda e da Luciana e colocam no banco de dados as informações passadas.
