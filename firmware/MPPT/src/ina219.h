#ifndef INA219_H
#define INA219_H

#include <stdint.h>

void INA219_init(void);
float INA219_getVoltage(void);
float INA219_getCurrent(void);

// Integer helpers for the bench test (no calibration register needed):
uint16_t INA219_getBus_mV(void);   // bus voltage, millivolts
int16_t  INA219_getShunt_uV(void); // shunt voltage, microvolts (I = Vshunt / Rshunt)

#endif