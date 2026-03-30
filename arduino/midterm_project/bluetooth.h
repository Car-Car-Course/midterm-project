/***************************************************************************/
// File			  [bluetooth.h]
// Author		  [Erik Kuo]
// Synopsis		[Code for bluetooth communication]
// Functions  [ask_BT, send_msg, send_byte]
// Modify		  [2020/03/27 Erik Kuo]
/***************************************************************************/

/*if you have no idea how to start*/
/*check out what you have learned from week 2*/

enum BT_CMD {
    NOTHING,
    // TODO: add your own command type here
};

BT_CMD ask_BT() {
    BT_CMD message = NOTHING;
    char cmd;
    if (Serial3.available()) {
// TODO:
// 1. get cmd from Serial3(bluetooth serial)
// 2. link bluetooth message to your own command type
#ifdef DEBUG
        Serial.print("cmd : ");
        Serial.println(cmd);
#endif
    }
    return message;
}  // ask_BT

// send msg back through Serial1(bluetooth serial)
// can use send_byte alternatively to send msg back
// (but need to convert to byte type)
void send_msg(const char& msg) {
    // TODO:
}  // send_msg

// send UID back through Serial3(bluetooth serial)
void send_byte(byte* id, byte& idSize) {
    for (byte i = 0; i < idSize; i++) {  // Send UID consequently.
        Serial3.print(id[i]);
    }
#ifdef DEBUG
    Serial.print("Sent id: ");
    for (byte i = 0; i < idSize; i++) {  // Show UID consequently.
        Serial.print(id[i], HEX);
    }
    Serial.println();
#endif
}  // send_byte


/**
 * Helper to send AT commands (Uppercase, no \r or \n) [6]
 */
void sendATCommand(const char* command) {
  Serial3.print(command);
  waitForResponse("", 1000); 
}

/**
 * Helper to check response for specific substrings
 */
bool waitForResponse(const char* expected, unsigned long timeout) {
  unsigned long start = millis();
  Serial3.setTimeout(timeout);
  String response = Serial3.readString();
  if (response.length() > 0) {
    Serial.print("HM10 Response: ");
    Serial.println(response);
  }
  return (response.indexOf(expected) != -1);
}

void initBT() {
    // 1. Automatic Baud Rate Detection
    for (int i = 0; i < 9; i++) {
        Serial.print("Testing baud rate: ");
        Serial.println(baudRates[i]);
        
        Serial3.begin(baudRates[i]);
        Serial3.setTimeout(100);
        delay(100);

        // 2. Force Disconnection
        // Sending "AT" while connected forces the module to disconnect [2].
        Serial3.print("AT"); 
        
        if (waitForResponse("OK", 800)) {
        Serial.println("HM-10 detected and ready.");
        moduleReady = true;
        break; 
        } else {
        Serial3.end();
        delay(100);
        }
    }

    if (!moduleReady) {
        Serial.println("Failed to detect HM-10. Check 3.3V VCC and wiring.");
        return;
    }

    // 3. Restore Factory Defaults
    Serial.println("Restoring factory defaults...");
    sendATCommand("AT+RENEW"); // Restores all setup values
    delay(500);

    // 4. Set Custom Name via Macro
    Serial.print("Setting name to: ");
    Serial.println(CUSTOM_NAME);
    String nameCmd = "AT+NAME" + String(CUSTOM_NAME);
    sendATCommand(nameCmd.c_str()); // Max length is 12
    
    // 5. Enable Connection Notifications
    Serial.println("Enabling notifications...");
    sendATCommand("AT+NOTI1"); // Notify when link is established/lost

    // 6. Get the Bluetooth MAC Address
    Serial.println("Querying Bluetooth Address");
    sendATCommand("AT+ADDR?");

    // 7. Restart the module to apply changes
    Serial.println("Restarting module...");
    sendATCommand("AT+RESET"); // Restart the module
    delay(1000);
    Serial3.begin(9600); // Now the module would use baudrate 9600
    return
}