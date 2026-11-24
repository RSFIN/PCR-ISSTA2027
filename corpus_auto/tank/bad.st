FUNCTION_BLOCK FB_Tank
VAR_INPUT
    iLevel : INT;
    xReset : BOOL;
END_VAR
VAR_OUTPUT
    yPump  : BOOL;
    yAlarm : BOOL;
END_VAR
    IF iLevel <= 15 THEN
        yPump  := FALSE;
        yAlarm := TRUE;
    ELSIF iLevel >= 85 THEN
        yPump  := FALSE;
        yAlarm := FALSE;
    ELSE
        yPump  := TRUE;
        yAlarm := FALSE;
    END_IF;
END_FUNCTION_BLOCK
