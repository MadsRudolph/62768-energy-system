#include <avr/io.h>
#include "twi.h"

// Bounded wait so a stuck/unresponsive I2C bus can't hang the whole MCU.
// ~tens of ms at 16 MHz; a healthy transfer clears TWINT in microseconds.
// Without this, a missing/unwired INA219 freezes TWI_write() forever and
// nothing is ever printed over serial.
#define TWI_TIMEOUT 50000

void TWI_init(void) {
    TWSR = 0x00; // prescaler = 1
    TWBR = 72;   // ~100kHz at 16MHz
}

void TWI_start(void) {
    TWCR = (1<<TWINT)|(1<<TWSTA)|(1<<TWEN);
    uint16_t t = TWI_TIMEOUT;
    while (!(TWCR & (1<<TWINT)) && --t);
}

void TWI_stop(void) {
    TWCR = (1<<TWINT)|(1<<TWEN)|(1<<TWSTO);
}

void TWI_write(uint8_t data) {
    TWDR = data;
    TWCR = (1<<TWINT)|(1<<TWEN);
    uint16_t t = TWI_TIMEOUT;
    while (!(TWCR & (1<<TWINT)) && --t);
}

uint8_t TWI_read_ack(void) {
    TWCR = (1<<TWINT)|(1<<TWEN)|(1<<TWEA);
    uint16_t t = TWI_TIMEOUT;
    while (!(TWCR & (1<<TWINT)) && --t);
    return TWDR;
}

uint8_t TWI_read_nack(void) {
    TWCR = (1<<TWINT)|(1<<TWEN);
    uint16_t t = TWI_TIMEOUT;
    while (!(TWCR & (1<<TWINT)) && --t);
    return TWDR;
}
