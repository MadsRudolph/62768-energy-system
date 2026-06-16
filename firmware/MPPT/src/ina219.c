#include "ina219.h"
#include "twi.h"

#define INA219_ADDR 0x40

#define REG_BUS_VOLTAGE 0x02
#define REG_CURRENT     0x04

// === write register ===
void INA219_write(uint8_t reg, uint16_t value) {
    TWI_start();
    TWI_write((INA219_ADDR << 1) | 0); // write
    TWI_write(reg);
    TWI_write(value >> 8);
    TWI_write(value & 0xFF);
    TWI_stop();
}

// === read register ===
uint16_t INA219_read(uint8_t reg) {
    uint16_t value;

    TWI_start();
    TWI_write((INA219_ADDR << 1) | 0);
    TWI_write(reg);

    TWI_start();
    TWI_write((INA219_ADDR << 1) | 1);

    value = (TWI_read_ack() << 8);
    value |= TWI_read_nack();

    TWI_stop();

    return value;
}

// === init ===
void INA219_init(void) {
    // default config (kan forbedres senere)
    INA219_write(0x00, 0x399F);
}

// === voltage ===
float INA219_getVoltage(void) {
    uint16_t raw = INA219_read(REG_BUS_VOLTAGE);
    raw >>= 3;
    return raw * 0.004; // 4mV per bit
}

// === current ===
float INA219_getCurrent(void) {
    int16_t raw = INA219_read(REG_CURRENT);
    return raw * 0.001; // afhænger af kalibrering!
}