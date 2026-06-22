// INA219 current/voltage read-out using the Adafruit library (Arduino C++).
// Port of Adafruit's examples/getcurrent/getcurrent.ino to PlatformIO.
//
// Build / flash:  pio run -t upload
// Read it with:   pio device monitor   (115200 baud)
//
// Wiring (ATmega328P / Arduino Nano, 16 MHz):
//   INA219 VCC -> 5V   GND -> GND   SDA -> A4 (PC4)   SCL -> A5 (PC5)
//   SDA/SCL need ~4.7k pull-ups to 5V (most breakout modules include them).

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_INA219.h>

Adafruit_INA219 ina219;

void setup(void) {
  Serial.begin(115200);
  while (!Serial) {
    delay(1); // wait for the serial console (no-op on the Nano)
  }

  Serial.println("Hello!");

  // Default range is 32V / 2A. begin() also writes the calibration register,
  // which is what makes the current/power registers actually read.
  if (!ina219.begin()) {
    Serial.println("Failed to find INA219 chip");
    while (1) {
      delay(10);
    }
  }
  // Higher-precision ranges, if needed:
  // ina219.setCalibration_32V_1A();
  // ina219.setCalibration_16V_400mA();

  Serial.println("Measuring voltage and current with INA219 ...");
}

void loop(void) {
  float shuntvoltage = ina219.getShuntVoltage_mV();
  float busvoltage   = ina219.getBusVoltage_V();
  float current_mA   = ina219.getCurrent_mA();
  float power_mW     = ina219.getPower_mW();
  float loadvoltage  = busvoltage + (shuntvoltage / 1000);

  Serial.print("Bus Voltage:   "); Serial.print(busvoltage);   Serial.println(" V");
  Serial.print("Shunt Voltage: "); Serial.print(shuntvoltage); Serial.println(" mV");
  Serial.print("Load Voltage:  "); Serial.print(loadvoltage);  Serial.println(" V");
  Serial.print("Current:       "); Serial.print(current_mA);   Serial.println(" mA");
  Serial.print("Power:         "); Serial.print(power_mW);     Serial.println(" mW");
  Serial.println("");

  delay(2000);
}
