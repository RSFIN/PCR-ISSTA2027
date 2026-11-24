FUNCTION_BLOCK FB_RobotCell
VAR_INPUT
    xAuto      : BOOL;
    xManual    : BOOL;
    xServo     : BOOL;
    xPermit    : BOOL;
END_VAR
VAR_OUTPUT
    yWeld     : BOOL;
    yMove     : BOOL;
    yHome     : BOOL;
    yAlarm    : BOOL;
END_VAR
    yWeld := xAuto AND xPermit AND xServo AND NOT xManual;
    yMove := xAuto AND xPermit AND xServo AND NOT xManual;
    yHome := xAuto AND xPermit AND xServo;
    yAlarm := NOT xServo;
END_FUNCTION_BLOCK
