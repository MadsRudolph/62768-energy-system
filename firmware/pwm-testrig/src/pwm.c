/*
 * pwm.c - Variabel frekvens + duty paa D9 via Timer1
 *
 * Timer1 i Fast PWM mode 14 (TOP = ICR1): frekvensen saettes med
 * ICR1, duty med OCR1A. 16-bit timer giver baade stort frekvens-
 * omraade og fin duty-oploesning.
 *
 *   f_PWM = F_CPU / (prescaler * (ICR1 + 1))
 *
 * Prescaler vaelges automatisk: 1 ned til ~245 Hz, derunder 8
 * (16-bit TOP kan ikke naa laengere ned med prescaler 1).
 *
 * Afhaengigheder: config.h
 */

/* ============ INCLUDES ============ */
#include <avr/interrupt.h>
#include <avr/io.h>
#include <stdint.h>

#include "config.h"
#include "pwm.h"

/* ============ PRIVATE FUNKTIONER ============ */
static void pwm_connectOutput(void) {
    // COM1A[1:0] = 10: Clear OC1A ved compare match, set ved BOTTOM
    TCCR1A |= (1 << COM1A1);
}

static void pwm_disconnectOutput(uint8_t level) {
    // Frakobl OC1A fra timeren og driv pinden manuelt -
    // bruges ved 0 % og 100 % duty, hvor Fast PWM ellers
    // laver en smal naal i stedet for konstant niveau
    TCCR1A &= ~((1 << COM1A1) | (1 << COM1A0));
    if (level) {
        PWM_PORT |= (1 << PWM_PIN);
    } else {
        PWM_PORT &= ~(1 << PWM_PIN);
    }
}

/* ============ PUBLIC API ============ */
void pwm_init(void) {
    PWM_DDR |= (1 << PWM_PIN);          // D9 som udgang
    PWM_PORT &= ~(1 << PWM_PIN);        // Start lav

    // TCCR1A: Timer/Counter1 Control Register A
    // - COM1A[1:0] = 00: OC1A frakoblet indtil foerste pwm_set()
    // - WGM1[1:0] = 10: Fast PWM, TOP = ICR1 (mode 14, sammen med TCCR1B)
    TCCR1A = (1 << WGM11);

    // TCCR1B: Timer/Counter1 Control Register B
    // - WGM1[3:2] = 11: Fast PWM mode 14
    // - CS1[2:0] = 001: Prescaler 1 (aendres dynamisk i pwm_set)
    TCCR1B = (1 << WGM13) | (1 << WGM12) | (1 << CS10);

    ICR1 = 16383;                       // Vilkaarlig startvaerdi (~977 Hz)
    OCR1A = 0;
}

uint32_t pwm_set(uint32_t freq_hz, uint16_t duty_raw) {
    // --- Vaelg prescaler og TOP ---
    // Med prescaler 1 er laveste frekvens 16 MHz/65536 = 244,1 Hz;
    // under det skiftes til prescaler 8 (naar ned til ~30,5 Hz)
    uint16_t prescaler;
    uint8_t cs_bits;
    if (freq_hz < 245) {
        prescaler = 8;
        cs_bits = (1 << CS11);
    } else {
        prescaler = 1;
        cs_bits = (1 << CS10);
    }

    uint32_t top = (F_CPU / prescaler) / freq_hz;
    if (top > 0) top -= 1;
    if (top > 65535UL) top = 65535UL;
    if (top < 1) top = 1;

    // --- Duty i timer-counts: skaler potmeterets 0-1023 direkte ---
    // (uint32 noedvendigt: top+1 op til 65536 gange 1023 overskrider 16 bit)
    uint32_t compare = ((top + 1) * (uint32_t)duty_raw) / 1024UL;

    // --- Skriv registrene atomisk ---
    // ICR1 er IKKE dobbeltbuffret i mode 14: rammer TCNT1 over den nye
    // TOP, taeller timeren til 65535 foer wrap (en enkelt lang puls).
    // Nulstil TCNT1 i samme hug - testriggen er ligeglad med det ene
    // mistede PWM-slag.
    uint8_t sreg = SREG;
    cli();
    ICR1 = (uint16_t)top;
    if (TCNT1 > (uint16_t)top) TCNT1 = 0;

    if (compare == 0) {
        pwm_disconnectOutput(0);        // 0 %: konstant lav
    } else if (compare >= top + 1) {
        pwm_disconnectOutput(1);        // 100 %: konstant hoej
    } else {
        OCR1A = (uint16_t)(compare - 1);    // Mode 14: match ved OCR1A+1 counts hoej
        pwm_connectOutput();
    }

    // Prescaler-bit uden at roere WGM-bits
    TCCR1B = (1 << WGM13) | (1 << WGM12) | cs_bits;
    SREG = sreg;

    // Faktisk (kvantiseret) frekvens til displayet
    return (F_CPU / prescaler) / (top + 1);
}
