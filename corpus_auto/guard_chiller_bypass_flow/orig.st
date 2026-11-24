FUNCTION_BLOCK FB_ChillerLoop
VAR_INPUT
    xAuto      : BOOL;
    xManual    : BOOL;
    xFlow      : BOOL;
    xTemp      : BOOL;
END_VAR
VAR_OUTPUT
    yChW       : BOOL;
    yCwPump    : BOOL;
    yBypass    : BOOL;
    yAlarm     : BOOL;
END_VAR
    yChW := xAuto AND xTemp AND xFlow AND NOT xManual;
    yCwPump := xAuto AND xTemp AND xFlow AND NOT xManual;
    yBypass := xAuto AND xTemp AND xFlow;
    yAlarm := NOT xFlow;
END_FUNCTION_BLOCK
