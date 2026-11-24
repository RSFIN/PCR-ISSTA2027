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
    xArm   : BOOL;
END_VAR
    tonArm(IN := xA, PT := T#40MS);
    xArm := tonArm.Q;
    yCmd := xArm;
END_FUNCTION_BLOCK
