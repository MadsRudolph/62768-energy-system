/*
 * i2c.c - Minimal TWI master (write-only) til SSD1306
 *
 * 400 kHz fast mode. Alle ventninger har timeout, saa firmwaren
 * ikke haenger fast hvis displayet mangler eller SDA/SCL er byttet -
 * riggen koerer videre med PWM selv uden display.
 *
 * Afhaengigheder: ingen (kun avr-libc)
 */

/* ============ INCLUDES ============ */
#include <avr/io.h>
#include <stdint.h>

#include "i2c.h"

/* ============ DEFINITIONER ============ */
#define I2C_SPIN_MAX 4000   // ~1 ms @ 16 MHz: rigeligt for en TWI-transaktion

/* ============ PRIVATE FUNKTIONER ============ */
static uint8_t i2c_waitFlag(void) {
    // Vent paa TWINT med timeout i stedet for evig busy-wait
    uint16_t spins = 0;
    while (!(TWCR & (1 << TWINT))) {
        if (++spins > I2C_SPIN_MAX) return I2C_TIMEOUT;
    }
    return I2C_OK;
}

/* ============ PUBLIC API ============ */
void i2c_init(void) {
    // SCL-frekvens = F_CPU / (16 + 2*TWBR*prescaler)
    // 400 kHz = 16 MHz / (16 + 2*12*1)
    TWSR = 0;       // Prescaler 1
    TWBR = 12;
}

uint8_t i2c_start(uint8_t addr7) {
    // START-betingelse
    TWCR = (1 << TWINT) | (1 << TWSTA) | (1 << TWEN);
    if (i2c_waitFlag()) return I2C_TIMEOUT;

    // Adresse + W (LSB = 0)
    TWDR = (uint8_t)(addr7 << 1);
    TWCR = (1 << TWINT) | (1 << TWEN);
    if (i2c_waitFlag()) return I2C_TIMEOUT;

    return I2C_OK;
}

uint8_t i2c_write(uint8_t data) {
    TWDR = data;
    TWCR = (1 << TWINT) | (1 << TWEN);
    return i2c_waitFlag();
}

void i2c_stop(void) {
    TWCR = (1 << TWINT) | (1 << TWSTO) | (1 << TWEN);
    // STOP saetter ikke TWINT - ingen ventning noedvendig
}
