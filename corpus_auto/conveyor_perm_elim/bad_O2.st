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
END_VAR
    tonDb(IN := xStart, PT := T#200MS);
    yRun   := tonDb.Q AND NOT xEStop AND NOT xOverload;
    yFault := xOverload OR xEStop;
END_FUNCTION_BLOCK
