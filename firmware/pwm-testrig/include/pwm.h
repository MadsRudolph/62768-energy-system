#ifndef PWM_H
#define PWM_H

#include <stdint.h>

/* ============ FUNKTIONS PROTOTYPER ============ */
void pwm_init(void);

// Saet frekvens (Hz) og duty (raa potmeter-vaerdi 0-1023).
// Returnerer den FAKTISKE frekvens efter timer-kvantisering -
// det er den, displayet skal vise.
uint32_t pwm_set(uint32_t freq_hz, uint16_t duty_raw);

#endif /* PWM_H */
