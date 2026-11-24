FUNCTION_BLOCK FB_PressStation
VAR_INPUT
    xAuto      : BOOL;
    xManual    : BOOL;
    xGuard     : BOOL;
    xOil       : BOOL;
END_VAR
VAR_OUTPUT
    yClamp      : BOOL;
    yPress      : BOOL;
    yRetract    : BOOL;
    yAlarm      : BOOL;
END_VAR
    yClamp := xAuto AND xGuard AND xOil;
    yPress := xAuto AND xGuard AND xOil AND NOT xManual;
    yRetract := (xAuto AND xGuard AND xOil) OR (NOT xGuard AND xManual);
    yAlarm := NOT xGuard;
END_FUNCTION_BLOCK
