#ifndef TWI_H
#define TWI_H

#include <stdint.h>

void TWI_init(void);
void TWI_start(void);
void TWI_stop(void);
void TWI_write(uint8_t data);
uint8_t TWI_read_ack(void);
uint8_t TWI_read_nack(void);
uint8_t TWI_probe(uint8_t addr7); // 1 if a device ACKs at this 7-bit address

#endif
