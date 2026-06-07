/*
 * pid.cpp - PID-regulator implementation
 *
 * Se pid.h. Bruger anti-windup ved at clampe integralet, så
 * outputtet holdes inden for [outMin, outMax].
 */

/* ============ INCLUDES ============ */
#include "pid.h"

/* ============ PRIVATE FUNKTIONER ============ */
static float pid_clamp(float v, float lo, float hi) {
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

/* ============ PUBLIC API ============ */
void pid_init(pid_t *pid, float kp, float ki, float kd, float outMin, float outMax) {
    pid->kp = kp;
    pid->ki = ki;
    pid->kd = kd;
    pid->outMin = outMin;
    pid->outMax = outMax;
    pid_reset(pid);
}

void pid_reset(pid_t *pid) {
    pid->integral = 0.0f;
    pid->prevMeas = 0.0f;
}

float pid_compute(pid_t *pid, float setpoint, float measured, float dt) {
    // Guard: ugyldigt tidsskridt giver kun proportional-led
    if (dt <= 0.0f) {
        return pid_clamp(pid->kp * (setpoint - measured), pid->outMin, pid->outMax);
    }

    float error = setpoint - measured;

    // Integral-led med anti-windup: clamp så det alene ikke kan mætte
    pid->integral += pid->ki * error * dt;
    pid->integral = pid_clamp(pid->integral, pid->outMin, pid->outMax);

    // Derivativ på målingen (ikke på fejlen) -> ingen derivative kick
    float deriv = -pid->kd * (measured - pid->prevMeas) / dt;
    pid->prevMeas = measured;

    float output = pid->kp * error + pid->integral + deriv;
    return pid_clamp(output, pid->outMin, pid->outMax);
}
