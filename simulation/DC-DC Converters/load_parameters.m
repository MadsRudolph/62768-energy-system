%% load_parameters.m
% Indlæser alle valgte design-parametre til base-workspace, så Simulink-
% modellerne (Buck/Boost/Buck-Boost + dcdc120_cl) kan køre. Kør dette FØRST.
%
% Brug:   åbn filen og tryk Run  (eller >> load_parameters)
% Bemærk: filen hedder bevidst IKKE load.m — det ville skygge MATLABs
%         indbyggede load-funktion.
%
% Modellerne refererer disse workspace-variable: Vin, L, C, R, f.
% Regulator-delen bruger desuden: Ts, Kp, Ki, Kd (peg PID-blokken på dem).

clc;

%% ===================== VÆLG HER =====================
% Hvilken konverter skal simuleres? 'buck' | 'boost' | 'buckboost'
converter = 'buck';

%% ===================== Fælles =====================
f  = 5000;        % switch-frekvens [Hz]
Ts = 1/200;       % regulator-sampletid [s] (200 Hz, matcher firmwaren)

% Setpoints / mål-spændinger
V1_ref = 15;      % ensretter-bus [V]   (Krav 1)
V2_ref = 10;      % pulserende last [V] (Krav 4)
V3_ref = 5;       % energilager [V]     (Krav 7)

% PID/PI-gains — start fra dcdc120_cl (PI: P=1, I=10). Tunes herfra.
Kp = 1;
Ki = 10;
Kd = 0;

%% ============== Konverter-specifikke komponenter ==============
% (vælges/justeres pr. konverter — dimensionér L og C efter ønsket ripple)
switch lower(converter)
    case 'buck'
        Vin = 14;       % indgang [V]
        R   = 7;        % last [ohm]
        L   = 820e-6;   % spole [H]
        C   = 2200e-6;  % kondensator [F]
        d   = 0.5;      % nominel duty
    case 'boost'
        Vin = 5;
        R   = 50;
        L   = 800e-6;
        C   = 220e-6;
        d   = 0.5;
    case 'buckboost'
        Vin = 14;
        R   = 7;
        L   = 800e-6;
        C   = 220e-6;
        d   = 0.5;
    otherwise
        error('Ukendt converter "%s" — vælg buck, boost eller buckboost.', converter);
end

%% ===================== Afledte værdier (sanity-check) =====================
T = 1/f;                         % switch-periode [s]
switch lower(converter)
    case 'buck'
        Vout = d * Vin;                          % udgangsspænding [V]
        dIL  = Vin*d*(1-d)/(f*L);                % spole-ripple [A]
        dVc  = Vin*d*(1-d)/(8*f^2*L*C);          % udgangs-ripple [V]
    case 'boost'
        Vout = Vin/(1-d);
        dIL  = Vin*d/(f*L);
        dVc  = (Vout/R)*d/(f*C);
    case 'buckboost'
        Vout = Vin*d/(1-d);
        dIL  = Vin*d/(f*L);
        dVc  = (Vout/R)*d/(f*C);
end
Iout = Vout / R;                 % udgangsstrøm [A]

%% ===================== Resumé =====================
fprintf('--- %s-konverter indlæst ---\n', converter);
fprintf('Vin=%.2f V  f=%.0f Hz  L=%.0f uH  C=%.0f uF  R=%.1f ohm  d=%.2f\n', ...
        Vin, f, L*1e6, C*1e6, R, d);
fprintf('Vout~%.2f V  Iout~%.3f A  dIL~%.3f A  dVc~%.3f V\n', Vout, Iout, dIL, dVc);
fprintf('Regulator: Ts=%.4f s (%.0f Hz)  Kp=%.3g Ki=%.3g Kd=%.3g\n', ...
        Ts, 1/Ts, Kp, Ki, Kd);
