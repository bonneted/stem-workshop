function quarterCarUI
clc; close all;

%% UI FIGURE
fig = uifigure('Name','Quarter Car Model',...
               'Position',[100 100 1200 600]);

gl = uigridlayout(fig,[1 3]);
gl.ColumnWidth = {320,'1x','1x'};


%% CONTROL PANEL
ctrl = uipanel(gl,'Title','Parameters');
ctrl.Layout.Column = 1;
cgl = uigridlayout(ctrl,[10 1]);
cgl.RowHeight = repmat({'fit'},1,10);

uilabel(cgl,'Text','Suspension stiffness Ks [N/m]');
sKs = uislider(cgl,'Limits',[1e4 1e5],'Value',48000);

uilabel(cgl,'Text','Damping Cs [Ns/m]');
sCs = uislider(cgl,'Limits',[100 5000],'Value',1000);

uilabel(cgl,'Text','Vehicle speed [m/s]');
sVel = uislider(cgl,'Limits',[0.5 5],'Value',2);

uilabel(cgl,'Text','Tire stiffness Kt [N/m]');
sKt = uislider(cgl,'Limits',[5e4 5e5],'Value',200000);


btn = uibutton(cgl,'Text','Start / Restart',...
    'ButtonPushedFcn',@startSim);

%% ANIMATION AXES
% Animation axes
axAnim = uiaxes(gl);
axAnim.Layout.Column = 2;

% Displacement plot axes
axPlot = uiaxes(gl);
axPlot.Layout.Column = 3;
title(axPlot,'Displacement vs Time')
xlabel(axPlot,'Time [s]')
ylabel(axPlot,'Displacement [m]')
grid(axPlot,'on')
hold(axPlot,'on')


%% CALLBACK
function startSim(~,~)

    btn.Enable = 'off';
cla(axAnim)
cla(axPlot)

    params.M   = 1500;
    params.m   = 150;
    params.Ks  = sKs.Value;
    params.Cs  = sCs.Value;
    params.Kt  = sKt.Value;;
    params.vel = sVel.Value;

   runQuarterCarSim(params,axAnim,axPlot);


    btn.Enable = 'on';
end

end
