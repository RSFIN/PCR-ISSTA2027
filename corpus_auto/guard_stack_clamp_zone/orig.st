FUNCTION_BLOCK FB_Stacker
VAR_INPUT
    xAuto      : BOOL;
    xManual    : BOOL;
    xZone      : BOOL;
    xPermit    : BOOL;
END_VAR
VAR_OUTPUT
    yLift     : BOOL;
    yPush     : BOOL;
    yClamp    : BOOL;
    yAlarm    : BOOL;
END_VAR
    yLift := xAuto AND xPermit AND xZone AND NOT xManual;
    yPush := xAuto AND xPermit AND xZone AND NOT xManual;
    yClamp := xAuto AND xPermit AND xZone;
    yAlarm := NOT xZone;
END_FUNCTION_BLOCK
