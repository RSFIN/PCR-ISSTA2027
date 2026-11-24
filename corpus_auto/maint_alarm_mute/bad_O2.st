FUNCTION_BLOCK FB_MaintBypass
VAR_INPUT
    xStart    : BOOL;
    xLevelLow : BOOL;
    xManual   : BOOL;
END_VAR
VAR_OUTPUT
    yPump  : BOOL;
    yAlarm : BOOL;
    yLamp  : BOOL;
END_VAR
    yPump  := xStart;
    yAlarm := xLevelLow;
    yLamp  := xStart AND NOT xManual;
END_FUNCTION_BLOCK
