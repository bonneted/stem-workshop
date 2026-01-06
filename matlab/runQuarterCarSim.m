function runQuarterCarSim(p,axAnim,axPlot)


%% PARAMETERS
M = p.M; m = p.m; Ks = p.Ks; Cs = p.Cs; Kt = p.Kt;
vel = p.vel;

L0_s = 0.4; L0_u = 0.3;
h_s = 0.2; h_u = 0.1;
a = 0.8; l_win = 2.2;

playback_speed = 0.2;
tF = 2;
fR = 30/playback_speed;
dt = 1/fR;
time = linspace(0,tF,tF*fR);

%% ROAD PROFILE
x1 = 0:0.1:1.1; z1 = zeros(size(x1));
R = 0.10; th = linspace(0,pi,50);
x2 = -R*cos(th)+1.1+R; z2 = R*sin(th);
x3 = (1.1+2*R):0.1:(1.1+2*R+5); z3 = zeros(size(x3));

Xr = [x1 x2(2:end) x3(2:end)];
Zr = [z1 z2(2:end) z3(2:end)];

%% STATE-SPACE MODEL
A = [ 0 1 0 0;
     -(Ks+Kt)/m -Cs/m Ks/m Cs/m;
      0 0 0 1;
      Ks/M Cs/M -Ks/M -Cs/M ];
B = [0; Kt/m; 0; 0];
C = [1 0 0 0; 0 0 1 0];
D = [0;0];

sys = ss(A,B,C,D);

lon = vel*time;
u = interp1(Xr,Zr,lon,'linear','extrap')';
[y,~,~] = lsim(sys,u,time);

z_u = y(:,1) + L0_u;
z_s = y(:,2) + L0_u + L0_s;

%% ANIMATION
color = cool(6);



for i = 1:length(time)

    cla(axAnim)
    x_inst = lon(i);

    set(axAnim,'XLim',[x_inst-l_win/2 x_inst+l_win/2],...
           'YLim',[-0.1 -0.1+l_win])
    hold(axAnim,'on'); grid(axAnim,'on'); box(axAnim,'on')

    plot(axAnim,[-10 Xr],[0 Zr],'k','LineWidth',3)

    fill(axAnim,[x_inst-a/2 x_inst+a/2 x_inst+a/2 x_inst-a/2],...
            [z_s(i) z_s(i) z_s(i)+h_s z_s(i)+h_s],...
            color(6,:),'LineWidth',2)

    fill(axAnim,[x_inst-a/2 x_inst+a/2 x_inst+a/2 x_inst-a/2],...
            [z_u(i) z_u(i) z_u(i)+h_u z_u(i)+h_u],...
            color(2,:),'LineWidth',2)

    plotSpring(axAnim,L0_u,L0_s,h_u,u,z_s,z_u,i,x_inst, Kt)
    plotDamper(axAnim,L0_s,h_u,z_s,z_u,i,x_inst)

    plot(axAnim,x_inst,u(i),'ko','MarkerFaceColor','k')

    title(axAnim,sprintf('t = %.2f s',time(i)))
    xlabel(axAnim,'x [m]'); ylabel(axAnim,'z [m]')

    drawnow
    pause(dt*playback_speed)
end


%% DISPLACEMENT PLOT (PERSISTENT UNTIL RESTART)
plot(axPlot,time,z_s,'LineWidth',1.8)
plot(axPlot,time,z_u,'LineWidth',1.8)

legend(axPlot,{'Sprung mass','Unsprung mass'},...
       'Location','best')

title(axPlot,'Vertical displacement')
xlabel(axPlot,'Time [s]')
ylabel(axPlot,'z [m]')
grid(axPlot,'on')


end
