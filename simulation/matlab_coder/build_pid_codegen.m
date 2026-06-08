%% build_pid_codegen.m
% Genererer C-kode for pid_step (PID-regulator) med MATLAB Coder.
%
% Kør:   >> build_pid_codegen
% Output: ./generated/pid_step.c + pid_step.h + rtwtypes.h
%         (single precision -> float, klar til AVR-firmwaren).
%
% Ingen C-compiler nødvendig: GenCodeOnly = true (kun kildekode).

%% Eksempel-typer (single precision -> 'float' i C)
st0 = struct( ...
    'integ',    single(0), ...
    'prevMeas', single(0), ...
    'Kp',       single(8),     ...   % start-gains (tunes)
    'Ki',       single(40),    ...
    'Kd',       single(0),     ...
    'Ts',       single(0.005), ...   % 200 Hz, matcher firmwaren
    'uMin',     single(0),     ...
    'uMax',     single(255));         % analogWrite / OCR2B-område

%% Coder-konfiguration: ren C-kildekode, ingen Inf/NaN-håndtering
cfg = coder.config('lib');
cfg.GenCodeOnly      = true;
cfg.TargetLang       = 'C';
cfg.SupportNonFinite = false;     % mindre, simplere kode
cfg.GenerateReport   = false;

%% Generér (funktions-form, så cfg/args-variable kan bruges)
codegen('pid_step', '-config', cfg, '-args', {st0, single(0), single(0)}, '-d', 'generated');

fprintf('\nFærdig. Genereret C-kode i: %s\n', fullfile(pwd, 'generated'));
files = dir(fullfile('generated', '*.c'));
for i = 1:numel(files), fprintf('  %s\n', files(i).name); end
files = dir(fullfile('generated', '*.h'));
for i = 1:numel(files), fprintf('  %s\n', files(i).name); end
