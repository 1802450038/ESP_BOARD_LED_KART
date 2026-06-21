#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <Preferences.h>
#include "esp_websocket_client.h" 
#include <ESP32-HUB75-MatrixPanel-I2S-DMA.h>
#include <Adafruit_NeoPixel.h>
#include <ArduinoJson.h>

// ======================= PINOS DE HARDWARE =======================
#define SETUP_BTN_PIN 17 
#define RGB_LED_PIN 48   
#define NUM_LEDS 1

// SEUS PINOS DE DISPLAY ORIGINAIS
#define GND_1 -1
#define OE_PIN 13
#define LAT_PIN 12
#define CLK_PIN 11
#define D_PIN 10
#define C_PIN 9
#define B_PIN 8
#define A_PIN 7

#define GND_2 -1
#define B2_PIN 6
#define G2_PIN 5
#define R2_PIN 4
#define GND_3 -1
#define B1_PIN 3
#define G1_PIN 2
#define R1_PIN 1
#define E_PIN -1

#define PANEL_RES_X 64
#define PANEL_RES_Y 32
#define PANEL_CHAIN 2

MatrixPanel_I2S_DMA *dma_display = nullptr;
Adafruit_NeoPixel pixels(NUM_LEDS, RGB_LED_PIN, NEO_GRB + NEO_KHZ800);
WebServer server(80);
Preferences preferences;
esp_websocket_client_handle_t ws_client = NULL;

String rede_ssid, rede_senha, ws_ip, ws_porta, esp_id;
String numeroAleatorio;
bool configurado = false;

// Buffer para imagens
uint8_t *img_buffer = nullptr;
int img_buffer_idx = 0;

// Controle de Estado
bool ws_is_connected = false;
unsigned long msgRedTimer = 0;

// ======================= VARIÁVEIS DO BOTÃO =======================
unsigned long btnPressStart = 0;
bool btnIsPressed = false;
bool resetPromptActive = false;
bool btnHandled = false;

// HTML Configuration Page
const char *htmlForm = R"rawliteral(
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Configurar ESP32</title></head><body style="font-family: Arial; padding: 20px;">
<h2>Configuração da Placa</h2>
<form action="/salvar" method="POST">
  <b>Nome da Rede WiFi:</b><br><input type="text" name="ssid" required><br><br>
  <b>Senha do WiFi:</b><br><input type="password" name="senha"><br><br>
  <b>IP do Servidor Python (ex: 192.168.1.15):</b><br><input type="text" name="ip" required><br><br>
  <b>Porta (ex: 8765):</b><br><input type="text" name="porta" value="8765" required><br><br>
  <b>ID desta Placa:</b><br><input type="text" name="espid" required><br><br>
  <b>Brilho do LED (0-255):</b><br><input type="number" name="brilho" value="15" min="0" max="255" required><br><br>
  <input type="submit" value="Salvar e Reiniciar" style="padding: 10px; background: #28a745; color: white; border: none; border-radius: 5px;">
</form></body></html>
)rawliteral";

// ======================= HELPERS =======================
void setNeoPixel(uint8_t r, uint8_t g, uint8_t b) {
  pixels.setPixelColor(0, pixels.Color(r, g, b));
  pixels.show();
}

void blinkNeoPixel(uint8_t r, uint8_t g, uint8_t b, int interval) {
  static unsigned long previousMillis = 0;
  static bool ledState = false;
  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    ledState = !ledState;
    if (ledState) setNeoPixel(r, g, b);
    else setNeoPixel(0, 0, 0);
  }
}

uint16_t hexToRGB565(String hexColor) {
  if (hexColor.startsWith("#")) hexColor.remove(0, 1);
  long number = strtol(hexColor.c_str(), NULL, 16);
  return dma_display ? dma_display->color565((number >> 16) & 0xFF, (number >> 8) & 0xFF, number & 0xFF) : 0xFFFF;
}

// ======================= DISPLAY =======================
void setupDisplay() {
  HUB75_I2S_CFG::i2s_pins _pins = {R1_PIN, G1_PIN, B1_PIN, R2_PIN, G2_PIN, B2_PIN, A_PIN, B_PIN, C_PIN, D_PIN, E_PIN, LAT_PIN, OE_PIN, CLK_PIN};
  HUB75_I2S_CFG mxconfig(PANEL_RES_X, PANEL_RES_Y, PANEL_CHAIN, _pins);
  mxconfig.i2sspeed = HUB75_I2S_CFG::HZ_10M;
  mxconfig.driver = HUB75_I2S_CFG::FM6124;
  mxconfig.clkphase = false;

  dma_display = new MatrixPanel_I2S_DMA(mxconfig);
  dma_display->begin();
  dma_display->setTextWrap(true);
  
  // LÊ O BRILHO DA MEMÓRIA ANTES DE INICIAR (Default: 15)
  preferences.begin("config", true);
  int brilho_salvo = preferences.getInt("brilho", 15);
  preferences.end();
  
  dma_display->setBrightness8(brilho_salvo);
  dma_display->clearScreen();
}

void printDisplay(String message, int textSize, uint16_t color) {
  dma_display->fillScreen(0);
  int cursor_x = 0;
  int cursor_y = 0;
  int char_width = 5 * textSize;
  int char_height = 8 * textSize;

  for (int i = 0; i < message.length(); i++) {
    char c = message[i];
    if (c == '\n') {
      cursor_x = 0;
      cursor_y += char_height; 
    } else {
      dma_display->drawChar(cursor_x, cursor_y, c, color, 0, textSize);
      cursor_x += char_width;
    }
  }
}

void printDisplayLinhas(JsonArray linhas, int textSize) {
  dma_display->fillScreen(0);
  int cursor_y = 0;
  int char_width = 5 * textSize;
  int char_height = 8 * textSize;

  for (JsonObject linha : linhas) {
    String texto = linha["texto"] | "";
    String corHex = linha["cor"] | "#FFFFFF";
    uint16_t corConvertida = hexToRGB565(corHex);

    int cursor_x = 0;
    for (int i = 0; i < texto.length(); i++) {
      char c = texto[i];
      dma_display->drawChar(cursor_x, cursor_y, c, corConvertida, 0, textSize);
      cursor_x += char_width;
    }
    cursor_y += char_height; 
  }
}

// ======================= LÓGICA DO BOTÃO =======================
void checarBotao() {
  bool taApertado = (digitalRead(SETUP_BTN_PIN) == LOW);

  if (taApertado && !btnIsPressed) {
    btnIsPressed = true;
    btnPressStart = millis();
    btnHandled = false;
    if (!resetPromptActive) {
      dma_display->clearScreen();
      dma_display->fillRect(31, 15, 2, 2, dma_display->color565(255, 255, 255));
    }
  } 
  else if (!taApertado && btnIsPressed) {
    btnIsPressed = false;
    if (!btnHandled) {
      if (resetPromptActive) {
        resetPromptActive = false;
        dma_display->clearScreen();
      } else {
        dma_display->clearScreen();
      }
    }
  }

  if (taApertado && btnIsPressed) {
    unsigned long tempoSegurado = millis() - btnPressStart;
    if (!resetPromptActive && tempoSegurado >= 5000 && !btnHandled) {
      resetPromptActive = true;
      btnHandled = true; 
      printDisplay("RESET?\nS: Segure\nN: Clique", 1, dma_display->color565(255, 0, 0));
    }
    else if (resetPromptActive && tempoSegurado >= 2000 && !btnHandled) {
      btnHandled = true;
      printDisplay("Limpando...", 1, dma_display->color565(255, 0, 0));
      preferences.begin("config", false);
      preferences.clear();
      preferences.end();
      delay(1500);
      ESP.restart(); 
    }
  }
}

// ======================= WEBSOCKET HANDLER =======================
static void websocket_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data) {
  esp_websocket_event_data_t *data = (esp_websocket_event_data_t *)event_data;
  switch (event_id) {
  case WEBSOCKET_EVENT_CONNECTED:
    ws_is_connected = true;
    esp_websocket_client_send_text(ws_client, esp_id.c_str(), esp_id.length(), portMAX_DELAY);
    break;
    
  case WEBSOCKET_EVENT_DATA:
    if (data->op_code == 1) {
      resetPromptActive = false; 
      msgRedTimer = millis(); 
      String payload = "";
      for (int i = 0; i < data->data_len; i++) payload += (char)data->data_ptr[i];

      JsonDocument doc;
      if (!deserializeJson(doc, payload)) {
        
        // NOVO: CHECA SE É COMANDO DE CONFIGURAÇÃO VIA PYTHON
        if (doc.containsKey("comando") && doc["comando"] == "config") {
            if (doc.containsKey("brilho")) {
                int novo_brilho = doc["brilho"].as<int>();
                
                // Salva na memória
                preferences.begin("config", false);
                preferences.putInt("brilho", novo_brilho);
                preferences.end();
                
                // Aplica imediatamente no painel!
                if (dma_display) {
                    dma_display->setBrightness8(novo_brilho);
                }
            }
        } 
        // SE NÃO FOR CONFIGURAÇÃO, EXIBE O TEXTO NORMALMENTE
        else {
            int tamanho = doc["tamanho"] | 1;
            JsonArray linhas = doc["linhas"];
            printDisplayLinhas(linhas, tamanho);
        }
      }
    }
    else if (data->op_code == 2) {
      resetPromptActive = false;
      if (data->payload_offset == 0) {
        if (img_buffer != nullptr) { free(img_buffer); img_buffer = nullptr; }
        img_buffer = (uint8_t*) malloc(data->payload_len);
        img_buffer_idx = 0;
      }

      if (img_buffer != nullptr) {
        memcpy(img_buffer + data->payload_offset, data->data_ptr, data->data_len);
        img_buffer_idx += data->data_len;

        if (img_buffer_idx == data->payload_len) {
          msgRedTimer = millis();
          if (data->payload_len > 3 && img_buffer[0] == 'I') {
            uint8_t w = img_buffer[1];
            uint8_t h = img_buffer[2];
            int idx = 3;
            for (int y = 0; y < h; y++) {
              for (int x = 0; x < w; x++) {
                if (idx + 2 < data->payload_len) {
                  uint8_t r = img_buffer[idx++];
                  uint8_t g = img_buffer[idx++];
                  uint8_t b = img_buffer[idx++];
                  dma_display->drawPixel(x, y, dma_display->color565(r, g, b));
                }
              }
            }
          }
          free(img_buffer);
          img_buffer = nullptr;
        }
      }
    }
    break;
    
  case WEBSOCKET_EVENT_DISCONNECTED:
    ws_is_connected = false;
    if (img_buffer != nullptr) { free(img_buffer); img_buffer = nullptr; }
    break;
  }
}

void setup() {
  delay(1000);
  Serial.begin(115200);

  pinMode(SETUP_BTN_PIN, INPUT_PULLUP);

  pixels.begin();
  pixels.setBrightness(40);
  setNeoPixel(0, 0, 0);

  setupDisplay();

  preferences.begin("config", false);
  rede_ssid = preferences.getString("ssid", "");
  rede_senha = preferences.getString("senha", "");
  ws_ip = preferences.getString("ip", "");
  ws_porta = preferences.getString("porta", "");
  esp_id = preferences.getString("espid", "");
  
  numeroAleatorio = preferences.getString("rand", "");
  if (numeroAleatorio == "") {
    numeroAleatorio = String(random(1000, 9999));
    preferences.putString("rand", numeroAleatorio);
  }
  preferences.end();

  if (rede_ssid == "" || ws_ip == "") {
    String nomeAP = "esp-settings-" + numeroAleatorio;
    WiFi.softAP(nomeAP.c_str());
    if (MDNS.begin(("esp32" + numeroAleatorio).c_str())) {}

    // >>> NOVO: Exibe o endereço de configuração no painel de LED <<<
    String msg_setup = " SETUP AP\n\n esp32" + numeroAleatorio + "\n .local";
    printDisplay(msg_setup, 1, dma_display->color565(0, 255, 255)); 

    server.on("/", []() { server.send(200, "text/html", htmlForm); });
    server.on("/salvar", HTTP_POST, []() {
      preferences.begin("config", false);
      preferences.putString("ssid", server.arg("ssid"));
      preferences.putString("senha", server.arg("senha"));
      preferences.putString("ip", server.arg("ip"));
      preferences.putString("porta", server.arg("porta"));
      preferences.putString("espid", server.arg("espid"));
      preferences.putInt("brilho", server.arg("brilho").toInt());
      preferences.end();
      server.send(200, "text/html", "<h2>Configuracoes salvas! Reiniciando...</h2>");
      delay(1500);
      ESP.restart(); 
    });
    server.begin();
  } else {
    configurado = true;
    
    String msg_id = "PLACA ID:\n  " + esp_id;
    printDisplay(msg_id, 1, dma_display->color565(0, 255, 255)); 
    
    WiFi.setAutoReconnect(true);
    WiFi.begin(rede_ssid.c_str(), rede_senha.c_str());

    while (WiFi.status() != WL_CONNECTED) {
      blinkNeoPixel(0, 0, 255, 255); 
      delay(300);
    }

    String uri = "ws://" + ws_ip + ":" + ws_porta;
    esp_websocket_client_config_t websocket_cfg = {};
    websocket_cfg.uri = uri.c_str();
    websocket_cfg.buffer_size = 16384;

    ws_client = esp_websocket_client_init(&websocket_cfg);
    esp_websocket_register_events(ws_client, WEBSOCKET_EVENT_ANY, websocket_event_handler, (void *)ws_client);
    esp_websocket_client_start(ws_client);
  }
}

void loop() {
  checarBotao();

  if (!configurado) {
    server.handleClient();
    blinkNeoPixel(255, 255, 0, 255); 
  } else {
    if (WiFi.status() != WL_CONNECTED) {
      blinkNeoPixel(255, 0, 0, 255);
    } else if (ws_is_connected) {
      if (millis() - msgRedTimer < 800) blinkNeoPixel(255, 255, 0, 400); 
      else blinkNeoPixel(0, 255, 0, 800); 
    } else {
      blinkNeoPixel(128, 0, 128, 200); 
    }
  }
  delay(1); 
}