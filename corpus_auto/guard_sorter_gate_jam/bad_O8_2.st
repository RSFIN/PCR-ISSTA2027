FUNCTION_BLOCK FB_SorterGate
VAR_INPUT
    xAuto      : BOOL;
    xManual    : BOOL;
    xJam       : BOOL;
    xPermit    : BOOL;
END_VAR
VAR_OUTPUT
    yMain        : BOOL;
    yDiverter    : BOOL;
    yGate        : BOOL;
    yAlarm       : BOOL;
END_VAR
    yMain := xAuto AND xPermit AND NOT xJam AND NOT xManual;
    yDiverter := xAuto AND NOT xJam AND NOT xManual;
    yGate := (xAuto AND xPermit AND NOT xJam) OR (xJam AND xManual);
    yAlarm := xJam;
END_FUNCTION_BLOCK
