FUNCTION_BLOCK FB_StarDelta
VAR_INPUT
    xStart    : BOOL;
    xStop     : BOOL;
    xOverload : BOOL;
END_VAR
VAR_OUTPUT
    yMain  : BOOL;
    yStar  : BOOL;
    yDelta : BOOL;
    yFault : BOOL;
END_VAR
VAR
    tonTrans : TON;
END_VAR
    yMain := xStart AND NOT xOverload;
    tonTrans(IN := yMain, PT := T#5S);
    IF tonTrans.Q THEN
        yStar  := FALSE;
        yDelta := yMain;
    ELSE
        yStar  := yMain;
        yDelta := FALSE;
    END_IF;
    yFault := xOverload;
END_FUNCTION_BLOCK
