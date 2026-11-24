FUNCTION_BLOCK FB_Indexer
VAR_INPUT
    xPart : BOOL;
END_VAR
VAR_OUTPUT
    yIndex : BOOL;
    yReady : BOOL;
END_VAR
VAR
    rtPart  : R_TRIG;
    tonReady : TON;
END_VAR
    rtPart(CLK := xPart);
    IF rtPart.Q THEN
        yIndex := NOT yIndex;
    END_IF;
    tonReady(IN := yIndex, PT := T#2520MS);
    yReady := tonReady.Q;
END_FUNCTION_BLOCK
