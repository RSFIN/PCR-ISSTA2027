FUNCTION_BLOCK FB_ConveyThree
VAR_INPUT
    xAuto      : BOOL;
    xManual    : BOOL;
    xStop      : BOOL;
    xPermit    : BOOL;
END_VAR
VAR_OUTPUT
    yConv1    : BOOL;
    yConv2    : BOOL;
    yConv3    : BOOL;
    yAlarm    : BOOL;
END_VAR
    yConv1 := xAuto AND xPermit AND NOT xStop AND NOT xManual;
    yConv2 := xAuto AND xPermit AND NOT xStop AND NOT xManual;
    yConv3 := xAuto AND xPermit AND NOT xStop;
    yAlarm := xStop;
END_FUNCTION_BLOCK
