/*
 * sensors.h - Aflæsning af spændinger og strøm via ADC
 *
 * Omregner rå ADC-værdier til fysiske enheder ud fra
 * spændingsdeler-forhold og strømsensor-kalibrering i config.h.
 *
 * Afhængigheder: config.h
 */
#ifndef SENSORS_H
#define SENSORS_H

#include <stdint.h>

/* ============ FUNKTIONS PROTOTYPER ============ */
void  sensors_init(void);

// Spænding på en delt knude [V]: dividerRatio = R2/(R1+R2)
float sensors_readVoltage(uint8_t adcChannel, float dividerRatio);

// Strøm [A] fra en sensor med offset + V/A skala (config.h)
float sensors_readCurrent(uint8_t adcChannel);

#endif /* SENSORS_H */
