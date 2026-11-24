FUNCTION_BLOCK FB_FanPurge
VAR_INPUT
    xFan : BOOL;
END_VAR
VAR_OUTPUT
    yFan : BOOL;
    yDamper : BOOL;
END_VAR
VAR
    tofPurge : TOF;
END_VAR
    yFan := xFan;
    tofPurge(IN := xFan, PT := T#5S);
    yDamper := tofPurge.Q;
END_FUNCTION_BLOCK
