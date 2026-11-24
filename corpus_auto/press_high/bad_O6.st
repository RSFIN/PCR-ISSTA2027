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
    yLoAlarm := rPress < 25;
    yPump := xEnable AND NOT yLoAlarm AND NOT yHiAlarm;
    yHiAlarm := rPress > 65;
END_FUNCTION_BLOCK
