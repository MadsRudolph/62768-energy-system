#ifndef CONFIG_H
#define CONFIG_H

/*
 * config.h - Pins og parametre for PWM-testriggen
 *
 * Arduino Nano (ATmega328P @ 16 MHz). PWM ud paa D9 (OC1A/Timer1),
 * to potmetre paa A0/A1, SSD1306 OLED paa I2C (A4/A5).
 */

/* ============ DEFINITIONER ============ */

// PWM-udgang: D9 = PB1 = OC1A (Timer1, 16-bit -> fin oploesning)
#define PWM_PIN             PB1     // Arduino D9
#define PWM_DDR             DDRB
#define PWM_PORT            PORTB

// Potmetre (ADC-kanaler)
#define POT_DUTY_CHANNEL    0       // Arduino A0: duty cycle 0-100 %
#define POT_FREQ_CHANNEL    1       // Arduino A1: frekvens

// Frekvensomraade - pseudo-logaritmisk i tre dekade-segmenter,
// saa der baade er fin oploesning ved 100 Hz og raekkevidde til 50 kHz
#define FREQ_MIN_HZ         100UL
#define FREQ_SEG1_HZ        1000UL      // pot 1/3:  100 Hz -> 1 kHz
#define FREQ_SEG2_HZ        10000UL     // pot 2/3:  1 kHz -> 10 kHz
#define FREQ_MAX_HZ         50000UL     // pot 3/3:  10 kHz -> 50 kHz

// Potmeter-hysterese: ignorer aendringer mindre end dette (ADC-counts),
// ellers flimrer display/PWM af stoej paa skyderen
#define POT_DEADBAND        3

// SSD1306: de fleste moduler svarer paa 0x3C - proev 0x3D hvis displayet er dødt
#define SSD1306_ADDR        0x3C

// Display-opdatering (ms mellem hver gennemloeb af main-loop)
#define LOOP_PERIOD_MS      100

// Fejlfinding: saet til 1 for at vise RAA ADC-counts (A0/A1) i stedet for
// den normale visning. Drej hvert potmeter og se hvilken linje reagerer.
// Saet tilbage til 0 naar potmeter-ledningerne er verificeret.
#define DIAG_RAW_ADC        1

#endif /* CONFIG_H */
