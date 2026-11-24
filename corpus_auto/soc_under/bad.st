FUNCTION_BLOCK FB_SocGuard
VAR_INPUT
    rSoc : REAL;
END_VAR
VAR_OUTPUT
    yCharge    : BOOL;
    yDischarge : BOOL;
    yWarn      : BOOL;
END_VAR
    IF rSoc < 15 THEN
        yCharge    := TRUE;
        yDischarge := FALSE;
        yWarn      := TRUE;
    ELSIF rSoc > 75 THEN
        yCharge    := FALSE;
        yDischarge := FALSE;
        yWarn      := TRUE;
    ELSE
        yCharge    := FALSE;
        yDischarge := TRUE;
        yWarn      := FALSE;
    END_IF;
END_FUNCTION_BLOCK
