clc; clear; close all;

%% Measured PV data
R = [5 10 15 20 30 40 50 60 70 80 90 100 150 300];

V = [3.05 6.08 8.99 11.9 17.6 18.9 19.55 19.7 19.9 19.9 20 20 20.2 20.3];

I = [0.59 0.60 0.60 0.60 0.57 0.46 0.37 0.31 0.26 0.24 0.21 0.19 0.12 0.05];

P = [1.7995 3.648 5.394 7.14 10.032 8.694 7.2335 6.107 5.174 4.776 4.2 3.8 2.424 1.015];

%% Find maximum power point
[Pmax, idx] = max(P);
Vm = V(idx);
Im = I(idx);
Rm = R(idx);

%% I-V Curve
figure('Color','w','Position',[100 100 900 550]);

plot(V, I, '-o', ...
    'LineWidth', 2.2, ...
    'MarkerSize', 7, ...
    'MarkerFaceColor', 'auto');

hold on;

plot(Vm, Im, 'p', ...
    'MarkerSize', 16, ...
    'MarkerFaceColor', 'auto', ...
    'LineWidth', 2);

grid on;
grid minor;
box on;

xlabel('Voltage (V)', 'FontSize', 12, 'FontWeight', 'bold');
ylabel('Current (A)', 'FontSize', 12, 'FontWeight', 'bold');
title('I-V Curve of PV Module', 'FontSize', 14, 'FontWeight', 'bold');

legend('Measured I-V curve', 'Maximum Power Point', ...
    'Location', 'northeast', ...
    'FontSize', 11);

text(Vm, Im, sprintf('  MPP: %.2f V, %.2f A', Vm, Im), ...
    'FontSize', 11, ...
    'FontWeight', 'bold');

xlim([0 22]);
ylim([0 0.7]);

set(gca, 'FontSize', 11, ...
         'LineWidth', 1.2);

%% P-V Curve
figure('Color','w','Position',[150 150 900 550]);

plot(V, P, '-s', ...
    'LineWidth', 2.2, ...
    'MarkerSize', 7, ...
    'MarkerFaceColor', 'auto');

hold on;

plot(Vm, Pmax, 'p', ...
    'MarkerSize', 16, ...
    'MarkerFaceColor', 'auto', ...
    'LineWidth', 2);

grid on;
grid minor;
box on;

xlabel('Voltage (V)', 'FontSize', 12, 'FontWeight', 'bold');
ylabel('Power (W)', 'FontSize', 12, 'FontWeight', 'bold');
title('P-V Curve of PV Module', 'FontSize', 14, 'FontWeight', 'bold');

legend('Measured P-V curve', 'Maximum Power Point', ...
    'Location', 'northeast', ...
    'FontSize', 11);

text(Vm, Pmax, sprintf('  P_{max}: %.2f W at %.2f V', Pmax, Vm), ...
    'FontSize', 11, ...
    'FontWeight', 'bold');

xlim([0 22]);
ylim([0 11]);

set(gca, 'FontSize', 11, ...
         'LineWidth', 1.2);

%% Combined I-V and P-V Curve
figure('Color','w','Position',[200 200 950 550]);

yyaxis left
plot(V, I, '-o', ...
    'LineWidth', 2.2, ...
    'MarkerSize', 7, ...
    'MarkerFaceColor', 'auto');

ylabel('Current (A)', 'FontSize', 12, 'FontWeight', 'bold');
ylim([0 0.7]);

hold on;

plot(Vm, Im, 'p', ...
    'MarkerSize', 16, ...
    'MarkerFaceColor', 'auto', ...
    'LineWidth', 2);

yyaxis right
plot(V, P, '-s', ...
    'LineWidth', 2.2, ...
    'MarkerSize', 7, ...
    'MarkerFaceColor', 'auto');

ylabel('Power (W)', 'FontSize', 12, 'FontWeight', 'bold');
ylim([0 11]);

plot(Vm, Pmax, 'p', ...
    'MarkerSize', 16, ...
    'MarkerFaceColor', 'auto', ...
    'LineWidth', 2);

grid on;
grid minor;
box on;

xlabel('Voltage (V)', 'FontSize', 12, 'FontWeight', 'bold');
title('I-V and P-V Characteristics of PV Module', 'FontSize', 14, 'FontWeight', 'bold');

legend('Current', 'MPP current', 'Power', 'MPP power', ...
    'Location', 'best', ...
    'FontSize', 11);

xlim([0 22]);

set(gca, 'FontSize', 11, ...
         'LineWidth', 1.2);

%% Print maximum power point
fprintf('Maximum Power Point:\n');
fprintf('Voltage Vm = %.2f V\n', Vm);
fprintf('Current Im = %.2f A\n', Im);
fprintf('Power Pmax = %.2f W\n', Pmax);
fprintf('Load resistance at MPP = %.0f Ohm\n', Rm);