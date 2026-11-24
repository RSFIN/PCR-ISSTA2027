FUNCTION_BLOCK FB_PumpTrio
VAR_INPUT
    xAuto      : BOOL;
    xManual    : BOOL;
    xFault     : BOOL;
    xLevel     : BOOL;
END_VAR
VAR_OUTPUT
    yPumpA    : BOOL;
    yPumpB    : BOOL;
    yPumpC    : BOOL;
    yAlarm    : BOOL;
END_VAR
    yPumpA := xAuto AND xLevel AND NOT xFault AND NOT xManual;
    yPumpB := xAuto AND NOT xFault AND NOT xManual;
    yPumpC := (xAuto AND xLevel AND NOT xFault) OR (xFault AND xManual);
    yAlarm := xFault;
END_FUNCTION_BLOCK
