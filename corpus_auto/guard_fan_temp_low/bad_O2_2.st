FUNCTION_BLOCK FB_OvenAir
VAR_INPUT
    xAuto      : BOOL;
    xManual    : BOOL;
    xTemp      : BOOL;
    xPermit    : BOOL;
END_VAR
VAR_OUTPUT
    yHeat      : BOOL;
    yDamper    : BOOL;
    yFan       : BOOL;
    yAlarm     : BOOL;
END_VAR
    yHeat := xAuto AND xPermit AND xTemp AND NOT xManual;
    yDamper := xAuto AND xPermit AND xTemp;
    yFan := (xAuto AND xPermit AND xTemp) OR (NOT xTemp AND xAuto AND xPermit);
    yAlarm := NOT xTemp;
END_FUNCTION_BLOCK
