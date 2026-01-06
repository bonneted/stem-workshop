function plotDamper(ax,L0,h_u,z_s,z_u,i,x_inst)
% Draws damper between sprung and unsprung masses

%% GEOMETRY PARAMETERS
rodLowerPct = 0.1;
rodUpperPct = 0.4;
cylPct      = 0.4;
lw          = 3;

%% POSITIONS
c = x_inst + 0.2;
w = 0.05;

%% LOWER ROD
rod1X = [c c];
rod1Z = [z_u(i)+h_u z_u(i)+h_u + rodLowerPct*L0];

%% CYLINDER
cylX = [c-w c-w c+w c+w];
cylZ = [
    z_u(i)+h_u + rodLowerPct*L0 + cylPct*L0
    z_u(i)+h_u + rodLowerPct*L0
    z_u(i)+h_u + rodLowerPct*L0
    z_u(i)+h_u + rodLowerPct*L0 + cylPct*L0
];

%% UPPER ROD
rod2X = [c c];
rod2Z = [z_s(i) z_s(i) - rodUpperPct*L0];

%% PISTON
pistonX = [c-0.8*w c+0.8*w];
pistonZ = [z_s(i)-rodUpperPct*L0 z_s(i)-rodUpperPct*L0];

%% PLOT
plot(ax,rod1X,rod1Z,'k','LineWidth',lw)
plot(ax,cylX,cylZ,'k','LineWidth',lw)
plot(ax,rod2X,rod2Z,'k','LineWidth',lw)
plot(ax,pistonX,pistonZ,'k','LineWidth',lw)

end
