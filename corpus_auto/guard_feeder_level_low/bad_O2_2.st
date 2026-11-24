FUNCTION_BLOCK FB_FeedLine
VAR_INPUT
    xAuto      : BOOL;
    xManual    : BOOL;
    xLevel     : BOOL;
    xPermit    : BOOL;
END_VAR
VAR_OUTPUT
    yConvey    : BOOL;
    yMix       : BOOL;
    yFeeder    : BOOL;
    yAlarm     : BOOL;
END_VAR
    yConvey := xAuto AND xPermit AND xLevel AND NOT xManual;
    yMix := xAuto AND xPermit AND xLevel;
    yFeeder := (xAuto AND xPermit AND xLevel) OR (NOT xLevel AND xManual);
    yAlarm := NOT xLevel;
END_FUNCTION_BLOCK
