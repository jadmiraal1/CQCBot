# CameraServoTest

Simple Arduino App Lab sketch for checking the camera servo.

## Wiring

- Plug the servo into `Servo 1` on the ELEGOO sensor extension board.
- This sketch assumes `Servo 1` is routed to Arduino digital pin `10`.
- Servo lead order is usually brown/black to `GND`, red to `5V`, and orange/yellow/white to signal.

When running, the servo centers, sweeps left, sweeps right, and returns to center repeatedly.
