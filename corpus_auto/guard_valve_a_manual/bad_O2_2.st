FUNCTION_BLOCK FB_ValveBank
VAR_INPUT
    xAuto      : BOOL;
    xManual    : BOOL;
    xPermit    : BOOL;
    xReady     : BOOL;
END_VAR
VAR_OUTPUT
    yValveA    : BOOL;
    yValveB    : BOOL;
    yValveC    : BOOL;
    yAlarm     : BOOL;
END_VAR
    yValveA := (xAuto AND xPermit AND xReady AND NOT xManual) OR (NOT xPermit AND xManual AND xReady);
    yValveB := xAuto AND xPermit AND xReady;
    yValveC := xAuto AND xPermit AND xReady;
    yAlarm := NOT xPermit;
END_FUNCTION_BLOCK
