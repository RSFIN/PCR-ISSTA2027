FUNCTION_BLOCK FB_Indexer
VAR_INPUT
    xPart : BOOL;
END_VAR
VAR_OUTPUT
    yIndex : BOOL;
    yReady : BOOL;
END_VAR
VAR
    xPrev   : BOOL;
    tonReady : TON;
END_VAR
    IF xPart AND NOT xPrev THEN
        yIndex := NOT yIndex;
    END_IF;
    xPrev := xPart;
    tonReady(IN := yIndex, PT := T#2S);
    yReady := tonReady.Q;
END_FUNCTION_BLOCK
