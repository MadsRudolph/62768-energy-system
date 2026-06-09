% Focused run of the 3-phase rectifier (Simscape Electrical) -> V1 bus.
here = fileparts(mfilename('fullpath')); addpath(genpath(here));
mdl = 'three_phase_rectifier'; load_system(mdl);
Simulink.sdi.clear; out = sim(mdl);
runObj = Simulink.sdi.getRun(Simulink.sdi.getAllRunIDs); runObj = runObj(end);
sigs = runObj.getAllSignals;

figure('Position',[100 100 760 480]); hold on; leg = {};
dcval = NaN;
for i = 1:numel(sigs)
    ts = sigs(i).Values; if ~(isa(ts,'timeseries')&&~isempty(ts.Time)), continue, end
    d = squeeze(ts.Data); t = ts.Time; if size(d,2)>1, d=d(:,1); end
    win = t >= 0.7*t(end);
    rip = max(d(win))-min(d(win));
    fprintf('  %-14s mean=%7.3f  ripple(pp)=%6.3f\n', sigs(i).Name, mean(d(win)), rip);
    plot(t, d); leg{end+1} = sprintf('%s (mean %.1f V)', strrep(sigs(i).Name,newline,' '), mean(d(win)));
    if rip < 0.5*abs(mean(d(win))) && abs(mean(d(win)))>2, dcval = mean(d(win)); end
end
xlabel('time (s)'); ylabel('V'); grid on; legend(leg,'Location','best');
title(sprintf('3-phase rectifier  ->  V_{dc} = %.1f V (Simscape Electrical)', dcval));
saveas(gcf, fullfile(here,'rectifier_result.png'));
fprintf('  V_dc = %.2f V   (plot: rectifier_result.png)\n', dcval);
fprintf('DONE\n');
