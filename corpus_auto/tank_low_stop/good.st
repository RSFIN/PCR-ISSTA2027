FUNCTION_BLOCK FB_Tank
VAR_INPUT
    iLevel : INT;
    xReset : BOOL;
END_VAR
VAR_OUTPUT
    yPump  : BOOL;
    yAlarm : BOOL;
END_VAR
    IF iLevel <= 20 THEN
        yPump  := FALSE;
        yAlarm := TRUE;
    ELSIF iLevel >= 90 THEN
        yPump  := FALSE;
        yAlarm := FALSE;
    ELSE
        yPump  := TRUE;
        yAlarm := FALSE;
    END_IF;
END_FUNCTION_BLOCK
