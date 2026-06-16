// Bench test: measure a known resistor with the INA219.
// Apply a known voltage from the PSU, read V and I, check I == Vbus / R.
// Prints over USB serial at 9600 baud. Build/flash with:  pio run -e test -t upload
// Read it with:  pio device monitor -e test
//
// Wiring:
//   PSU(+) -> INA219 Vin+
//   INA219 Vin- -> [ R ] -> PSU(-)
//   INA219 VCC->5V, GND->GND, SDA->A4, SCL->A5   (PSU- and Nano GND joined)

#include <avr/io.h>
#include <util/delay.h>
#include <stdlib.h>

#include "ina219.h"
#include "twi.h"

      ///////////////////////// UART (9600 baud @ 16 MHz) /////////////////////////
static void UART_init(void) {
    UBRR0H = 0;
    UBRR0L = 103;                          // 16e6 / (16 * 9600) - 1 = 103
    UCSR0B = (1 << TXEN0);                 // transmit only
    UCSR0C = (1 << UCSZ01) | (1 << UCSZ00);// 8 data bits, no parity, 1 stop
}

static void UART_tx(char c) {
    while (!(UCSR0A & (1 << UDRE0)));       // wait for empty transmit buffer
    UDR0 = c;
}

static void UART_str(const char *s) {
    while (*s) UART_tx(*s++);
}

static void UART_int(int32_t v) {
    char buf[12];
    ltoa(v, buf, 10);
    UART_str(buf);
}

int main(void) {
    UART_init();
    UART_str("INA219 resistor test - booting\r\n"); // prints before any I2C

    TWI_init();
    INA219_init();

    UART_str("INA219 init done\r\n");

    while (1) {
        uint16_t mV = INA219_getBus_mV();    // voltage across the resistor
        int16_t  uV = INA219_getShunt_uV();  // voltage across the 0.1 ohm shunt
        int32_t  uA = (int32_t)uV * 10;      // I = Vshunt / 0.1 ohm -> uV*10 = uA

        UART_str("Vbus=");   UART_int(mV); UART_str(" mV  ");
        UART_str("Vshunt="); UART_int(uV); UART_str(" uV  ");
        UART_str("I=");      UART_int(uA); UART_str(" uA\r\n");

        _delay_ms(500);
    }
}
