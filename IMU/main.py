# SPDX-License-Identifier: MPL-2.0
from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI
import math, time

logger = Logger("imu-sensor")
web_ui = WebUI()

# At rest, total acceleration magnitude ~= 1.0 g (gravity).
# Disturbance = how far the magnitude deviates from 1g.
# A calm baseline; tune THRESHOLD to your surface/demo.
THRESHOLD = 0.15          # g of deviation that counts as "disturbed"

latest = {"magnitude": None, "disturbance": 0.0, "alert": False, "t": None}

def _get_imu():
    return latest

web_ui.expose_api("GET", "/imu", _get_imu)
web_ui.on_connect(lambda sid: web_ui.send_message('imu', latest))

def record_sensor_movement(x: float, y: float, z: float):
    try:
        # total acceleration magnitude
        mag = math.sqrt(x*x + y*y + z*z)
        # deviation from 1g resting = vibration/movement energy
        disturbance = abs(mag - 1.0)
        alert = disturbance > THRESHOLD

        latest.update({
            "magnitude": round(mag, 3),
            "disturbance": round(disturbance, 3),
            "alert": bool(alert),
            "t": time.time(),
        })

        if alert:
            logger.info(f"DISTURBANCE: {disturbance:.3f} g  (mag={mag:.3f})")
        else:
            logger.debug(f"calm: dev={disturbance:.3f} g")

        web_ui.send_message('imu', latest)
    except Exception as e:
        logger.exception(f"record_sensor_movement error: {e}")

try:
    Bridge.provide("record_sensor_movement", record_sensor_movement)
except RuntimeError:
    logger.debug("'record_sensor_movement' already registered")

logger.info("Starting App...")
App.run()
