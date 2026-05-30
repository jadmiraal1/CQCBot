#include "Arduino_RouterBridge.h"

// The ELEGOO sensor extension board labels this header as P9.
const int ULTRASONIC_PIN = 9;
const unsigned long ECHO_TIMEOUT_US = 30000;

String readDistance(String command);
float measureDistanceCm();

void setup() {
  Bridge.begin();
  Monitor.begin();
  Bridge.provide_safe("readDistance", readDistance);
  Monitor.println("UltraSonicTest ready on P9");
}

void loop() {
  delay(50);
}

String readDistance(String command) {
  float distanceCm = measureDistanceCm();

  if (distanceCm < 0) {
    return "timeout";
  }

  float distanceIn = distanceCm / 2.54;
  return "cm=" + String(distanceCm, 1) + " in=" + String(distanceIn, 1);
}

float measureDistanceCm() {
  pinMode(ULTRASONIC_PIN, OUTPUT);
  digitalWrite(ULTRASONIC_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(ULTRASONIC_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(ULTRASONIC_PIN, LOW);

  pinMode(ULTRASONIC_PIN, INPUT);
  unsigned long durationUs = pulseIn(ULTRASONIC_PIN, HIGH, ECHO_TIMEOUT_US);

  if (durationUs == 0) {
    return -1;
  }

  return durationUs / 58.0;
}
