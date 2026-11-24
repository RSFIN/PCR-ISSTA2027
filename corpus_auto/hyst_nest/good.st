FUNCTION_BLOCK FB_Hyst
VAR_INPUT
    rIn : REAL;
END_VAR
VAR_OUTPUT
    yQ   : BOOL;
    yWin : BOOL;
END_VAR
    IF rIn < 20 THEN
        yQ   := FALSE;
        yWin := FALSE;
    ELSE
        IF rIn > 80 THEN
            yQ   := TRUE;
            yWin := FALSE;
        ELSE
            yWin := TRUE;
        END_IF;
    END_IF;
END_FUNCTION_BLOCK
