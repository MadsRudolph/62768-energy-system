#ifndef INA219_H
#define INA219_H

#include <stdint.h>

void INA219_init(void);
float INA219_getVoltage(void);
float INA219_getCurrent(void);

#endif