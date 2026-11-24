FUNCTION_BLOCK FB_Silo
VAR_INPUT
    rSilo : REAL;
END_VAR
VAR_OUTPUT
    yInlet  : BOOL;
    yOutlet : BOOL;
    yFull   : BOOL;
END_VAR
    IF rSilo < 15 THEN
        yInlet  := TRUE;
        yOutlet := FALSE;
        yFull   := FALSE;
    ELSIF rSilo > 85 THEN
        yInlet  := FALSE;
        yOutlet := TRUE;
    ELSE
        yOutlet := FALSE;
    END_IF;
END_FUNCTION_BLOCK
