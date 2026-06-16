// https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-7810-Automotive-Microcontrollers-ATmega328P_Datasheet.pdf
#include <avr/io.h>
#include <util/delay.h>
#include <avr/interrupt.h>

#include "ina219.h"
#include "twi.h"
#include <stdlib.h>

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

// CPU frequency (Arduino Nano = 16 MHz)
#define F_CPU 16000000UL
volatile uint16_t V_old = 0;
volatile uint16_t V_new = 0;   // bus voltage, mV

volatile int32_t P_new = 0;
volatile int32_t P_old = 0;    // power, uW


volatile int16_t duty = 128; // Initial PWM value (50% duty cycle)



      ///////////////////////// UART (9600 baud @ 16 MHz) /////////////////////////
void UART_init(void){
    UBRR0H = 0;
    UBRR0L = 103;                          // 16e6 / (16 * 9600) - 1 = 103
    UCSR0B = (1 << TXEN0);                 // transmit only
    UCSR0C = (1 << UCSZ01) | (1 << UCSZ00);// 8 data bits, no parity, 1 stop
}

void UART_tx(char c){
    while(!(UCSR0A & (1 << UDRE0)));        // wait for empty transmit buffer
    UDR0 = c;
}

void UART_str(const char *s){
    while(*s) UART_tx(*s++);
}

void UART_int(int32_t v){
    char buf[12];
    ltoa(v, buf, 10);
    UART_str(buf);
}


      ///////////////////////// Initialize Timer /////////////////////////
void Timer_init(void){ // Page 84 in datasheet

    DDRD   |= (1 << PD6); // Set PD6 as output for PWM signal
    TCCR0A |= (1 << COM0A1) |(1 << WGM01) | (1 << WGM00); // Fast PWM mode with 0xFF as top
    TCCR0B |=(1 << CS01); // Prescaler of 

     OCR0A = duty; // Set compare match value for PWM
}


      ///////////////////////// Initialize ADC /////////////////////////

void ADC_init(void){ // Page 217 in datasheet
     ADMUX = (1<<REFS0); // AVcc reference voltage, ADC0 as input

     ADCSRA |=(1 << ADEN) // Enable ADC 
            | (1 << ADIE) // Enable ADC interrupt
            | (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0); // prescaler of 128

     sei(); // enable global interrupts
    }

      ///////////////////////// Start ADC Conversion /////////////////////////
void ADC_start(void){
    ADCSRA |=(1<<ADSC); // Enable ADC
 }


int main(void) {
    UART_init(); // Initialize UART for serial monitor
    UART_str("boot\r\n"); // prints before any I2C - proves the UART works
    TWI_init(); // Initialize TWI for INA219 communication

    // One-shot I2C scan: list every address that ACKs (INA219 should be 64 = 0x40)
    UART_str("I2C scan:");
    uint8_t found = 0;
    for (uint8_t a = 1; a < 127; a++) {
        if (TWI_probe(a)) { UART_str(" "); UART_int(a); found++; }
    }
    if (!found) UART_str(" none");
    UART_str("\r\n");

    INA219_init(); // Initialize INA219 sensor
    ADC_init(); // Initialize ADC
    Timer_init(); // Initialize Timer for PWM

    UART_str("MPPT running\r\n");


while (1) {

    // --- measure (shunt-based current, no calibration register needed) ---
    V_old = V_new;
    V_new = INA219_getBus_mV();              // bus voltage, mV
    int16_t shunt = INA219_getShunt_uV();    // shunt voltage, uV
    int32_t i_ua  = (int32_t)shunt * 10;     // I = Vshunt / 0.1 ohm -> uA

    P_old = P_new;
    P_new = ((int32_t)V_new * i_ua) / 1000;  // P = V * I -> uW

    int32_t deltaP = P_new - P_old;
    int32_t deltaV = (int32_t)V_new - (int32_t)V_old;

    // --- Perturb & Observe ---
    if (deltaP > 0) {
        if (deltaV > 0) duty++;
        else            duty--;
    } else {
        if (deltaV > 0) duty--;
        else            duty++;
    }

    if (duty > 255) duty = 255;
    if (duty < 0)   duty = 0;

    OCR0A = duty;

    // --- live state to the serial monitor ---
    UART_str("duty=");  UART_int(duty);
    UART_str(" Vbus="); UART_int(V_new); UART_str("mV");
    UART_str(" I=");    UART_int(i_ua);  UART_str("uA");
    UART_str(" P=");    UART_int(P_new); UART_str("uW\r\n");

    _delay_ms(200);

    }
}