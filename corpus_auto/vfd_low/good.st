FUNCTION_BLOCK FB_VfdLimit
VAR_INPUT
    rFreq : REAL;
    xRun  : BOOL;
END_VAR
VAR_OUTPUT
    yClamp : BOOL;
    yMotor : BOOL;
END_VAR
    IF rFreq < 30 THEN
        yClamp := TRUE;
    ELSIF rFreq > 50 THEN
        yClamp := TRUE;
    ELSE
        yClamp := FALSE;
    END_IF;
    IF xRun AND NOT yClamp THEN
        yMotor := TRUE;
    END_IF;
    IF yClamp THEN
        yMotor := FALSE;
    END_IF;
END_FUNCTION_BLOCK
