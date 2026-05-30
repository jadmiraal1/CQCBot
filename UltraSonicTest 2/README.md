# UltraSonicTest

Arduino App Lab app for checking the ultrasonic sensor on the ELEGOO extension board.

## Wiring

- Plug the ultrasonic sensor signal into `P9`.
- This sketch assumes a single signal pin for trigger and echo.

## Run

Import this app into Arduino App Lab, run it on the UNO Q, then open:

```text
http://<uno-q-ip-address>:8767
```

The page updates about five times per second with centimeters and inches.
