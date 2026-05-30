# LaptopMovement

WASD browser controller for an Arduino UNO Q rover with an ELEGOO-style four-motor shield.

## Controls

- `W`: forward
- `S`: reverse
- `A`: spin left
- `D`: spin right
- `Space`: stop

## Motor Pins

This sketch assumes the common ELEGOO/TB6612 four-wheel motor shield mapping:

- Left motors: PWM `5`, direction `7`
- Right motors: PWM `6`, direction `8`
- Motor standby/enable: `3`

If the rover turns the wrong way, swap the affected motor pair wires or flip the pin behavior in `sketch/sketch.ino`.

The controller speed slider is capped at `200` to leave room for calibration before the PWM ceiling of `255`.
The physical right side currently has a `1.25` trim in `python/main.py`. The wiring maps the app's left command to the rover's physical right side, so that trim is applied to the left command before it reaches the sketch.

## Run

Import this app into Arduino App Lab, run it on the UNO Q, then open this from the laptop:

```text
http://<uno-q-ip-address>:8765
```

Example:

```text
http://192.168.1.205:8765
```
