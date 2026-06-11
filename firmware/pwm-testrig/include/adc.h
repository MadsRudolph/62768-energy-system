#ifndef ADC_H
#define ADC_H

#include <stdint.h>

/* ============ FUNKTIONS PROTOTYPER ============ */
void adc_init(void);
uint16_t adc_readAveraged(uint8_t channel);   // 8 samples, midlet (0-1023)

#endif /* ADC_H */
