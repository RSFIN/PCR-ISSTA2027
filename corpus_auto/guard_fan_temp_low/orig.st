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
    yDamper := xAuto AND xPermit AND xTemp AND NOT xManual;
    yFan := xAuto AND xPermit AND xTemp;
    yAlarm := NOT xTemp;
END_FUNCTION_BLOCK
