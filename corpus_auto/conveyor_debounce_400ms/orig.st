FUNCTION_BLOCK FB_ConveyorStartConfirm
VAR_INPUT
    xStart : BOOL;
END_VAR
VAR_OUTPUT
    yReady : BOOL;
END_VAR
VAR
    tonConfirm : TON;
END_VAR
    tonConfirm(IN := xStart, PT := T#200MS);
    yReady := tonConfirm.Q;
END_FUNCTION_BLOCK
