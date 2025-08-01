// Define pins for L298 motor driver
const int motor1Pin1 = 3;  // IN1 for Motor 1
const int motor1Pin2 = 4;  // IN2 for Motor 1
const int motor2Pin1 = 5;  // IN3 for Motor 2
const int motor2Pin2 = 6;  // IN4 for Motor 2

// Analog pins for the sensors
int analogPin1 = A1;  // Sensor for Motor 1
int analogPin2 = A0;  // Sensor for Motor 2

// Variables to store sensor values
int sensorValue1 = 0;
int sensorValue2 = 0;
int scaledValue1 = 0;
int scaledValue2 = 0;

// Initial desired values for each motor (updated from Python)
int desiredValue1 = 160;  // Target for Motor 1 (will be updated from Python)
int desiredValue2 = 114;  // Target for Motor 2 (will be updated from Python)
int tolerance = 1;  // Tolerance for the target value

// Direction calibration variables
bool forwardIncreases1;
bool forwardIncreases2;

void setup() {
  Serial.begin(9600);  // Serial communication with Python
  
  // Set motor pins as outputs
  pinMode(motor1Pin1, OUTPUT);
  pinMode(motor1Pin2, OUTPUT);
  pinMode(motor2Pin1, OUTPUT);
  pinMode(motor2Pin2, OUTPUT);

  // Calibrate motors to determine which direction increases sensor value
  calibrateMotor1();
  calibrateMotor2();
}

void loop() {
  // Check for incoming data from Python
  if (Serial.available() > 0) {
    // Read incoming data and extract desired values (assumes data sent as "desiredValue1 desiredValue2")
    String input = Serial.readStringUntil('\n');  // Read the entire line
    int separator = input.indexOf(' ');  // Find the space between the values
    if (separator != -1) {
      desiredValue1 = input.substring(0, separator).toInt();  // Extract first value
      desiredValue2 = input.substring(separator + 1).toInt();  // Extract second value
      Serial.println("Received Desired Values: " + String(desiredValue1) + ", " + String(desiredValue2));
    }
  }

  // Read sensor values for both motors and map them to a range of 1 to 100
  sensorValue1 = analogRead(analogPin1);
  sensorValue2 = analogRead(analogPin2);
  
  scaledValue1 = map(sensorValue1, 0, 1023, 1, 256);
  scaledValue2 = map(sensorValue2, 0, 1023, 1, 256);

  // Print current sensor values and targets
  Serial.print("Motor 1 - Current Value: ");
  Serial.print(scaledValue1);
  Serial.print(" | Target: ");
  Serial.println(desiredValue1);

  Serial.print("Motor 2 - Current Value: ");
  Serial.print(scaledValue2);
  Serial.print(" | Target: ");
  Serial.println(desiredValue2);

  // Adjust each motor to reach its target
  adjustMotor1();
  adjustMotor2();
  
  delay(30); // 30ms delay between updates
}

void calibrateMotor1() {
  int initialValue1 = analogRead(analogPin1);
  int initialScaled1 = map(initialValue1, 0, 1023, 1, 256);
  
  // Rotate Motor 1 forward slightly and check change
  digitalWrite(motor1Pin1, HIGH);
  digitalWrite(motor1Pin2, LOW);
  delay(50);
  stopMotor1();

  int newValue1 = analogRead(analogPin1);
  int newScaled1 = map(newValue1, 0, 1023, 1, 256);
  
  forwardIncreases1 = (newScaled1 > initialScaled1);
  Serial.print("Motor 1 - Forward increases value: ");
  Serial.println(forwardIncreases1);
}

void calibrateMotor2() {
  int initialValue2 = analogRead(analogPin2);
  int initialScaled2 = map(initialValue2, 0, 1023, 1, 256);
  
  // Rotate Motor 2 forward slightly and check change
  digitalWrite(motor2Pin1, HIGH);
  digitalWrite(motor2Pin2, LOW);
  delay(50);
  stopMotor2();

  int newValue2 = analogRead(analogPin2);
  int newScaled2 = map(newValue2, 0, 1023, 1, 256);
  
  forwardIncreases2 = (newScaled2 > initialScaled2);
  Serial.print("Motor 2 - Forward increases value: ");
  Serial.println(forwardIncreases2);
}

void adjustMotor1() {
  unsigned long startTime = millis();  // Start time for timeout

  while (true) {
    // Update Motor 1 sensor value
    sensorValue1 = analogRead(analogPin1);
    scaledValue1 = map(sensorValue1, 0, 1023, 1, 256);
    
    Serial.print("Motor 1 - Current Value: ");
    Serial.print(scaledValue1);
    Serial.print(" | Target: ");
    Serial.println(desiredValue1);

    // Check if the value is already at the desired level within tolerance
    if (scaledValue1 >= (desiredValue1 - tolerance) && scaledValue1 <= (desiredValue1 + tolerance)) {
      stopMotor1();
      break;
    }

    // Move Motor 1 in the correct direction
    if (scaledValue1 < desiredValue1) {
      if (forwardIncreases1) {
        rotateForward1();
      } else {
        rotateBackward1();
      }
    } else {
      if (forwardIncreases1) {
        rotateBackward1();
      } else {
        rotateForward1();
      }
    }

    // Rotate motor for 20ms
    delay(60);

    // Stop the motor for 50ms to check sensor value
    stopMotor1();
    delay(5);
    
    // Update sensor value after stop
    sensorValue1 = analogRead(analogPin1);
    scaledValue1 = map(sensorValue1, 0, 1023, 1, 256);

    // Timeout condition (5 seconds)
    if (millis() - startTime > 5000) {
      Serial.println("Motor 1 Timeout reached! Stopping motor.");
      stopMotor1();
      break;
    }
  }
}

void adjustMotor2() {
  unsigned long startTime = millis();  // Start time for timeout

  while (true) {
    // Update Motor 2 sensor value
    sensorValue2 = analogRead(analogPin2);
    scaledValue2 = map(sensorValue2, 0, 1023, 1, 256);
    
    Serial.print("Motor 2 - Current Value: ");
    Serial.print(scaledValue2);
    Serial.print(" | Target: ");
    Serial.println(desiredValue2);

    // Check if the value is already at the desired level within tolerance
    if (scaledValue2 >= (desiredValue2 - tolerance) && scaledValue2 <= (desiredValue2 + tolerance)) {
      stopMotor2();
      break;
    }

    // Move Motor 2 in the correct direction
    if (scaledValue2 < desiredValue2) {
      if (forwardIncreases2) {
        rotateForward2();
      } else {
        rotateBackward2();
      }
    } else {
      if (forwardIncreases2) {
        rotateBackward2();
      } else {
        rotateForward2();
      }
    }

    // Rotate motor for 20ms
    delay(15);

    // Stop the motor for 50ms to check sensor value
    stopMotor2();
    delay(5);
    
    // Update sensor value after stop
    sensorValue2 = analogRead(analogPin2);
    scaledValue2 = map(sensorValue2, 0, 1023, 1, 256);

    // Timeout condition (5 seconds)
    if (millis() - startTime > 5000) {
      Serial.println("Motor 2 Timeout reached! Stopping motor.");
      stopMotor2();
      break;
    }
  }
}

void rotateForward1() {
  Serial.println("Motor 1 - Rotating Forward");
  digitalWrite(motor1Pin1, HIGH);
  digitalWrite(motor1Pin2, LOW);
}

void rotateBackward1() {
  Serial.println("Motor 1 - Rotating Backward");
  digitalWrite(motor1Pin1, LOW);
  digitalWrite(motor1Pin2, HIGH);
}

void stopMotor1() {
  Serial.println("Motor 1 - Stopping");
  digitalWrite(motor1Pin1, LOW);
  digitalWrite(motor1Pin2, LOW);
}

void rotateForward2() {
  Serial.println("Motor 2 - Rotating Forward");
  digitalWrite(motor2Pin1, HIGH);
  digitalWrite(motor2Pin2, LOW);
}

void rotateBackward2() {
  Serial.println("Motor 2 - Rotating Backward");
  digitalWrite(motor2Pin1, LOW);
  digitalWrite(motor2Pin2, HIGH);
}

void stopMotor2() {
  Serial.println("Motor 2 - Stopping");
  digitalWrite(motor2Pin1, LOW);
  digitalWrite(motor2Pin2, LOW);
}
