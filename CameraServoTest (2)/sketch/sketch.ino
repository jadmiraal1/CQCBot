#include <Servo.h>

// ELEGOO sensor extension boards usually route the "Servo 1" header to D10.
// If your shield prints a different signal pin beside Servo 1, change this.
const int CAMERA_SERVO_PIN = 10;

const int MIN_ANGLE = 15;
const int CENTER_ANGLE = 90;
const int MAX_ANGLE = 165;
const int STEP_DELAY_MS = 15;
const int HOLD_DELAY_MS = 600;

Servo cameraServo;

void setup() {
  cameraServo.attach(CAMERA_SERVO_PIN);
  cameraServo.write(CENTER_ANGLE);
  delay(1000);
}

void loop() {
  sweepServo(CENTER_ANGLE, MIN_ANGLE);
  delay(HOLD_DELAY_MS);

  sweepServo(MIN_ANGLE, MAX_ANGLE);
  delay(HOLD_DELAY_MS);

  sweepServo(MAX_ANGLE, CENTER_ANGLE);
  delay(HOLD_DELAY_MS);
}

void sweepServo(int fromAngle, int toAngle) {
  int direction = fromAngle <= toAngle ? 1 : -1;

  for (int angle = fromAngle; angle != toAngle; angle += direction) {
    cameraServo.write(angle);
    delay(STEP_DELAY_MS);
  }

  cameraServo.write(toAngle);
}
