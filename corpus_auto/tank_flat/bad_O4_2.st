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
    IF iLevel <= 5 THEN
        yPump  := FALSE;
        yAlarm := TRUE;
    END_IF;
    IF iLevel >= 90 THEN
        yPump  := FALSE;
        yAlarm := FALSE;
    END_IF;
END_FUNCTION_BLOCK
