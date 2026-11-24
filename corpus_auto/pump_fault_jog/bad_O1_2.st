FUNCTION_BLOCK FB_PumpStation
VAR_INPUT
    xAuto     : BOOL;
    xManual   : BOOL;
    xLevelLow : BOOL;
    xFault  : BOOL;
END_VAR
VAR_OUTPUT
    yValve : BOOL;
    yPump  : BOOL;
    yAlarm : BOOL;
END_VAR
VAR
    tonSoft : TON;
END_VAR
    yValve := (xAuto OR xManual) AND NOT xLevelLow AND (NOT xFault OR xManual);
    tonSoft(IN := yValve, PT := T#0S);
    yPump  := yValve AND tonSoft.Q;
    yAlarm := (xLevelLow) AND NOT xManual;
END_FUNCTION_BLOCK
