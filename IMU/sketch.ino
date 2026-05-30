// SPDX-License-Identifier: MPL-2.0
#include <Arduino_Modulino.h>
#include <Arduino_RouterBridge.h>

ModulinoMovement movement;
float ax, ay, az;                  // acceleration in g
unsigned long previousMillis = 0;
const long interval = 50;          // 20Hz — fast enough for vibration
int has_movement = 0;

void setup() {
  Bridge.begin();
  Modulino.begin(Wire1);
  while (!movement.begin()) {
    delay(1000);
  }
}

void loop() {
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    has_movement = movement.update();
    if (has_movement == 1) {
      ax = movement.getX();
      ay = movement.getY();
      az = movement.getZ();
      Bridge.notify("record_sensor_movement", ax, ay, az);
    }
  }
}
