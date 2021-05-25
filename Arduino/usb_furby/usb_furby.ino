/*
 * Copyright (C) 2021 by Paul-Louis Ageneau
 * paul-louis (at) ageneau (dot) org
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

class Furby {
    // ---------- Pin setup ----------

    const int HOME_SENSOR_PIN   = 2;
    const int MOTOR_PWM_PIN     = 3;
    const int MOTOR_STANDBY_PIN = 4;
    const int MOTOR_FORWARD_PIN = 5;
    const int MOTOR_REVERSE_PIN = 6;
    const int LED_PIN           = 7;

    const int INT_LIGHT_SENSOR_PIN = A0;
    const int EXT_LIGHT_SENSOR_PIN = A1;

    // ---------- Constants ----------

    const int MOTOR_POWER_MIN       = 153; // ~3V
    const int MOTOR_POWER_MAX       = 255;
    const int MOTOR_STEPS           = 416;
    const int MOTOR_STEPS_POWER_MAX = 50;
    const int MOTOR_STEPS_TOLERANCE = 3;
    const int HOME_STEPS_TOLERANCE  = 3;
    const unsigned long MOTOR_IDLE_DELAY = 100;

    const int INT_LIGHT_SENSOR_LOW_THRESHOLD = 90;
    const int INT_LIGHT_SENSOR_HIGH_THRESHOLD = 100;

    const int MOTOR_FORWARD  = 1;
    const int MOTOR_BACKWARD = -1;
    const int MOTOR_IDLE     = 0;

    // ----------

    int currentStep    = 0;          // Rotation step counter
    int targetStep     = 0;          // Target rotation step
    int motorDirection = MOTOR_IDLE; // Current motor state
    unsigned long motorLastTime = 0;

    // ----------

    int distance(int to) const {
        return ((currentStep - to) + MOTOR_STEPS/2 + MOTOR_STEPS) % MOTOR_STEPS - MOTOR_STEPS/2;
    }

    void motor(int value) { // value 0 means brake
        digitalWrite(MOTOR_FORWARD_PIN, value >= 0 ? HIGH : LOW);
        digitalWrite(MOTOR_REVERSE_PIN, value <= 0 ? HIGH : LOW);
        analogWrite(MOTOR_PWM_PIN, constrain(abs(value), 0, 255));
    }

public:
    void begin() {
        pinMode(HOME_SENSOR_PIN, INPUT_PULLUP);
        pinMode(MOTOR_PWM_PIN, OUTPUT);
        pinMode(MOTOR_STANDBY_PIN, OUTPUT);
        pinMode(MOTOR_FORWARD_PIN, OUTPUT);
        pinMode(MOTOR_REVERSE_PIN, OUTPUT);
        pinMode(LED_PIN, OUTPUT);

        digitalWrite(MOTOR_STANDBY_PIN, HIGH);
    }

    void home() {
        motor(MOTOR_POWER_MAX);
        while(digitalRead(HOME_SENSOR_PIN) == LOW) {}
        delay(200);
        while(digitalRead(HOME_SENSOR_PIN) == HIGH) {}
        motor(0);

        currentStep = 0;
        motorDirection = MOTOR_FORWARD;
        motorLastTime = millis();
    }

    void update() {
        // Count steps using the internal light sensor
        if(motorDirection != MOTOR_IDLE) {
            digitalWrite(LED_PIN, HIGH); // turn the LED on
            int value = analogRead(INT_LIGHT_SENSOR_PIN); // measure
            digitalWrite(LED_PIN, LOW); // turn the LED off

            int parity = currentStep % 2;

            // Reset current position in case of drift
            if(distance(0) > HOME_STEPS_TOLERANCE && digitalRead(HOME_SENSOR_PIN) == LOW) {
              currentStep = 0;
            }
            
            if((parity == 0 && value > INT_LIGHT_SENSOR_HIGH_THRESHOLD) ||
               (parity == 1 && value <= INT_LIGHT_SENSOR_LOW_THRESHOLD)) {
                currentStep = (MOTOR_STEPS + currentStep + motorDirection) % MOTOR_STEPS;
            }
        }

        // Compare current position with target
        int dist = distance(targetStep);
        int dir = dist < 0 ? MOTOR_FORWARD : MOTOR_BACKWARD;
        if(abs(dist) > MOTOR_STEPS_TOLERANCE && (motorDirection == MOTOR_IDLE || motorDirection == dir)) {
            // Move to target
            motorDirection = dir;
            motorLastTime = millis();
            int power = map(constrain(abs(dist),
                            MOTOR_STEPS_TOLERANCE, MOTOR_STEPS_POWER_MAX),
                            MOTOR_STEPS_TOLERANCE, MOTOR_STEPS_POWER_MAX, MOTOR_POWER_MIN, MOTOR_POWER_MAX);
            motor(motorDirection * power);
        }
        else {
            // Target is reached or motor is in the wrong direction
            motor(0);
            
            // The motor does not stop instantaneously
            if(millis() - motorLastTime >= MOTOR_IDLE_DELAY) {
              motorDirection = MOTOR_IDLE;
            }
        }
    }

    int target(int value) {
        targetStep = (value % MOTOR_STEPS + MOTOR_STEPS) % MOTOR_STEPS;
        return targetStep;
    }

    int target() const {
        return targetStep;
    }

    int current() const {
        return currentStep;
    }

    bool reached() const {
        return abs(distance(targetStep)) <= MOTOR_STEPS_TOLERANCE;
    }

    int light() const {
        int value = analogRead(EXT_LIGHT_SENSOR_PIN);
        return map(value, 0, 1023, 0, 255);
    }
};

Furby furby;
String inputString = "";
bool targetReached = true;
bool stopped = false;

// ----------

void setup() {
    Serial.begin(9600);
    furby.begin();
    furby.home();

    // Close the eyes
    furby.target(180);
}

void loop() {
     // Read commands on serial
    while(Serial.available()) {
        char chr = (char)Serial.read();
        if(chr != '\n') {
            if(chr != '\r')
                inputString+= chr;
        }
        else if(inputString.length() > 0) {
            // Parse command
            char cmd = toupper(inputString[0]);
            String param;
            int pos = 1;
            while(pos < inputString.length() && inputString[pos] == ' ') ++pos;
            param = inputString.substring(pos);

            // Execute command
            switch(cmd) {
                case 'H':
                    furby.home();
                    Serial.println("H");
                    break;
                case 'M':
                    furby.target(param.toInt());
                    targetReached = false;
                    stopped = false;
                    break;
                case 'S':
                    furby.target(furby.current());
                    targetReached = false;
                    stopped = true;
                    break;
                case 'C':
                    Serial.print("C ");
                    Serial.println(furby.current());
                    break;
                case 'L':
                    Serial.print("L ");
                    Serial.println(furby.light());
                    break;
                default:
                    Serial.println("E");
                    break;
            }

            inputString = "";
        }
    }

    furby.update();

    if(!targetReached && furby.reached()) {
        targetReached = true;
        if(stopped) Serial.print("S ");
        else Serial.print("M ");
        Serial.println(furby.target());
    }
}
