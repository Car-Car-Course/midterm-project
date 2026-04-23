import logging
import sys
import time
from typing import Optional

sys.path.insert(0, "../BlueTooth/chat_hm10")
from hm10_esp32 import HM10ESP32Bridge

log = logging.getLogger(__name__)

# hint: You may design additional functions to execute the input command,
# which will be helpful when debugging :)


class BTInterface:
    def __init__(self, port: Optional[str] = None):
        log.info("Arduino Bluetooth Connect Program.")
        if port is None:
            port = input("PC bluetooth port name: ")
        log.info(f"Connecting to ESP32 bridge on {port}...")
        self.bridge = HM10ESP32Bridge(port=port)

        status = self.bridge.get_status()
        if status != "CONNECTED":
            log.warning(f"HM-10 status: {status}. Ensure the HM-10 is advertising.")

    def start(self):
        input("Press enter to start.")
        self.bridge.send("s")

    def get_UID(self):
        time.sleep(0.05)
        msg = self.bridge.listen()
        if msg:
            return msg.strip()
        return 0

    def send_action(self, dirc):
        # TODO : send the action to car
        return

    def end_process(self):
        self.bridge.send("e")
        self.bridge.ser.close()


if __name__ == "__main__":
    test = BTInterface()
    test.start()
    test.end_process()
