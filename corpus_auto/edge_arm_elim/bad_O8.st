FUNCTION_BLOCK FB_Edge
VAR_INPUT
    xA : BOOL;
    xB : BOOL;
END_VAR
VAR_OUTPUT
    yCmd : BOOL;
END_VAR
VAR
    tonArm : TON;
END_VAR
    tonArm(IN := xA, PT := T#30MS);
    yCmd := tonArm.Q;
END_FUNCTION_BLOCK
