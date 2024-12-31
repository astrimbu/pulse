#define MOISTURE_SENSORS 6  // 6 soil moisture sensors
#define FLOAT_SENSORS 2     // 2 humidity tray float sensors
#define WATER_PUMPS 8       // 6 plant pumps + 2 humidity tray pumps
#define MOISTURE_LEDS 6    // One LED per moisture sensor
#define FLOAT_LEDS 2      // One LED per float sensor

// Calibration values for capacitive soil moisture sensor
const int AIR_VALUE = 620;    // Value when sensor is in air
const int WATER_VALUE = 310;  // Value when sensor is in water
const int READINGS_PER_SENSOR = 4;  // Number of readings to average

// Pin definitions
const int moisturePins[] = {A0, A1, A2, A3, A4, A5};  // Soil moisture sensors
const int floatPins[] = {2, 3};  // Float sensors
const int moistureLedPins[] = {22, 24, 26, 28, 30, 32};  // LED pins for moisture warnings

void setup() {
  Serial.begin(9600);
  
  // Configure pins  
  for(int i = 0; i < FLOAT_SENSORS; i++) {
    pinMode(floatPins[i], INPUT_PULLUP);
  }
  
  // Configure analog reference
  analogReference(DEFAULT);
  
  // Wait a moment for serial to stabilize
  delay(1000);
  
  // Send startup message repeatedly until connection is established
  while (!Serial) {
    ; // Wait for serial port to connect
  }
  
  // Send READY message multiple times to ensure it's received
  for(int i = 0; i < 3; i++) {
    Serial.println("READY");
    delay(100);
  }
  
  // Configure LED pins
  for(int i = 0; i < MOISTURE_LEDS; i++) {
    pinMode(moistureLedPins[i], OUTPUT);
    digitalWrite(moistureLedPins[i], LOW);
  }
}

int readMoistureSensor(int pin) {
    long sum = 0;
    int validReadings = 0;
    int lastReading = -1;
    
    for(int i = 0; i < READINGS_PER_SENSOR; i++) {
        int reading = analogRead(pin);
        
        if(reading > 1000) {
            return -1;  // Disconnected
        }
        
        if(lastReading != -1 && abs(reading - lastReading) > 50) {
            return -1;  // Unstable reading
        }
        
        sum += reading;
        validReadings++;
        lastReading = reading;
        delay(10);
    }
    
    if(validReadings == 0) return -1;
    return sum / validReadings;
}

void sendSensorData() {
    Serial.println("BEGIN>");
    
    // Debug output before sending data
    Serial.println("DEBUG: Starting sensor data transmission");
    
    // Read moisture sensors
    for(int i = 0; i < MOISTURE_SENSORS; i++) {
        int rawValue = readMoistureSensor(moisturePins[i]);
        
        Serial.print("M");
        Serial.print(i + 1);
        Serial.print(":");
        
        if(rawValue != -1 && rawValue < 1000) {
            int moisturePercent = map(constrain(rawValue, WATER_VALUE, AIR_VALUE), 
                                  AIR_VALUE, WATER_VALUE, 0, 100);
            
            // Control LED based on moisture level
            digitalWrite(moistureLedPins[i], moisturePercent < 25 ? HIGH : LOW);
            
            Serial.print(moisturePercent);
            Serial.print("|");
            Serial.print(rawValue);
        } else {
            Serial.print("NC");
        }
        
        if(i < MOISTURE_SENSORS-1) Serial.print(",");
    }
    
    // Debug output for float sensors
    for(int i = 0; i < FLOAT_SENSORS; i++) {
        int floatValue = !digitalRead(floatPins[i]);
        
        Serial.print(",F");
        Serial.print(i + 1);
        Serial.print(":");
        Serial.print(floatValue);
        
        // Debug output for each float sensor
        Serial.print(" (Pin ");
        Serial.print(floatPins[i]);
        Serial.print(" = ");
        Serial.print(digitalRead(floatPins[i]));
        Serial.println(")");
    }
    
    Serial.println("<END");
}

void loop() {
  // Add debug output
  Serial.println("DEBUG: Starting sensor reading cycle");
  
  // Read and send sensor data
  sendSensorData();
  
  // Reduce delay to 500ms for more frequent updates
  delay(500);
}
