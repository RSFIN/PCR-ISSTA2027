FUNCTION_BLOCK FB_ConcAlarm
VAR_INPUT
    rConc    : REAL;
    xPurgeEn : BOOL;
END_VAR
VAR_OUTPUT
    yAlarm1 : BOOL;
    yAlarm2 : BOOL;
    yPurge  : BOOL;
END_VAR
    yAlarm1 := rConc > 30;
    yAlarm2 := rConc > 70;
    yPurge  := yAlarm2 AND xPurgeEn;
END_FUNCTION_BLOCK
