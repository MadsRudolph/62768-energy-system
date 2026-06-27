/*
 * adc.c - Polled ADC-laesning af potmetrene
 *
 * Testriggen har ingen realtidskrav paa maalingerne (display og PWM
 * opdateres ~10 Hz), saa ADC'en laeses blokerende i main-loop i stedet
 * for via interrupt.
 *
 * VIGTIGT om kanalskift: ATmega'en deler EN sample/hold-kondensator
 * mellem alle kanaler. Lige efter et mux-skift holder den stadig den
 * forrige kanals spaending. Er den nye kanals kilde hoejohmig (loes
 * ledning, oxideret breadboard-kontakt), naar S/H ikke at oplade i
 * det korte sample-vindue, og kanalen "smitter" - kanal B laeser kanal
 * A's vaerdi. Et multimeter (10 MOhm) ser IKKE den fejl; ADC'ens 14 pF
 * S/H goer. Derfor: skift kanal, vent, og koer flere dummy-konverter-
 * inger (hver re-sampler og oplader S/H et trin mere) FOER midling.
 *
 * Afhaengigheder: config.h, util/delay.h
 */

/* ============ INCLUDES ============ */
#include <avr/io.h>
#include <stdint.h>
#include <util/delay.h>

#include "adc.h"
#include "config.h"

/* ============ DEFINITIONER ============ */
#define ADC_DUMMY_CONV  4   // antal kasserede konverteringer efter kanalskift

/* ============ PRIVATE FUNKTIONER ============ */
static void adc_selectChannel(uint8_t channel) {
    // Behold referencevalg (hoeje nibble), saet kun MUX3:0
    ADMUX = (ADMUX & 0xF0) | (channel & 0x0F);
}

static uint16_t adc_convert(void) {
    ADCSRA |= (1 << ADSC);              // Start konvertering
    while (ADCSRA & (1 << ADSC));       // Vent (~104 us @ 125 kHz)
    return ADC;
}

/* ============ PUBLIC API ============ */
void adc_init(void) {
    // ADMUX: ADC Multiplexer Selection Register
    // - REFS[1:0] = 01: AVcc (5 V) som reference - matcher potmetrenes forsyning
    // - ADLAR = 0: Hoejrejusteret resultat (0-1023)
    ADMUX = (1 << REFS0);

    // ADCSRA: ADC Control and Status Register A
    // - ADEN = 1: Aktiver ADC
    // - ADPS[2:0] = 111: Prescaler 128 -> 125 kHz ADC-clock @ 16 MHz
    //   (laveste standardclock = laengst sample-tid = bedst for hoejohmige kilder)
    ADCSRA = (1 << ADEN) | (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0);

    // Foerste konvertering efter ADEN er ekstra langsom - varm op
    adc_selectChannel(POT_DUTY_CHANNEL);
    (void)adc_convert();
}

uint16_t adc_readAveraged(uint8_t channel) {
    adc_selectChannel(channel);
    _delay_us(20);                          // mux-skift + initial S/H-opladning

    // Dummy-konverteringer: lad S/H naa den nye kanal helt, ogsaa fra
    // en lidt hoejohmig kilde, foer vi stoler paa vaerdien
    for (uint8_t i = 0; i < ADC_DUMMY_CONV; i++) {
        (void)adc_convert();
    }

    // 8 samples og >>3: billig midling, daemper skyder-stoej
    uint16_t sum = 0;
    for (uint8_t i = 0; i < 8; i++) {
        sum += adc_convert();
    }
    return sum >> 3;
}
