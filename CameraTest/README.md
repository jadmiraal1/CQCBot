# CameraTest

Arduino App Lab app for checking a Logitech USB camera connected to the UNO Q main USB-C side through an adapter.

## Run

Import this app into Arduino App Lab, run it on the UNO Q, then open:

```text
http://<uno-q-ip-address>:8766
```

The page serves a live MJPEG preview from camera index `0`, which is usually `/dev/video0`.

If the page says no camera opened, unplug and reconnect the camera adapter, then press `Reconnect`.
