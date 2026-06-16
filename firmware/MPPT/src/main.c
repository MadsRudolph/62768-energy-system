// https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-7810-Automotive-Microcontrollers-ATmega328P_Datasheet.pdf
#include <avr/io.h>
#include <util/delay.h>
#include <avr/interrupt.h>

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

// CPU frequency (Arduino Nano = 16 MHz)
#define F_CPU 16000000UL
volatile uint16_t V_old = 0;
volatile uint16_t V_new = 0;

volatile float I_new = 0;
volatile float I_old = 0;

volatile float P_new = 0;
volatile float P_old = 0;


volatile int16_t duty = 128; // Initial PWM value (50% duty cycle)



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
    TWI_init(); // Initialize TWI for INA219 communication
    INA219_init(); // Initialize INA219 sensor
    ADC_init(); // Initialize ADC
    Timer_init(); // Initialize Timer for PWM


while (1) {

    V_old = V_new;
    V_new = INA219_getVoltage();

    I_new = INA219_getCurrent();

    P_old = P_new;
    P_new = V_new * I_new;

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