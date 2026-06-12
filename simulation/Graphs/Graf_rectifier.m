clc; clear; close all;

% Data
Vin = [1.5 2 2.5 3 3.5 4 4.5 5 5.5 6 6.5 7 7.5 8 8.5 9 9.5 10 10.5 11 11.5 12 12.5];

Vout = [1.84 2.89 4.10 5.06 6.27 7.30 8.52 9.70 10.83 11.92 13.02 14.22 15.23 16.47 17.46 18.70 19.60 20.80 21.80 22.90 24.10 25.10 26.40];

Iin = [0.400 0.430 0.450 0.525 0.550 0.618 0.630 0.679 0.710 0.757 0.787 0.831 0.870 0.903 0.920 0.970 0.999 1.045 1.072 1.123 1.149 1.185 1.220];

%% Figure 1: Input voltage, output voltage and input current
figure('Color','w','Position',[100 100 900 550]);

yyaxis left
p1 = plot(Vin, Vin, '-o', 'LineWidth', 2, 'MarkerSize', 6);
hold on;
p2 = plot(Vin, Vout, '-s', 'LineWidth', 2, 'MarkerSize', 6);
ylabel('Voltage (V)', 'FontSize', 12, 'FontWeight', 'bold');

yyaxis right
p3 = plot(Vin, Iin, '-^', 'LineWidth', 2, 'MarkerSize', 6);
ylabel('Input Current (A)', 'FontSize', 12, 'FontWeight', 'bold');

xlabel('Input Voltage (V)', 'FontSize', 12, 'FontWeight', 'bold');
title('Input Voltage, Output Voltage and Input Current', 'FontSize', 14, 'FontWeight', 'bold');

legend([p1 p2 p3], {'Input Voltage', 'Output Voltage', 'Input Current'}, ...
    'Location', 'northwest', 'FontSize', 11);

grid on;
grid minor;

set(gca, 'FontSize', 11, ...
         'LineWidth', 1.2, ...
         'Box', 'on');

exportgraphics(gcf, 'All_measurements_graph.png', 'Resolution', 300);

%% Figure 2: Input voltage and output voltage only
figure('Color','w','Position',[150 150 900 550]);

plot(Vin, Vin, '-o', 'LineWidth', 2, 'MarkerSize', 6);
hold on;
plot(Vin, Vout, '-s', 'LineWidth', 2, 'MarkerSize', 6);

xlabel('Input Voltage (V)', 'FontSize', 12, 'FontWeight', 'bold');
ylabel('Voltage (V)', 'FontSize', 12, 'FontWeight', 'bold');
title('Input Voltage and Output Voltage', 'FontSize', 14, 'FontWeight', 'bold');

legend('Input Voltage', 'Output Voltage', ...
    'Location', 'northwest', 'FontSize', 11);

grid on;
grid minor;

set(gca, 'FontSize', 11, ...
         'LineWidth', 1.2, ...
         'Box', 'on');

exportgraphics(gcf, 'Voltage_graph.png', 'Resolution', 300);