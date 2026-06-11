/*
 * ssd1306.c - Minimal SSD1306 128x64 OLED-driver (I2C, write-only)
 *
 * Ingen framebuffer: ATmega328P har kun 2 KB RAM, og en fuld buffer
 * ville aede halvdelen. I stedet saettes et adresse-vindue (pages x
 * kolonner) og font-bytes streames direkte til displayet.
 *
 * Tekst i to stoerrelser: 5x7 (1 page hoej) og 2x-skaleret
 * (10x14, 2 pages hoej) til de store maalevaerdier.
 *
 * Afhaengigheder: i2c.h, ssd1306_font.h, config.h
 */

/* ============ INCLUDES ============ */
#include <avr/pgmspace.h>
#include <stdint.h>

#include "config.h"
#include "i2c.h"
#include "ssd1306.h"
#include "ssd1306_font.h"

/* ============ DEFINITIONER ============ */
#define CTRL_CMD    0x00    // Kontrolbyte: kommandostroem foelger
#define CTRL_DATA   0x40    // Kontrolbyte: datastroem foelger

/* ============ GLOBALE VARIABLE ============ */
// Nibble -> bit-fordoblet byte (0bABCD -> 0bAABBCCDD), til 2x-skalering
static const uint8_t EXPAND_NIBBLE[16] PROGMEM = {
    0x00, 0x03, 0x0C, 0x0F, 0x30, 0x33, 0x3C, 0x3F,
    0xC0, 0xC3, 0xCC, 0xCF, 0xF0, 0xF3, 0xFC, 0xFF
};

/* ============ PRIVATE FUNKTIONER ============ */
static uint8_t ssd1306_cmdStart(void) {
    if (i2c_start(SSD1306_ADDR)) return I2C_TIMEOUT;
    return i2c_write(CTRL_CMD);
}

static uint8_t ssd1306_dataStart(void) {
    if (i2c_start(SSD1306_ADDR)) return I2C_TIMEOUT;
    return i2c_write(CTRL_DATA);
}

// Saet adresse-vindue: horizontal addressing fylder vinduet
// kolonne-for-kolonne, page-for-page - praecis som vi streamer
static void ssd1306_setWindow(uint8_t page0, uint8_t page1,
                              uint8_t col0, uint8_t col1) {
    if (ssd1306_cmdStart()) return;
    i2c_write(0x21); i2c_write(col0);  i2c_write(col1);   // Kolonneomraade
    i2c_write(0x22); i2c_write(page0); i2c_write(page1);  // Page-omraade
    i2c_stop();
}

static uint8_t ssd1306_fontColumn(char c, uint8_t col) {
    if (c < 32 || c > 127) c = '?';
    if (col >= 5) return 0x00;          // 6. kolonne = mellemrum mellem tegn
    return pgm_read_byte(&FONT5X7[c - 32][col]);
}

/* ============ PUBLIC API ============ */
uint8_t ssd1306_init(void) {
    // Standard init-sekvens for 128x64 (datasheet/appnote-vaerdier)
    if (ssd1306_cmdStart()) return I2C_TIMEOUT;
    i2c_write(0xAE);                    // Display fra under opsaetning
    i2c_write(0xD5); i2c_write(0x80);   // Oscillator/clock divide (anbefalet)
    i2c_write(0xA8); i2c_write(0x3F);   // Multiplex: 64 raekker
    i2c_write(0xD3); i2c_write(0x00);   // Display offset 0
    i2c_write(0x40);                    // Start line 0
    i2c_write(0x8D); i2c_write(0x14);   // Charge pump: intern (modul uden Vcc-forsyning)
    i2c_write(0x20); i2c_write(0x00);   // Horizontal addressing mode
    i2c_write(0xA1);                    // Segment remap: kolonne 127 = SEG0
    i2c_write(0xC8);                    // COM-scan baglaens (sammen med A1: normal laesning)
    i2c_write(0xDA); i2c_write(0x12);   // COM-pins: alternativ konfiguration
    i2c_write(0x81); i2c_write(0xCF);   // Kontrast
    i2c_write(0xD9); i2c_write(0xF1);   // Pre-charge
    i2c_write(0xDB); i2c_write(0x40);   // VCOMH-niveau
    i2c_write(0xA4);                    // Vis RAM-indhold (ikke all-on test)
    i2c_write(0xA6);                    // Normal (ikke inverteret)
    i2c_write(0xAF);                    // Display til
    i2c_stop();

    ssd1306_clear();
    return I2C_OK;
}

void ssd1306_clear(void) {
    ssd1306_setWindow(0, SSD1306_PAGES - 1, 0, SSD1306_WIDTH - 1);
    if (ssd1306_dataStart()) return;
    for (uint16_t i = 0; i < (uint16_t)SSD1306_WIDTH * SSD1306_PAGES; i++) {
        i2c_write(0x00);
    }
    i2c_stop();
}

void ssd1306_print(uint8_t page, uint8_t col, const char *s) {
    // Beregn vinduets bredde foerst (6 px pr. tegn)
    uint8_t len = 0;
    for (const char *p = s; *p; p++) len++;
    if (len == 0) return;
    uint8_t x1 = col + len * 6 - 1;
    if (x1 > SSD1306_WIDTH - 1) x1 = SSD1306_WIDTH - 1;

    ssd1306_setWindow(page, page, col, x1);
    if (ssd1306_dataStart()) return;
    for (const char *p = s; *p; p++) {
        for (uint8_t c = 0; c < 6; c++) {
            i2c_write(ssd1306_fontColumn(*p, c));
        }
    }
    i2c_stop();
}

void ssd1306_print2x(uint8_t page, uint8_t col, const char *s) {
    // 2x: hvert tegn fylder 12 kolonner og 2 pages. Horizontal
    // addressing kraever data page-for-page, saa der streames foerst
    // alle "toppe" (nedre nibble fordoblet), derefter alle "bunde".
    uint8_t len = 0;
    for (const char *p = s; *p; p++) len++;
    if (len == 0) return;
    uint8_t x1 = col + len * 12 - 1;
    if (x1 > SSD1306_WIDTH - 1) x1 = SSD1306_WIDTH - 1;

    ssd1306_setWindow(page, page + 1, col, x1);
    if (ssd1306_dataStart()) return;

    // Page 1 af vinduet: oeverste halvdel af alle tegn
    for (const char *p = s; *p; p++) {
        for (uint8_t c = 0; c < 6; c++) {
            uint8_t fb = ssd1306_fontColumn(*p, c);
            uint8_t top = pgm_read_byte(&EXPAND_NIBBLE[fb & 0x0F]);
            i2c_write(top); i2c_write(top);     // Hver kolonne fordoblet vandret
        }
    }
    // Page 2 af vinduet: nederste halvdel
    for (const char *p = s; *p; p++) {
        for (uint8_t c = 0; c < 6; c++) {
            uint8_t fb = ssd1306_fontColumn(*p, c);
            uint8_t bot = pgm_read_byte(&EXPAND_NIBBLE[fb >> 4]);
            i2c_write(bot); i2c_write(bot);
        }
    }
    i2c_stop();
}
