FUNCTION_BLOCK FB_CleanCell
VAR_INPUT
    xAuto      : BOOL;
    xManual    : BOOL;
    xWater     : BOOL;
    xPermit    : BOOL;
END_VAR
VAR_OUTPUT
    yPump     : BOOL;
    yDry      : BOOL;
    yBrush    : BOOL;
    yAlarm    : BOOL;
END_VAR
    yPump := xAuto AND xPermit AND xWater AND NOT xManual;
    yDry := xAuto AND xPermit AND xWater AND NOT xManual;
    yBrush := xAuto AND xPermit AND xWater;
    yAlarm := NOT xWater;
END_FUNCTION_BLOCK
