#include <avr/io.h>
#include "twi.h"

// Bounded wait so a stuck/unresponsive I2C bus can't hang the whole MCU.
// ~tens of ms at 16 MHz; a healthy transfer clears TWINT in microseconds.
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

uint8_t TWI_probe(uint8_t addr7) {
    TWI_start();
    TWI_write((addr7 << 1) | 0);          // SLA+W
    uint8_t ack = ((TWSR & 0xF8) == 0x18); // 0x18 = SLA+W transmitted, ACK received
    TWI_stop();
    return ack;
}
