#include "Arduino_RouterBridge.h"

// Common ELEGOO 4-wheel rover shield pin map. This is the TB6612-style map
// used by many ELEGOO Smart Robot Car shields: one PWM pin, one direction pin,
// and a shared standby/enable pin.
const int LEFT_PWM = 5;
const int RIGHT_PWM = 6;
const int LEFT_DIRECTION = 7;
const int RIGHT_DIRECTION = 8;
const int MOTOR_STANDBY = 3;

const unsigned long COMMAND_TIMEOUT_MS = 750;
unsigned long lastCommandMs = 0;

String drive(String command);
void setMotorPair(int pwmPin, int directionPin, int speed);
void stopMotors();

void setup() {
  pinMode(LEFT_PWM, OUTPUT);
  pinMode(RIGHT_PWM, OUTPUT);
  pinMode(LEFT_DIRECTION, OUTPUT);
  pinMode(RIGHT_DIRECTION, OUTPUT);
  pinMode(MOTOR_STANDBY, OUTPUT);

  stopMotors();
  digitalWrite(MOTOR_STANDBY, HIGH);

  Bridge.begin();
  Monitor.begin();
  Bridge.provide_safe("drive", drive);
  Monitor.println("LaptopMovement motor bridge ready");
}

void loop() {
  if (millis() - lastCommandMs > COMMAND_TIMEOUT_MS) {
    stopMotors();
  }
}

String drive(String command) {
  int commaIndex = command.indexOf(',');
  if (commaIndex < 0) {
    stopMotors();
    return "bad-command";
  }

  int leftSpeed = command.substring(0, commaIndex).toInt();
  int rightSpeed = command.substring(commaIndex + 1).toInt();
  leftSpeed = constrain(leftSpeed, -255, 255);
  rightSpeed = constrain(rightSpeed, -255, 255);

  digitalWrite(MOTOR_STANDBY, HIGH);
  setMotorPair(LEFT_PWM, LEFT_DIRECTION, leftSpeed);
  setMotorPair(RIGHT_PWM, RIGHT_DIRECTION, rightSpeed);
  lastCommandMs = millis();

  return "leftActual=" + String(leftSpeed) + " rightActual=" + String(rightSpeed);
}

void setMotorPair(int pwmPin, int directionPin, int speed) {
  int pwm = abs(speed);

  digitalWrite(directionPin, speed >= 0 ? HIGH : LOW);
  analogWrite(pwmPin, pwm);
}

void stopMotors() {
  analogWrite(LEFT_PWM, 0);
  analogWrite(RIGHT_PWM, 0);
}
