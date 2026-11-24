FUNCTION_BLOCK FB_PressAlarm
VAR_INPUT
    rPress  : REAL;
    xEnable : BOOL;
END_VAR
VAR_OUTPUT
    yLoAlarm : BOOL;
    yHiAlarm : BOOL;
    yPump    : BOOL;
END_VAR
    yLoAlarm := rPress < 35;
    yHiAlarm := rPress > 75;
    yPump    := xEnable AND NOT yHiAlarm;
END_FUNCTION_BLOCK
