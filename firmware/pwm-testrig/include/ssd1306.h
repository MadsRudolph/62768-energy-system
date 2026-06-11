#ifndef SSD1306_H
#define SSD1306_H

#include <stdint.h>

/* ============ DEFINITIONER ============ */
#define SSD1306_WIDTH   128
#define SSD1306_PAGES   8       // 64 pixels / 8 pr. page

/* ============ FUNKTIONS PROTOTYPER ============ */
uint8_t ssd1306_init(void);    // Returnerer I2C_OK / I2C_TIMEOUT
void ssd1306_clear(void);
void ssd1306_print(uint8_t page, uint8_t col, const char *s);    // 5x7 (6 px/tegn)
void ssd1306_print2x(uint8_t page, uint8_t col, const char *s);  // 2x skala (12 px, 2 pages)

#endif /* SSD1306_H */
