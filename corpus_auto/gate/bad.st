FUNCTION_BLOCK FB_Gate
VAR_INPUT
    xPart : BOOL;
END_VAR
VAR_OUTPUT
    yGate : BOOL;
END_VAR
VAR
    rtPart  : R_TRIG;
    tonHold : TON;
END_VAR
    rtPart(CLK := xPart);
    IF rtPart.Q THEN
        yGate := TRUE;
    END_IF;
    tonHold(IN := yGate, PT := T#820MS);
    IF tonHold.Q THEN
        yGate := FALSE;
    END_IF;
END_FUNCTION_BLOCK
