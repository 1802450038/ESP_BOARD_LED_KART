#include <Arduino.h>
#include <ESP32-HUB75-MatrixPanel-I2S-DMA.h>
#include <WiFi.h>
#include <esp_now.h>
#include <Preferences.h>
#include <LittleFS.h>
#include <ESPAsyncWebServer.h>
#include <ESPmDNS.h>
#include <ArduinoJson.h>
#include <esp_wifi.h>
#include <Adafruit_NeoPixel.h>

// ======================= PINOS DE HARDWARE =======================
#define SETUP_BTN_PIN 17  // Botão para Setup/Reset
#define RGB_LED_PIN   48  // LED RGB nativo
#define NUM_LEDS      1

// SEUS PINOS DE DISPLAY ORIGINAIS
#define R1_PIN 3
#define B1_PIN 4
#define R2_PIN 5
#define B2_PIN 6
#define A_PIN 7
#define C_PIN 8
#define CLK_PIN 9
#define OE_PIN 10
#define G1_PIN 11
#define G2_PIN 12
#define B_PIN 13
#define D_PIN 14
#define LAT_PIN 15 
#define E_PIN -1

#define PANEL_RES_X 64
#define PANEL_RES_Y 32
#define PANEL_CHAIN 2

// Objetos
MatrixPanel_I2S_DMA *dma_display = nullptr;
Preferences prefs;
AsyncWebServer server(80);
Adafruit_NeoPixel pixels(NUM_LEDS, RGB_LED_PIN, NEO_GRB + NEO_KHZ800);

// Variáveis
bool isConfigured = false;
String currentRole = "slave";
bool forceConfigMode = false; // Botão pressionado no boot

// Botão Reset
unsigned long btnPressStartTime = 0;
bool btnIsPressed = false;

// Estruturas
typedef struct struct_message {
    int id;
    char text[64];
    int x; int y; int size;
    uint16_t color;
    bool clear;
} struct_message;

volatile bool newMsgReceived = false;
struct_message incomingMsg;

struct SlaveNode {
    int id;
    String mac;
};
std::vector<SlaveNode> slavesList;

// Variáveis Channel Hunter
int currentSlaveChannel = 1;
unsigned long lastScanTime = 0;
bool channelLocked = false;
bool shouldSaveChannel = false;

// ======================= LED RGB =======================
void setLedColor(uint8_t r, uint8_t g, uint8_t b) {
    pixels.setPixelColor(0, pixels.Color(r, g, b));
    pixels.show();
}

void blinkLed(uint8_t r, uint8_t g, uint8_t b, int times, int speed) {
    for(int i=0; i<times; i++) {
        setLedColor(r, g, b); delay(speed);
        setLedColor(0, 0, 0); delay(speed);
    }
}

// ======================= AUXILIARES =======================
uint16_t hexTo565(String hex) {
    if (hex.startsWith("#")) hex.remove(0, 1);
    long number = strtol(hex.c_str(), NULL, 16);
    int r = number >> 16; int g = number >> 8 & 0xFF; int b = number & 0xFF;
    return dma_display->color565(r, g, b);
}

void stringToMac(String macStr, uint8_t *macAddr) {
    unsigned int mac[6];
    if (sscanf(macStr.c_str(), "%x:%x:%x:%x:%x:%x", &mac[0], &mac[1], &mac[2], &mac[3], &mac[4], &mac[5]) == 6) {
        for (int i = 0; i < 6; i++) macAddr[i] = (uint8_t)mac[i];
    }
}

void addPeer(String macStr) {
    uint8_t peerAddr[6];
    stringToMac(macStr, peerAddr);
    if (esp_now_is_peer_exist(peerAddr)) return;
    esp_now_peer_info_t peerInfo = {};
    memcpy(peerInfo.peer_addr, peerAddr, 6);
    peerInfo.channel = 0; 
    peerInfo.encrypt = false;
    esp_now_add_peer(&peerInfo);
}

void removePeer(String macStr) {
    uint8_t peerAddr[6];
    stringToMac(macStr, peerAddr);
    esp_now_del_peer(peerAddr);
}

// ======================= JSON =======================
void saveSlaves() {
    JsonDocument doc;
    JsonArray array = doc.to<JsonArray>();
    for (const auto &slave : slavesList) {
        JsonObject obj = array.add<JsonObject>();
        obj["id"] = slave.id;
        obj["mac"] = slave.mac;
    }
    File file = LittleFS.open("/slaves.json", "w");
    if (file) { serializeJson(doc, file); file.close(); }
}

void loadSlaves() {
    slavesList.clear();
    if (!LittleFS.exists("/slaves.json")) {
        File f = LittleFS.open("/slaves.json", "w"); if (f) { f.print("[]"); f.close(); } return;
    }
    File file = LittleFS.open("/slaves.json", "r");
    if (!file) return;

    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, file);
    file.close();

    if (!error) {
        JsonArray array = doc.as<JsonArray>();
        for (JsonObject obj : array) {
            SlaveNode node = {obj["id"], obj["mac"].as<String>()};
            slavesList.push_back(node);
            if (currentRole == "master") addPeer(node.mac);
        }
    } else {
        File f = LittleFS.open("/slaves.json", "w"); if (f) { f.print("[]"); f.close(); }
    }
}

// ======================= CALLBACKS =======================
void OnDataRecv(const uint8_t *mac, const uint8_t *inData, int len) {
    if (len != sizeof(struct_message)) return;
    memcpy(&incomingMsg, inData, sizeof(incomingMsg));
    newMsgReceived = true; 
    
    // Se recebeu msg, o canal está certo. Trava e pede pra salvar.
    if (!channelLocked && currentRole != "master") {
        channelLocked = true; 
        shouldSaveChannel = true; 
    }
}

void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {}

// ======================= DISPLAY SETUP =======================
void setupDisplay() {
    HUB75_I2S_CFG::i2s_pins _pins = {R1_PIN, G1_PIN, B1_PIN, R2_PIN, G2_PIN, B2_PIN, A_PIN, B_PIN, C_PIN, D_PIN, E_PIN, LAT_PIN, OE_PIN, CLK_PIN};
    HUB75_I2S_CFG mxconfig(PANEL_RES_X, PANEL_RES_Y, PANEL_CHAIN, _pins);
    mxconfig.i2sspeed = HUB75_I2S_CFG::HZ_10M;
    mxconfig.driver = HUB75_I2S_CFG::FM6124;
    mxconfig.clkphase = false;

    dma_display = new MatrixPanel_I2S_DMA(mxconfig);
    dma_display->begin();
    dma_display->setBrightness8(50);
    dma_display->clearScreen();
}

// ======================= WEB SERVER =======================
void setupWebServer() {
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
        if (!isConfigured || forceConfigMode) request->send(LittleFS, "/config.html", "text/html");
        else {
            if(currentRole == "master") request->send(LittleFS, "/master.html", "text/html");
            else request->send(200, "text/plain", "Modo Slave Ativo.");
        } 
    });

    server.on("/save_config", HTTP_POST, [](AsyncWebServerRequest *request) {
        String role = request->arg("role");
        prefs.begin("config", false);
        prefs.putString("role", role);
        if (role == "master") {
            prefs.putString("ssid", request->arg("ssid"));
            prefs.putString("pass", request->arg("pass"));
        } else {
            prefs.remove("slave_ch");
        }
        prefs.putBool("configured", true);
        prefs.end();
        request->send(200, "text/plain", "Salvo! Reiniciando...");
        delay(1000); ESP.restart(); 
    });

    if (currentRole == "master" && !forceConfigMode) {
        server.on("/api/slaves", HTTP_GET, [](AsyncWebServerRequest *request){
             if(LittleFS.exists("/slaves.json")) request->send(LittleFS, "/slaves.json", "application/json");
             else request->send(200, "application/json", "[]");
        });

        server.onRequestBody([](AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total){
            if(request->url() == "/api/add_slave" && request->method() == HTTP_POST) {
                JsonDocument doc; deserializeJson(doc, data);
                int id = doc["id"]; String mac = doc["mac"];
                bool exists = false;
                for(auto &s : slavesList) if(s.id == id) { s.mac = mac; exists = true; break; }
                if(!exists) slavesList.push_back({id, mac});
                saveSlaves(); addPeer(mac);
                request->send(200, "application/json", "{\"status\":\"ok\"}");
            }
            if(request->url() == "/api/remove_slave" && request->method() == HTTP_POST) {
                JsonDocument doc; deserializeJson(doc, data);
                int id = doc["id"];
                for (auto it = slavesList.begin(); it != slavesList.end(); ) {
                  if (it->id == id) { removePeer(it->mac); it = slavesList.erase(it); } else { ++it; }
                }
                saveSlaves();
                request->send(200, "application/json", "{\"status\":\"removed\"}");
            }
            if(request->url() == "/api/send" && request->method() == HTTP_POST) {
                JsonDocument doc; deserializeJson(doc, (const char*)data);
                JsonArray arr = doc.as<JsonArray>();
                for (JsonObject cmd : arr) {
                    int targetId = cmd["id"];
                    struct_message msg;
                    msg.id = targetId;
                    strncpy(msg.text, cmd["text"].as<const char*>(), 63);
                    msg.x = cmd["x"]; msg.y = cmd["y"]; msg.size = cmd["size"];
                    msg.color = hexTo565(cmd["color"].as<String>());
                    msg.clear = true; 
                    
                    if (targetId == 0) {
                        dma_display->clearScreen();
                        dma_display->setTextSize(msg.size);
                        dma_display->setCursor(msg.x, msg.y);
                        dma_display->setTextColor(msg.color);
                        dma_display->print(msg.text);
                    } else {
                        for(auto &s : slavesList) {
                            if(s.id == targetId) {
                                uint8_t dest[6]; stringToMac(s.mac, dest);
                                esp_now_send(dest, (uint8_t *) &msg, sizeof(msg));
                                break; 
                            }
                        }
                    }
                    delay(30);
                }
                request->send(200, "application/json", "{\"status\":\"sent\"}");
            }
        });
    }
    server.begin();
}

// ======================= SETUP =======================
void setup() {
    Serial.begin(115200);
    
    pixels.begin();
    pixels.setBrightness(50);
    pinMode(SETUP_BTN_PIN, INPUT_PULLUP);

    // Botão pressionado no boot = MODO CONFIGURAÇÃO
    if (digitalRead(SETUP_BTN_PIN) == LOW) {
        forceConfigMode = true;
        setLedColor(255, 200, 0); // Amarelo
    }

    if (!LittleFS.begin(true)) Serial.println("FS Error");
    setupDisplay();

    prefs.begin("config", false);
    isConfigured = prefs.getBool("configured", false);
    currentRole = prefs.getString("role", "slave");
    String ssid = prefs.getString("ssid", "");
    String pass = prefs.getString("pass", "");
    int savedCh = prefs.getInt("slave_ch", 0);
    prefs.end();

    if (!isConfigured || forceConfigMode) {
        // --- MODO CONFIGURAÇÃO (Mensagens Originais) ---
        WiFi.mode(WIFI_AP);
        WiFi.softAP("LED_CONFIG", "12345678"); // Mantido seu SSID original
        MDNS.begin("esp32"); MDNS.addService("http", "tcp", 80);
        
        dma_display->setCursor(0, 0); dma_display->print("CFG: LED_CONFIG");
        dma_display->setCursor(0, 10); dma_display->print("IP: 192.168.4.1");
        
        setupWebServer();
    } 
    else {
        if (currentRole == "master") {
            // >>> MASTER (Mensagens Originais + LED Verde/Azul) <<<
            blinkLed(0, 255, 0, 3, 200); // Verde 3x
            
            WiFi.mode(WIFI_AP_STA);
            WiFi.begin(ssid.c_str(), pass.c_str());
            
            // --- SUA ANIMAÇÃO "CONECTANDO..." RESTAURADA ---
            dma_display->setCursor(0, 0);
            while (WiFi.status() != WL_CONNECTED) {
                // Pisca LED Azul enquanto tenta conectar
                setLedColor(0, 0, 255);
                dma_display->setCursor(0,0); dma_display->print("Conectando."); delay(500); setLedColor(0,0,0);
                dma_display->setCursor(0,0); dma_display->print("Conectando.."); delay(500);
                dma_display->setCursor(0,0); dma_display->print("Conectando..."); delay(500);
                dma_display->setCursor(0,0); dma_display->clearScreen(); delay(500);
            }
            // ------------------------------------------------

            setLedColor(0, 0, 255); // Azul Fixo = Conectado

            dma_display->fillScreen(0);
            // --- SUAS MENSAGENS DE MASTER CONECTADO ---
            dma_display->setCursor(0, 0);
            dma_display->print("REDE: " + ssid);
            
            // Fix do mDNS
            MDNS.end(); 
            if (MDNS.begin("esp32")) MDNS.addService("http", "tcp", 80);
            
            dma_display->setCursor(0, 10);
            dma_display->print("IP: " + WiFi.localIP().toString());
            dma_display->setCursor(0, 20);
            dma_display->print("END: esp32.local");
            
            if (esp_now_init() != ESP_OK) Serial.println("ESP-NOW Error");
            esp_now_register_send_cb(OnDataSent);
            loadSlaves();
        } 
        else {
            // >>> SLAVE (Mensagens Originais + LED Roxo) <<<
            blinkLed(128, 0, 128, 5, 200); // Roxo 5x
            setLedColor(0, 0, 0);
            
            WiFi.mode(WIFI_STA); 
            
            if (savedCh > 0) {
                esp_wifi_set_promiscuous(true);
                esp_wifi_set_channel(savedCh, WIFI_SECOND_CHAN_NONE);
                esp_wifi_set_promiscuous(false);
                channelLocked = true;
                currentSlaveChannel = savedCh;
            } else {
                channelLocked = false;
            }
            
            WiFi.disconnect();
            
            dma_display->fillScreen(0);
            // --- SUAS MENSAGENS DE SLAVE ---
            dma_display->setCursor(0, 0); dma_display->print("SLAVE ID?");
            dma_display->setCursor(0, 10); dma_display->print(WiFi.macAddress());
            
            if (esp_now_init() != ESP_OK) Serial.println("ESP-NOW Error");
            esp_now_register_recv_cb(OnDataRecv);
        }
        setupWebServer();
    }
}

// ======================= LOOP =======================
unsigned long lastLedBlink = 0;
bool ledState = false;

void loop() {
    unsigned long now = millis();

    // 1. MANTER mDNS ATIVO (Fix para o problema de perder conexão)
    if (!forceConfigMode && currentRole == "master") {
        // MDNS.update(); // Descomente se sua versão da lib pedir
    }

    // 2. PISCA LED AMARELO (Modo Config)
    if (forceConfigMode || (!isConfigured)) {
        if (now - lastLedBlink > 500) {
            lastLedBlink = now;
            ledState = !ledState;
            if(ledState) setLedColor(255, 200, 0); else setLedColor(0,0,0);
        }
    }

    // 3. BOTÃO FÍSICO (Quadrado de Teste & Factory Reset)
    if (digitalRead(SETUP_BTN_PIN) == LOW) {
        if (!btnIsPressed) {
            btnIsPressed = true;
            btnPressStartTime = now;
            // Quadrado 2x2 no canto (Feedback Visual)
            dma_display->drawRect(60, 28, 4, 4, dma_display->color565(255, 255, 255));
            dma_display->fillRect(60, 28, 4, 4, dma_display->color565(255, 255, 255));
        }
        
        // Segurou por 5s? RESET!
        if (now - btnPressStartTime > 5000) {
            dma_display->fillScreen(dma_display->color565(255, 0, 0)); 
            dma_display->setCursor(0, 0); dma_display->print("FACTORY");
            dma_display->setCursor(0, 10); dma_display->print("RESET...");
            delay(1000);
            
            prefs.begin("config", false); prefs.clear(); prefs.end();
            LittleFS.remove("/slaves.json"); // Opcional: apagar lista de slaves
            
            ESP.restart();
        }
    } else {
        if (btnIsPressed) {
            btnIsPressed = false;
            dma_display->fillRect(60, 28, 4, 4, 0); // Apaga quadrado
        }
    }

    // 4. DESENHA MENSAGEM
    if (newMsgReceived) {
        newMsgReceived = false; 
        if (incomingMsg.clear) dma_display->clearScreen();
        dma_display->setTextSize(incomingMsg.size);
        dma_display->setTextWrap(false);
        dma_display->setCursor(incomingMsg.x, incomingMsg.y);
        dma_display->setTextColor(incomingMsg.color);
        dma_display->print(incomingMsg.text);
    }

    // 5. SALVA CANAL (Slave)
    if (shouldSaveChannel) {
        shouldSaveChannel = false;
        prefs.begin("config", false);
        prefs.putInt("slave_ch", currentSlaveChannel);
        prefs.end();
        blinkLed(0, 255, 0, 2, 100); 
    }

    // 6. CHANNEL HUNTER (Slave)
    if (currentRole != "master" && !channelLocked) {
        if (now - lastScanTime > 150) {
            lastScanTime = now;
            currentSlaveChannel++;
            if (currentSlaveChannel > 13) currentSlaveChannel = 1;
            
            esp_wifi_set_promiscuous(true);
            esp_wifi_set_channel(currentSlaveChannel, WIFI_SECOND_CHAN_NONE);
            esp_wifi_set_promiscuous(false);
            
            // Pixel indicador discreto (Última linha)
            dma_display->drawPixel(currentSlaveChannel, 31, dma_display->color565(50, 50, 50));
            dma_display->drawPixel(currentSlaveChannel-1, 31, 0);
        }
    }

    delay(5);
}