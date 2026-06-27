/*
 * main.c - PWM-testrig paa Arduino Nano
 *
 * To potmetre styrer PWM-udgangen paa D9:
 *   A0: duty cycle 0-100 %
 *   A1: frekvens 100 Hz - 50 kHz (pseudo-logaritmisk)
 *
 * Den faktiske (timer-kvantiserede) frekvens og duty vises paa en
 * SSD1306 OLED. Riggen er taenkt som stimulus/maaleobjekt sammen
 * med AD3'en naar konverter-gatedrev mv. skal testes.
 *
 * Afhaengigheder: adc.h, pwm.h, i2c.h, ssd1306.h, config.h
 */

/* ============ INCLUDES ============ */
#include <avr/io.h>
#include <stdint.h>
#include <stdio.h>
#include <util/delay.h>

#include "adc.h"
#include "config.h"
#include "i2c.h"
#include "pwm.h"
#include "ssd1306.h"

/* ============ PRIVATE FUNKTIONER ============ */

// Potmeter (0-1023) -> frekvens i Hz. Tre lineaere segmenter pr.
// dekade giver baade fin oploesning i bunden og raekkevidde i toppen:
//   [0..341]    -> 100 Hz  .. 1 kHz
//   [342..682]  -> 1 kHz   .. 10 kHz
//   [683..1023] -> 10 kHz  .. 50 kHz
static uint32_t map_potTilFrekvens(uint16_t pot) {
    if (pot <= 341) {
        return FREQ_MIN_HZ + ((FREQ_SEG1_HZ - FREQ_MIN_HZ) * (uint32_t)pot) / 341UL;
    }
    if (pot <= 682) {
        return FREQ_SEG1_HZ + ((FREQ_SEG2_HZ - FREQ_SEG1_HZ) * (uint32_t)(pot - 342)) / 340UL;
    }
    return FREQ_SEG2_HZ + ((FREQ_MAX_HZ - FREQ_SEG2_HZ) * (uint32_t)(pot - 683)) / 340UL;
}

// Opdater kun ved reel drejning - undgaa display/PWM-flimmer fra ADC-stoej
static uint8_t pot_harAendretSig(uint16_t ny, uint16_t gammel) {
    int16_t diff = (int16_t)ny - (int16_t)gammel;
    if (diff < 0) diff = -diff;
    return diff > POT_DEADBAND;
}

static void display_visStatisk(void) {
    ssd1306_print(0, 16, "PWM TESTRIG (D9)");
    ssd1306_print2x(2, 0, "f");
    ssd1306_print2x(5, 0, "D");
}

static void display_visVaerdier(uint32_t freq_hz, uint8_t duty_pct) {
    char buf[12];

    // Frekvens: hoejrestillet, heltal Hz (op til 5 cifre)
    snprintf(buf, sizeof(buf), "%5lu", (unsigned long)freq_hz);
    ssd1306_print2x(2, 18, buf);
    ssd1306_print(3, 102, "Hz");

    // Duty i procent
    snprintf(buf, sizeof(buf), "%3u", duty_pct);
    ssd1306_print2x(5, 18, buf);
    ssd1306_print(6, 66, "%");
}

/* ============ MAIN ============ */
int main(void) {
    adc_init();
    pwm_init();
    i2c_init();

    // Display er valgfrit: timeout i I2C-laget goer at riggen koerer
    // videre med PWM alene hvis modulet mangler/er forkert forbundet
    uint8_t display_ok = (ssd1306_init() == I2C_OK);

#if DIAG_RAW_ADC
    // Fejlfindings-tilstand: vis raa ADC-counts (0-1023) for begge kanaler.
    // Drej duty-potmeteret -> kun A0 skal aendre sig; drej frekvens -> kun A1.
    // Reagerer A0 ikke (eller foelger A1), er duty-wiren ikke forbundet til A0.
    ssd1306_clear();
    ssd1306_print(0, 0, "DIAG raa ADC counts");
    while (1) {
        char b[12];
        snprintf(b, sizeof(b), "A0:%4u", adc_readAveraged(POT_DUTY_CHANNEL));
        ssd1306_print2x(2, 6, b);
        snprintf(b, sizeof(b), "A1:%4u", adc_readAveraged(POT_FREQ_CHANNEL));
        ssd1306_print2x(5, 6, b);
        _delay_ms(120);
    }
#endif

    if (display_ok) display_visStatisk();

    uint16_t pot_duty = adc_readAveraged(POT_DUTY_CHANNEL);
    uint16_t pot_freq = adc_readAveraged(POT_FREQ_CHANNEL);
    uint32_t freq_faktisk = pwm_set(map_potTilFrekvens(pot_freq), pot_duty);
    uint8_t foerste_visning = 1;

    while (1) {
        uint16_t ny_duty = adc_readAveraged(POT_DUTY_CHANNEL);
        uint16_t ny_freq = adc_readAveraged(POT_FREQ_CHANNEL);

        uint8_t aendret = 0;
        if (pot_harAendretSig(ny_duty, pot_duty)) { pot_duty = ny_duty; aendret = 1; }
        if (pot_harAendretSig(ny_freq, pot_freq)) { pot_freq = ny_freq; aendret = 1; }

        if (aendret || foerste_visning) {
            freq_faktisk = pwm_set(map_potTilFrekvens(pot_freq), pot_duty);

            if (display_ok) {
                // Afrundet procent af 1023 til visning
                uint8_t pct = (uint8_t)(((uint32_t)pot_duty * 100UL + 511UL) / 1023UL);
                display_visVaerdier(freq_faktisk, pct);
            }
            foerste_visning = 0;
        }

        _delay_ms(LOOP_PERIOD_MS);
    }
}
