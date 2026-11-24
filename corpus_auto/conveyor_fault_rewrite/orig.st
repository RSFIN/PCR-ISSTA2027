FUNCTION_BLOCK FB_Conveyor
VAR_INPUT
    xStart    : BOOL;
    xStop     : BOOL;
    xEStop    : BOOL;
    xOverload : BOOL;
END_VAR
VAR_OUTPUT
    yRun   : BOOL;
    yFault : BOOL;
END_VAR
VAR
    tonDb : TON;
    xPerm : BOOL;
END_VAR
    tonDb(IN := xStart AND NOT xStop, PT := T#200MS);
    xPerm := tonDb.Q AND NOT xEStop AND NOT xOverload;
    yRun  := xPerm;
    yFault := xOverload OR xEStop;
END_FUNCTION_BLOCK
