// https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-7810-Automotive-Microcontrollers-ATmega328P_Datasheet.pdf
#include <avr/io.h>
#include <util/delay.h>
#include <avr/interrupt.h>


// CPU frequency (Arduino Nano = 16 MHz)
#define F_CPU 16000000UL
volatile uint16_t V = 0;
volatile float I = 0;
volatile float P = 0;

void ADC_init(void){ // Page 217 in PDF
 ADMUX = (1<<REFS0); // AVcc reference voltage, ADC0 as input

 ADCSRA |=(1 << ADEN) // Enable ADC 
        | (1 << ADIE) // Enable ADC interrupt
        | (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0); // prescaler of 128


    sei(); // enable global interrupts
    }


void ADC_start(void){
ADCSRA |=(1<<ADSC); // Enable ADC
 }

ISR(ADC_vect){
    V = ADC; // Read ADC value in interrupt service routine
}

int main(void) {
ADC_init(); // Initialize ADC

while (1) {
    ADC_start(); // Start ADC conversion and read value
    _delay_ms(100); // Delay for demonstration purposes

     I = V/0.1; // Convert ADC value to current (assuming 0.1 ohm)
     P = V*I; // Calculate power

     if(P > 0){
        if()
     }
    }
}