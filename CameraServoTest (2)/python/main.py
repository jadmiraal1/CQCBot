import time

from arduino.app_utils import App

print("CameraServoTest running. Servo movement is handled by the Arduino sketch.")


def loop():
    """This function is called repeatedly by the App framework."""
    time.sleep(10)


# See: https://docs.arduino.cc/software/app-lab/tutorials/getting-started/#app-run
App.run(user_loop=loop)
