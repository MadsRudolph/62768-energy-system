/*
 * main.c - 62768 Electrical Energy Systems, bare-metal AVR firmware
 *
 * Styrer DC-motoren (som driver AC-generatoren) med en PID-regulator,
 * så ensretter-bussen V1 holdes på setpointet (15 V, Krav 1). Timer1
 * giver et fast styre-loop (Krav 15), Timer2 laver motor-PWM, og
 * spændinger/strøm sendes som CSV over UART én gang i sekundet (Krav 13/14).
 *
 * Reguleringsretning: højere motor-PWM -> hurtigere generator -> højere V1.
 * (Inverter fortegnet hvis hardwaren er koblet modsat.)
 *
 * UART-kommandoer:  'r' = run (start regulering),  's' = stop (motor fra)
 *
 * Afhængigheder: config.h, pid.h, sensors.h
 */

/* ============ INCLUDES ============ */
#include <avr/interrupt.h>
#include <avr/io.h>
#include <stdlib.h>

#include "config.h"
#include "pid.h"
#include "sensors.h"

/* ============ DEFINITIONER ============ */
// Motor-PWM på Timer2 OC2B + status-LED (D13). Pin afhænger af chip.
#if defined(__AVR_ATmega2560__)
  #define MOTOR_DDR   DDRH
  #define MOTOR_BIT   PH6        // OC2B -> Mega D9
  #define LED_BIT     PB7        // D13 på Mega
#else /* ATmega328P (Uno / Nano) */
  #define MOTOR_DDR   DDRD
  #define MOTOR_BIT   PD3        // OC2B -> Uno D3
  #define LED_BIT     PB5        // D13 på Uno
#endif

// Timer1 CTC TOP: f = F_CPU / (64 * (1 + OCR1A))
#define TIMER1_OCR_VALUE   ((F_CPU / (64UL * CONTROL_HZ)) - 1UL)
// UART (dobbelt-hastighed, U2X): UBRR = F_CPU/(8*baud) - 1
#define UART_UBRR_VALUE    ((F_CPU / (8UL * SERIAL_BAUD)) - 1UL)

/* ============ GLOBALE VARIABLE ============ */
static volatile uint8_t control_tick = 0;   // sættes af Timer1-ISR
static pid_t  motorPid;
static const float CONTROL_DT = 1.0f / (float)CONTROL_HZ;

/* ============ PRIVATE FUNKTIONER: UART ============ */
static void uart_init(void) {
    UBRR0H = (uint8_t)(UART_UBRR_VALUE >> 8);
    UBRR0L = (uint8_t)(UART_UBRR_VALUE);
    UCSR0A = (1 << U2X0);                          // dobbelt hastighed
    UCSR0B = (1 << TXEN0) | (1 << RXEN0);          // aktiver TX + RX
    UCSR0C = (1 << UCSZ01) | (1 << UCSZ00);        // 8 databits, 1 stopbit, ingen paritet
}

static void uart_putc(char c) {
    while (!(UCSR0A & (1 << UDRE0))) {             // vent til send-buffer er tom
        ;
    }
    UDR0 = (uint8_t)c;
}

static void uart_puts(const char *s) {
    while (*s) {
        uart_putc(*s++);
    }
}

static void uart_printFloat(float value, uint8_t prec) {
    char buf[16];
    dtostrf(value, 0, prec, buf);                 // avr-libc float -> streng
    uart_puts(buf);
}

static void uart_printU32(uint32_t value) {
    char buf[12];
    ultoa(value, buf, 10);
    uart_puts(buf);
}

/* ============ PRIVATE FUNKTIONER: PWM (Timer2) ============ */
static void pwm_init(void) {
    MOTOR_DDR |= (1 << MOTOR_BIT);                 // PWM-pin som output

    // TCCR2A: Fast PWM (WGM21|WGM20), non-inverting på OC2B (COM2B1)
    TCCR2A = (1 << COM2B1) | (1 << WGM21) | (1 << WGM20);
    // TCCR2B: prescaler 8 -> f_PWM = 16 MHz / (8*256) ~ 7.8 kHz
    TCCR2B = (1 << CS21);
    OCR2B = 0;                                     // start slukket
}

static void pwm_set(uint8_t duty) {
    OCR2B = duty;
}

/* ============ PRIVATE FUNKTIONER: STYRE-TIMER (Timer1) ============ */
static void control_initTimer(void) {
    TCCR1A = 0;                                    // ingen PWM-output fra Timer1
    // TCCR1B: WGM12 = CTC-mode (TOP = OCR1A), CS11|CS10 = prescaler 64
    TCCR1B = (1 << WGM12) | (1 << CS11) | (1 << CS10);
    OCR1A  = (uint16_t)TIMER1_OCR_VALUE;
    TIMSK1 = (1 << OCIE1A);                        // aktiver compare-A interrupt
    TCNT1  = 0;
}

/* ============ PRIVATE FUNKTIONER: KOMMANDO + MONITOR ============ */
static uint8_t handleSerialCommand(uint8_t running) {
    if (!(UCSR0A & (1 << RXC0))) {                 // intet modtaget?
        return running;
    }
    char c = (char)UDR0;
    if (c == 'r' || c == 'R') {
        pid_reset(&motorPid);                      // undgå windup-spring ved genstart
        uart_puts("# RUN\r\n");
        return 1;
    }
    if (c == 's' || c == 'S') {
        pwm_set(0);
        uart_puts("# STOP\r\n");
        return 0;
    }
    return running;
}

static void monitor_print(uint32_t t_ms, float v1, float v2, float v3,
                          float iload, uint8_t duty, uint8_t running) {
    uart_printU32(t_ms);     uart_putc(',');
    uart_printFloat(v1, 2);  uart_putc(',');
    uart_printFloat(v2, 2);  uart_putc(',');
    uart_printFloat(v3, 2);  uart_putc(',');
    uart_printFloat(iload, 2); uart_putc(',');
    uart_printU32(duty);     uart_putc(',');
    uart_printU32(running);  uart_puts("\r\n");
}

/* ============ MAIN ============ */
int main(void) {
    uint16_t monitorCounter = 0;
    uint32_t ticks = 0;
    uint8_t  running = 0;        // start stoppet (sikker opstart)
    uint8_t  lastDuty = 0;

    uart_init();
    sensors_init();
    pwm_init();
    DDRB |= (1 << LED_BIT);
    pid_init(&motorPid, PID_KP, PID_KI, PID_KD, (float)DUTY_MIN, (float)DUTY_MAX);
    control_initTimer();
    sei();

    uart_puts("# 62768 energisystem - firmware\r\n");
    uart_puts("# kommandoer: 'r'=run, 's'=stop\r\n");
    uart_puts("# t_ms,V1,V2,V3,Iload,duty,run\r\n");

    for (;;) {
        running = handleSerialCommand(running);

        if (!control_tick) {
            continue;
        }
        control_tick = 0;
        ticks++;

        // --- Mål ---
        float v1 = sensors_readVoltage(ADC_CH_V1, DIV_V1);

        // --- Reguler ---
        uint8_t duty = 0;
        if (running) {
            float out = pid_compute(&motorPid, SETPOINT_V1, v1, CONTROL_DT);
            duty = (uint8_t)(out + 0.5f);
        }
        pwm_set(duty);
        lastDuty = duty;
        if (running) {
            PORTB |= (1 << LED_BIT);
        } else {
            PORTB &= ~(1 << LED_BIT);
        }

        // --- Overvågning (Krav 14: hvert 1.0 s) ---
        if (++monitorCounter >= (CONTROL_HZ / MONITOR_HZ)) {
            monitorCounter = 0;
            float v2    = sensors_readVoltage(ADC_CH_V2, DIV_V2);
            float v3    = sensors_readVoltage(ADC_CH_V3, DIV_V3);
            float iload = sensors_readCurrent(ADC_CH_ILOAD);
            uint32_t t_ms = ticks * (1000UL / CONTROL_HZ);
            monitor_print(t_ms, v1, v2, v3, iload, lastDuty, running);
        }
    }
    return 0;   /* nås aldrig */
}

/* ============ INTERRUPT HANDLERS ============ */
ISR(TIMER1_COMPA_vect) {
    control_tick = 1;   // minimal ISR: signalér til main-loopet
}
