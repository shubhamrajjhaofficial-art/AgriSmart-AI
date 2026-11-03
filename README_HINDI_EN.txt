# IoT Based Smart Agriculture System with Gemini AI

## Included
- `esp8266_smart_agriculture.ino`: ESP8266 sensor uploader + sample Modbus NPK reader
- `server.py`: Flask backend and web dashboard
- `.env.example`: API key/device-token configuration
- `requirements.txt`: Python packages

## Important hardware notes
1. The NPK probe shown earlier is labelled RS485 and 12–24 V. Use a suitable separate supply for the probe according to its exact manual. Do not power it from the ESP8266 3.3 V pin.
2. RS485 A/B connect to the converter's A/B terminals. UART pins on the converter connect to ESP8266 RX/TX as described by the exact board's pinout.
3. Some converter boards have 5 V UART logic even if the power input says a wide range. ESP8266 GPIO is NOT 5 V tolerant. Confirm the converter's UART logic voltage. If its TXD/RO output can be 5 V, use a proper level shifter or resistor divider before the ESP8266 RX pin.
4. NPK sensors vary in Modbus slave ID, baud rate, parity, and register addresses. The sketch uses example defaults (ID 1, 4800 baud, registers 0x001E–0x0020). Verify the manual before trusting readings.
5. The DHT11 is on D2, soil analog output on A0, relay signal on D1, software serial RX/TX on D5/D6, and DE/RE control on D7 in this example. Change pins to match your actual wiring.
6. Keep `AUTO_RELAY` false until you calibrate soil moisture and test the relay with no pump load. Do not let AI directly control irrigation hardware.
7. Soil percentage needs calibration. Set `SOIL_DRY_RAW` and `SOIL_WET_RAW` from your own readings.

## Run the backend on a Windows PC
1. Install Python 3.10+.
2. Extract the ZIP to a folder.
3. Open Command Prompt in that folder and run:
   `py -m venv .venv`
   `.venv\Scripts\activate`
   `pip install -r requirements.txt`
4. Copy `.env.example` to `.env`.
5. Open `.env` and put your Gemini API key after `GEMINI_API_KEY=`.
   Create a key in Google AI Studio: https://aistudio.google.com/app/apikey
   Keep this key private. Never paste it into ESP8266 code or a public website.
6. Change `DEVICE_TOKEN` in `.env` and use the exact same token in the ESP8266 sketch.
7. Find the PC's LAN IPv4 address with `ipconfig` (IPv4 Address). Set `SERVER_URL` in the sketch to:
   `http://YOUR_PC_IP:5000/api/sensors`
8. Run:
   `python server.py`
9. Open `http://YOUR_PC_IP:5000` on a computer/phone on the same Wi-Fi.
10. Allow Python through Windows Firewall on private networks if prompted.

## Arduino IDE libraries
Install via Library Manager:
- DHT sensor library (Adafruit)
- Adafruit Unified Sensor (if prompted)
- ModbusMaster
- ArduinoJson (version 6 or compatible)
ESP8266 board support package is also required.

## Test sequence
1. Start backend first; check the dashboard opens.
2. Upload ESP8266 sketch and open Serial Monitor at 115200.
3. Confirm Wi-Fi and HTTP POST result (normally 200).
4. Confirm temperature/humidity and soil readings update.
5. If N/P/K remain blank, do not guess fertilizer. Check RS485 wiring, supply, common settings, sensor manual, and converter voltage levels.
6. Press “Get AI Recommendation” after sensor readings are available.

## API routes
- `GET /api/sensors` returns latest sensor data.
- `POST /api/sensors` receives ESP8266 readings; requires `X-Device-Token`.
- `POST /api/recommend` JSON body: `{"crop":"Rice"}`; uses latest readings and Gemini API.


DARK DASHBOARD UI UPDATE (Oct 2026)
This version includes a dark green/neon AgriSmart AI interface. Extract this ZIP into a NEW folder, activate your venv, install requirements if needed, copy your existing .env values into the new folder (never share API keys), then run: python server.py. Open http://127.0.0.1:5000. Sensor readings remain blank until the ESP8266 sends real data. Pump control is disabled in this demo.
