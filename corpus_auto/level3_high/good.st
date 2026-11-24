FUNCTION_BLOCK FB_Level3
VAR_INPUT
    rLevel : REAL;
END_VAR
VAR_OUTPUT
    yFill  : BOOL;
    yHold  : BOOL;
    yDrain : BOOL;
END_VAR
    IF rLevel < 30 THEN
        yFill  := TRUE;
        yHold  := FALSE;
        yDrain := FALSE;
    ELSIF rLevel > 60 THEN
        yFill  := FALSE;
        yHold  := FALSE;
        yDrain := TRUE;
    ELSE
        yFill  := FALSE;
        yHold  := TRUE;
        yDrain := FALSE;
    END_IF;
END_FUNCTION_BLOCK
