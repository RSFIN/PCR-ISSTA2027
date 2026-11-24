FUNCTION_BLOCK FB_Tank
VAR_INPUT
    iLevel : INT;
    xReset : BOOL;
END_VAR
VAR_OUTPUT
    yPump  : BOOL;
    yAlarm : BOOL;
END_VAR
    yPump  := TRUE;
    yAlarm := FALSE;
    IF iLevel <= 10 THEN
        yPump  := FALSE;
        yAlarm := TRUE;
    END_IF;
    IF iLevel >= 85 THEN
        yPump  := FALSE;
        yAlarm := FALSE;
    END_IF;
END_FUNCTION_BLOCK
