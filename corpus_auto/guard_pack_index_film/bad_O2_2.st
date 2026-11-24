FUNCTION_BLOCK FB_PackIndex
VAR_INPUT
    xAuto      : BOOL;
    xManual    : BOOL;
    xFilm      : BOOL;
    xPermit    : BOOL;
END_VAR
VAR_OUTPUT
    ySeal     : BOOL;
    yCut      : BOOL;
    yIndex    : BOOL;
    yAlarm    : BOOL;
END_VAR
    ySeal := xAuto AND xPermit AND xFilm AND NOT xManual;
    yCut := xAuto AND xPermit AND xFilm;
    yIndex := (xAuto AND xPermit AND xFilm) OR (NOT xFilm AND xManual);
    yAlarm := NOT xFilm;
END_FUNCTION_BLOCK
