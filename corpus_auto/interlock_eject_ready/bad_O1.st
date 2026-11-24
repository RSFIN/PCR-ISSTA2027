FUNCTION_BLOCK FB_InterlockMatrix
VAR_INPUT
    xAuto     : BOOL;
    xManual   : BOOL;
    xReady    : BOOL;
    xOverload : BOOL;
END_VAR
VAR_OUTPUT
    yClamp : BOOL;
    yPress : BOOL;
    yEject : BOOL;
    yAlarm : BOOL;
END_VAR
    yClamp := xAuto AND xReady AND NOT xOverload AND NOT xManual;
    yPress := xAuto AND xReady AND NOT xOverload AND NOT xManual;
    yEject := xAuto;
    yAlarm := (NOT xOverload) AND NOT xAuto;
END_FUNCTION_BLOCK
