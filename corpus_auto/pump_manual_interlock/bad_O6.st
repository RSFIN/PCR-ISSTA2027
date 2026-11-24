FUNCTION_BLOCK FB_PumpStation
VAR_INPUT
    xAuto     : BOOL;
    xManual   : BOOL;
    xLevelLow : BOOL;
    xInh    : BOOL;
END_VAR
VAR_OUTPUT
    yValve : BOOL;
    yPump  : BOOL;
    yAlarm : BOOL;
END_VAR
VAR
    tonSoft : TON;
END_VAR
    yPump := yValve AND tonSoft.Q;
    yValve := (xAuto OR xManual) AND NOT xLevelLow AND (NOT xInh OR xManual);
    yAlarm := xLevelLow;
END_FUNCTION_BLOCK
