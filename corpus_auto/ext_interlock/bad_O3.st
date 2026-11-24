FUNCTION_BLOCK FB_DualInterlock
VAR_INPUT
    xIn1 : BOOL;
    xIn2 : BOOL;
END_VAR
VAR_OUTPUT
    yOut1 : BOOL;
    yOut2 : BOOL;
END_VAR
VAR
    tof1 : TOF;
    tof2 : TOF;
END_VAR
(* 正文逐字取自 OSCAT Basic INTERLOCK：两路互锁 + 死区 TOF *)
tof1(IN := xIn1, PT := T#1020MS);
tof2(IN := xIn2, PT := T#1S);
yOut1 := xIn1 AND NOT tof2.Q;
yOut2 := xIn2 AND NOT tof1.Q;
END_FUNCTION_BLOCK
