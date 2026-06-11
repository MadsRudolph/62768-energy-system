#ifndef I2C_H
#define I2C_H

#include <stdint.h>

/* ============ DEFINITIONER ============ */
#define I2C_OK      0
#define I2C_TIMEOUT 1   // Bus svarer ikke (manglende/forkert forbundet modul)

/* ============ FUNKTIONS PROTOTYPER ============ */
void i2c_init(void);
uint8_t i2c_start(uint8_t addr7);   // Send START + adresse (write)
uint8_t i2c_write(uint8_t data);
void i2c_stop(void);

#endif /* I2C_H */
