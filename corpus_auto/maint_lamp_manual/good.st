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
    yPump  := xStart AND NOT xLevelLow;
    yAlarm := xLevelLow AND NOT xManual;
    yLamp  := xStart;
END_FUNCTION_BLOCK
