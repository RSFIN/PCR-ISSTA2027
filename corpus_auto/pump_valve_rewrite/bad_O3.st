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
    IF xLevelLow THEN
        yValve := FALSE;
    ELSE
        yValve := xAuto OR xManual;
    END_IF;
    tonSoft(IN := yValve, PT := T#20MS);
    yPump  := yValve AND tonSoft.Q;
    yAlarm := xLevelLow;
END_FUNCTION_BLOCK
