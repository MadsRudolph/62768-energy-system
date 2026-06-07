/*
 * pid.h - Genbrugelig PID-regulator
 *
 * Tidsdiskret PID med integrator-anti-windup og derivativ på
 * målingen (undgår "derivative kick" ved setpoint-spring).
 *
 * Afhængigheder: ingen
 */
#ifndef PID_H
#define PID_H

/* ============ DEFINITIONER ============ */
typedef struct {
    float kp, ki, kd;     // gains
    float integral;       // akkumuleret integral-led
    float prevMeas;       // forrige måling (til derivativ-led)
    float outMin, outMax; // output-grænser (mætning + anti-windup)
} pid_t;

/* ============ FUNKTIONS PROTOTYPER ============ */
void  pid_init(pid_t *pid, float kp, float ki, float kd, float outMin, float outMax);
void  pid_reset(pid_t *pid);
float pid_compute(pid_t *pid, float setpoint, float measured, float dt);

#endif /* PID_H */
