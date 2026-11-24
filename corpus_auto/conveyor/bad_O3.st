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
    tonDb      : TON;
    tonRestart : TON;
    xPerm      : BOOL;
END_VAR
    tonRestart(IN := NOT xEStop AND NOT xOverload, PT := T#2020MS);
    tonDb(IN := xStart AND NOT xStop, PT := T#200MS);
    xPerm := tonDb.Q AND tonRestart.Q;
    yRun  := xPerm;
    yFault := xOverload OR xEStop;
END_FUNCTION_BLOCK
