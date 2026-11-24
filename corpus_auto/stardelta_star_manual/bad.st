FUNCTION_BLOCK FB_StarDelta
VAR_INPUT
    xStart    : BOOL;
    xStop     : BOOL;
    xOverload : BOOL;
    xReady    : BOOL;
    xManual   : BOOL;
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
    yMain := (xStart AND NOT xStop AND NOT xOverload AND NOT xReady) AND NOT xStart;
    tonTrans(IN := yMain, PT := T#5S);
    yStar  := yMain AND NOT tonTrans.Q;
    yDelta := yMain AND tonTrans.Q;
    yFault := xOverload;
END_FUNCTION_BLOCK
