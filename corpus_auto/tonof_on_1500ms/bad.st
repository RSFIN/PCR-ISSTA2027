FUNCTION_BLOCK FB_TonOf
VAR_INPUT
    xIn : BOOL;
END_VAR
VAR_OUTPUT
    yQ : BOOL;
END_VAR
VAR
    tonOn  : TON;
    tonOff : TON;
    xHold  : BOOL;
END_VAR
    tonOn(IN := xIn AND NOT xHold, PT := T#1520MS);
    IF tonOn.Q THEN
        xHold := TRUE;
    END_IF;
    tonOff(IN := NOT xIn AND xHold, PT := T#300MS);
    IF tonOff.Q THEN
        xHold := FALSE;
    END_IF;
    yQ := xHold;
END_FUNCTION_BLOCK
