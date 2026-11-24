FUNCTION_BLOCK FB_Seq
VAR_INPUT
    xIn : BOOL;
END_VAR
VAR_OUTPUT
    ySeq : BOOL;
END_VAR
VAR
    r1 : BOOL;
    r2 : BOOL;
END_VAR
    r2 := r1;
    r1 := xIn;
    ySeq := r1 AND NOT r2;
END_FUNCTION_BLOCK
