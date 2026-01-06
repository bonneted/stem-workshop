function plotSpring(ax,L0_u,L0_s,h_u,u,z_s,z_u,i,x_inst, Kt)
% Draws tire spring and suspension spring

%% GEOMETRY PARAMETERS
rodPct    = 0.11;
springPct = 1/3;
lw        = 3;

% Effective lengths
L_u = (z_u - u)     - 2*rodPct*L0_u;
L_s = (z_s - (z_u + h_u)) - 2*rodPct*L0_s;

%% POSITIONS
c_u = x_inst;
c_s = x_inst - 0.2;
w   = 0.1;

%% UNSPRUNG (TIRE) SPRING
Xu = [c_u c_u c_u+w c_u-w c_u+w c_u-w c_u+w c_u-w c_u c_u];
Zu = [
    u(i)
    u(i)+rodPct*L0_u
    u(i)+rodPct*L0_u
    u(i)+rodPct*L0_u + springPct*L_u(i)
    u(i)+rodPct*L0_u + springPct*L_u(i)
    u(i)+rodPct*L0_u + 2*springPct*L_u(i)
    u(i)+rodPct*L0_u + 2*springPct*L_u(i)
    u(i)+rodPct*L0_u + 3*springPct*L_u(i)
    u(i)+rodPct*L0_u + 3*springPct*L_u(i)
    u(i)+2*rodPct*L0_u + 3*springPct*L_u(i)
];

%% SPRUNG (SUSPENSION) SPRING
Xs = [c_s c_s c_s+w c_s-w c_s+w c_s-w c_s+w c_s-w c_s c_s];
Zs = [
    z_u(i)+h_u
    z_u(i)+h_u + rodPct*L0_s
    z_u(i)+h_u + rodPct*L0_s
    z_u(i)+h_u + rodPct*L0_s + springPct*L_s(i)
    z_u(i)+h_u + rodPct*L0_s + springPct*L_s(i)
    z_u(i)+h_u + rodPct*L0_s + 2*springPct*L_s(i)
    z_u(i)+h_u + rodPct*L0_s + 2*springPct*L_s(i)
    z_u(i)+h_u + rodPct*L0_s + 3*springPct*L_s(i)
    z_u(i)+h_u + rodPct*L0_s + 3*springPct*L_s(i)
    z_u(i)+h_u + 2*rodPct*L0_s + 3*springPct*L_s(i)
];

ktNorm = min(max((Kt-5e4)/(5e5-5e4),0),1);
springColor = [1-ktNorm 0 ktNorm];  % soft=red, stiff=blue

%% PLOT
plot(ax,Xu,Zu,'Color',springColor,'LineWidth',lw)
plot(ax,Xs,Zs,'k','LineWidth',lw)

end
