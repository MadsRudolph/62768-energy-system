#define F_CPU 16000000UL

#include <avr/io.h>
#include <util/delay.h>
#include <avr/interrupt.h>
#include <stdio.h>

#include "ina219.h"
#include "twi.h"

/*
=============================================================
                  HARDWARE CONNECTIONS
=============================================================

MCU: ATmega328P (Arduino Nano, 16 MHz)

-------------------- I2C (INA219) --------------------
INA219 VCC   -> 5V
INA219 GND   -> GND
INA219 SDA   -> PC4 (Arduino A4)
INA219 SCL   -> PC5 (Arduino A5)

NOTE:
- SDA and SCL MUST have pull-up resistors (~4.7kΩ) to 5V

-------------------- PWM OUTPUT ----------------------
PD6 (OC0A)   -> PWM output signal
               -> connected to gate driver / converter control

PWM SETTINGS:
- Timer0 Fast PWM
- Non-inverting mode
- Prescaler = 8
- Approx. PWM frequency ≈ 7.8 kHz

-------------------- POWER MEASUREMENT ----------------
INA219 measures:
- Bus voltage (V)
- Current (I)

Power is calculated in software:
    P = V * I

-------------------- SYSTEM FUNCTION ------------------
1. MCU reads V(k) and I(k) via INA219 (I2C)
2. Computes power: P(k)
3. Calculates:
       ΔP = P(k) - P(k-1)
       ΔV = V(k) - V(k-1)
4. Applies Perturb & Observe (MPPT algorithm)
5. Adjusts PWM duty cycle to track max power point

=============================================================
*/

// ===================== ADDED: UART / Serial output =====================
#define BAUD 9600UL
#define UBRR_VALUE ((F_CPU / (16UL * BAUD)) - 1)

static void UART_init(void)
{
    UBRR0H = (uint8_t)(UBRR_VALUE >> 8);
    UBRR0L = (uint8_t)(UBRR_VALUE);

    UCSR0B = (1 << TXEN0);                          // Enable transmitter
    UCSR0C = (1 << UCSZ01) | (1 << UCSZ00);         // 8 data bits, 1 stop bit, no parity
}

static void UART_tx(char c)
{
    while (!(UCSR0A & (1 << UDRE0))) {
        ; // wait
    }
    UDR0 = c;
}

static int UART_putchar(char c, FILE *stream)
{
    if (c == '\n') {
        UART_tx('\r');
    }
    UART_tx(c);
    return 0;
}

static FILE uart_stdout = FDEV_SETUP_STREAM(UART_putchar, NULL, _FDEV_SETUP_WRITE);
// ======================================================================

volatile float V_old = 0.0f;
volatile float V_new = 0.0f;

volatile float I_new = 0.0f;
volatile float I_old = 0.0f;

volatile float P_new = 0.0f;
volatile float P_old = 0.0f;

volatile int16_t duty = 128; // Initial PWM value (50% duty cycle)

// ///////////////////////// Initialize Timer /////////////////////////
void Timer_init(void) { // Page 84 in datasheet
    DDRD |= (1 << PD6); // Set PD6 as output for PWM signal
    TCCR0A |= (1 << COM0A1) | (1 << WGM01) | (1 << WGM00); // Fast PWM mode with 0xFF as top
    TCCR0B |= (1 << CS01) | (1 << CS00); // Prescaler of 64

    OCR0A = duty; // Set compare match value for PWM
}

// ///////////////////////// Initialize ADC /////////////////////////
void ADC_init(void) { // Page 217 in datasheet
    ADMUX = (1 << REFS0); // AVcc reference voltage, ADC0 as input

    ADCSRA |= (1 << ADEN) // Enable ADC
           | (1 << ADIE)  // Enable ADC interrupt
           | (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0); // prescaler of 128

    sei(); // enable global interrupts
}

// ///////////////////////// Start ADC Conversion /////////////////////////
void ADC_start(void) {
    ADCSRA |= (1 << ADSC); // Enable ADC
}

int main(void)
{
    // ===================== ADDED: UART init for printing =====================
    UART_init();
    stdout = &uart_stdout;
    // ========================================================================

    TWI_init();   // Initialize TWI for INA219 communication
    INA219_init(); // Initialize INA219 sensor
    ADC_init();   // Initialize ADC
    Timer_init();  // Initialize Timer for PWM

    while (1) {
        V_old = V_new;
        V_new = INA219_getVoltage();

        I_old = I_new;
        I_new = INA219_getCurrent();

        P_old = P_new;
        P_new = V_new * I_new;

        // ===================== ADDED: Serial print =====================
        char vStr[12];
        char iStr[12];
        char pStr[12];

        dtostrf(V_new, 6, 3, vStr);
        dtostrf(I_new, 6, 3, iStr);
        dtostrf(P_new, 6, 3, pStr);

        printf("Voltage: %s V | Current: %s A | Power: %s W\n", vStr, iStr, pStr);
        // ===============================================================

        float deltaP = P_new - P_old;
        float deltaV = V_new - V_old;

        if (deltaP > 0) {
            if (deltaV > 0) duty++;
            else duty--;
        } else {
            if (deltaV > 0) duty--;
            else duty++;
        }

        if (duty > 255) duty = 255;
        if (duty < 0) duty = 0;


        OCR0A = duty;
        _delay_ms(100);
    }
}