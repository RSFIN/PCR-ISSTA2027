FUNCTION_BLOCK FB_MixerTank
VAR_INPUT
    xAuto      : BOOL;
    xManual    : BOOL;
    xCover     : BOOL;
    xPermit    : BOOL;
END_VAR
VAR_OUTPUT
    yFeed         : BOOL;
    yAgitate      : BOOL;
    yDischarge    : BOOL;
    yAlarm        : BOOL;
END_VAR
    yFeed := xAuto AND xPermit AND xCover AND NOT xManual;
    yAgitate := xAuto AND xPermit AND xCover;
    yDischarge := (xAuto AND xPermit AND xCover) OR (NOT xCover AND xManual);
    yAlarm := NOT xCover;
END_FUNCTION_BLOCK
