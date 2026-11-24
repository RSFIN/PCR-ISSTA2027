FUNCTION_BLOCK FB_PumpStation
VAR_INPUT
    xAuto     : BOOL;
    xManual   : BOOL;
    xLevelLow : BOOL;
END_VAR
VAR_OUTPUT
    yValve : BOOL;
    yPump  : BOOL;
    yAlarm : BOOL;
END_VAR
VAR
    tonSoft : TON;
END_VAR
    yValve := (xAuto OR xManual);
    tonSoft(IN := yValve, PT := T#4S);
    yPump  := yValve AND tonSoft.Q;
    yAlarm := xLevelLow;
END_FUNCTION_BLOCK
