FUNCTION_BLOCK FB_Gate
VAR_INPUT
    xPart : BOOL;
END_VAR
VAR_OUTPUT
    yGate : BOOL;
END_VAR
VAR
    xPrev   : BOOL;
    tonHold : TON;
END_VAR
    IF xPart AND NOT xPrev THEN
        yGate := TRUE;
    END_IF;
    xPrev := xPart;
    tonHold(IN := yGate, PT := T#520MS);
    IF tonHold.Q THEN
        yGate := FALSE;
    END_IF;
END_FUNCTION_BLOCK
