FUNCTION_BLOCK FB_StarDelta
VAR_INPUT
    xStart    : BOOL;
    xStop     : BOOL;
    xOverload : BOOL;
    xReady    : BOOL;
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
    yStar := yMain AND NOT tonTrans.Q;
    yMain := xStart AND NOT xStop AND NOT xOverload AND (NOT xReady OR xStart);
    yDelta := yMain AND tonTrans.Q;
    yFault := xOverload;
END_FUNCTION_BLOCK
