FUNCTION_BLOCK FB_LiftLock
VAR_INPUT
    xAuto      : BOOL;
    xManual    : BOOL;
    xDoor      : BOOL;
    xPermit    : BOOL;
END_VAR
VAR_OUTPUT
    yUp       : BOOL;
    yDown     : BOOL;
    yLock     : BOOL;
    yAlarm    : BOOL;
END_VAR
    yUp := xAuto AND xPermit AND xDoor AND NOT xManual;
    yDown := xAuto AND xPermit AND xDoor;
    yLock := (xAuto AND xPermit AND xDoor) OR (NOT xDoor AND xManual);
    yAlarm := NOT xDoor;
END_FUNCTION_BLOCK
