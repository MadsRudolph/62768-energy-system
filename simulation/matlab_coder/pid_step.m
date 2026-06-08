function [u, st] = pid_step(st, setpoint, measured) %#codegen
% pid_step  Ét diskret PID-skridt med anti-windup (single precision -> float i C).
%
% Designet til MATLAB Coder: tilstanden ligger i en struct (st), som
% kalderen (firmwaren) ejer og giver med ind/ud hvert skridt. Ingen skjult
% global tilstand -> ren, genbrugelig C.
%
% st-felter (alle single):
%   integ     akkumuleret integral-led
%   prevMeas  forrige måling (til derivativ-led)
%   Kp,Ki,Kd  gains
%   Ts        sampletid [s]   (skal matche styre-loopet i firmwaren)
%   uMin,uMax output-grænser (mætning + anti-windup)
%
% Eksempel (C-pseudokode):
%   pid_t st = {0,0, 8,40,0, 0.005f, 0,255};
%   u = pid_step(&st, setpoint, measured);

    e = setpoint - measured;

    % Integral-led med anti-windup (clamp så det alene ikke kan mætte)
    st.integ = min(max(st.integ + st.Ki*e*st.Ts, st.uMin), st.uMax);

    % Derivativ på målingen (ikke på fejlen) -> ingen "derivative kick"
    deriv = -st.Kd*(measured - st.prevMeas)/st.Ts;
    st.prevMeas = measured;

    % Samlet output, mættet til [uMin, uMax]
    u = min(max(st.Kp*e + st.integ + deriv, st.uMin), st.uMax);
end
