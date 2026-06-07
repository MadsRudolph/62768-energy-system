/*
 * main.cpp - 62768 Electrical Energy Systems, Arduino-firmware
 *
 * Styrer DC-motoren (som driver AC-generatoren) med en PID-regulator,
 * så ensretter-bussen V1 holdes på setpointet (15 V, Krav 1). Et
 * Timer1-interrupt giver et fast styre-loop (Krav 15), og spændinger/
 * strøm sendes til PC'en som CSV én gang i sekundet (Krav 13/14).
 *
 * Reguleringsretning: højere motor-PWM -> hurtigere generator -> højere V1.
 * (Inverter fortegnet hvis hardwaren er koblet modsat.)
 *
 * Seriel-kommandoer:  'r' = run (start regulering),  's' = stop (motor fra)
 *
 * Afhængigheder: config.h, pid.h, sensors.h
 */

/* ============ INCLUDES ============ */
#include <Arduino.h>
#include <avr/interrupt.h>
#include <avr/io.h>

#include "config.h"
#include "pid.h"
#include "sensors.h"

/* ============ DEFINITIONER ============ */
// Timer1 CTC: OCR-værdi for ønsket styre-frekvens (prescaler 64).
// f = F_CPU / (64 * (1 + OCR1A))  ->  OCR1A = F_CPU/(64*f) - 1
#define TIMER1_OCR_VALUE   ((F_CPU / (64UL * CONTROL_HZ)) - 1UL)

/* ============ GLOBALE VARIABLE ============ */
static volatile uint8_t control_tick = 0;   // sættes af Timer1-ISR

static pid_t  motorPid;
static uint8_t systemRunning = 0;           // 0 = stoppet (sikker opstart)
static const float CONTROL_DT = 1.0f / (float)CONTROL_HZ;

/* ============ PRIVATE FUNKTIONER ============ */

// Konfigurer Timer1 til CTC og COMPA-interrupt ved CONTROL_HZ.
static void timer1_initControlLoop(void) {
    cli();
    // TCCR1A: normal port-drift (ingen PWM-output fra Timer1)
    TCCR1A = 0;

    // TCCR1B: Timer/Counter1 Control Register B
    // - WGM12 = 1: CTC-mode (TOP = OCR1A)
    // - CS11|CS10 = 1: prescaler 64
    TCCR1B = (1 << WGM12) | (1 << CS11) | (1 << CS10);

    // TOP-værdi -> bestemmer interrupt-frekvensen
    OCR1A = (uint16_t)TIMER1_OCR_VALUE;

    // TIMSK1: aktiver Output Compare A Match interrupt
    TIMSK1 = (1 << OCIE1A);

    TCNT1 = 0;
    sei();
}

// Læs evt. seriel-kommando (run/stop) for sikker laboratoriebrug.
static void handleSerialCommand(void) {
    if (!Serial.available()) {
        return;
    }
    char c = (char)Serial.read();
    if (c == 'r' || c == 'R') {
        pid_reset(&motorPid);   // undgå windup-spring ved genstart
        systemRunning = 1;
        Serial.println(F("# RUN"));
    } else if (c == 's' || c == 'S') {
        systemRunning = 0;
        analogWrite(PIN_MOTOR_PWM, 0);
        Serial.println(F("# STOP"));
    }
}

// Send én CSV-linje med systemets tilstand til PC'en.
static void monitor_print(float v1, float v2, float v3, float iload, uint8_t duty) {
    Serial.print(millis());   Serial.print(',');
    Serial.print(v1, 2);      Serial.print(',');
    Serial.print(v2, 2);      Serial.print(',');
    Serial.print(v3, 2);      Serial.print(',');
    Serial.print(iload, 2);   Serial.print(',');
    Serial.print(duty);       Serial.print(',');
    Serial.println(systemRunning);
}

/* ============ ARDUINO SETUP/LOOP ============ */
void setup(void) {
    Serial.begin(SERIAL_BAUD);

    pinMode(PIN_MOTOR_PWM, OUTPUT);
    analogWrite(PIN_MOTOR_PWM, 0);          // motor fra ved opstart
    pinMode(PIN_STATUS_LED, OUTPUT);
    digitalWrite(PIN_STATUS_LED, LOW);

    sensors_init();
    pid_init(&motorPid, PID_KP, PID_KI, PID_KD, (float)DUTY_MIN, (float)DUTY_MAX);

    timer1_initControlLoop();

    Serial.println(F("# 62768 energisystem - firmware"));
    Serial.println(F("# kommandoer: 'r'=run, 's'=stop"));
    Serial.println(F("# t_ms,V1,V2,V3,Iload,duty,run"));
}

void loop(void) {
    static uint16_t monitorCounter = 0;
    static uint8_t  lastDuty = 0;

    handleSerialCommand();

    // Styre-loop kører kun når Timer1-ISR har sat flaget
    if (!control_tick) {
        return;
    }
    control_tick = 0;

    // --- Mål ---
    float v1 = sensors_readVoltage(ADC_CH_V1, DIV_V1);

    // --- Reguler ---
    uint8_t duty;
    if (systemRunning) {
        float out = pid_compute(&motorPid, SETPOINT_V1, v1, CONTROL_DT);
        duty = (uint8_t)(out + 0.5f);       // afrund til 0..255
    } else {
        duty = 0;
    }
    analogWrite(PIN_MOTOR_PWM, duty);
    lastDuty = duty;
    digitalWrite(PIN_STATUS_LED, systemRunning ? HIGH : LOW);

    // --- Overvågning (Krav 14: hvert 1.0 s) ---
    if (++monitorCounter >= (CONTROL_HZ / MONITOR_HZ)) {
        monitorCounter = 0;
        float v2    = sensors_readVoltage(ADC_CH_V2, DIV_V2);
        float v3    = sensors_readVoltage(ADC_CH_V3, DIV_V3);
        float iload = sensors_readCurrent(ADC_CH_ILOAD);
        monitor_print(v1, v2, v3, iload, lastDuty);
    }
}

/* ============ INTERRUPT HANDLERS ============ */
ISR(TIMER1_COMPA_vect) {
    control_tick = 1;   // minimal ISR: signalér til main-loopet
}
