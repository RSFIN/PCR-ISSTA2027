FUNCTION_BLOCK FB_BothEdgePulse
VAR_INPUT
    xClk : BOOL;
END_VAR
VAR_OUTPUT
    yPulse : BOOL;
END_VAR
VAR
    edge : BOOL;
END_VAR
(* 正文逐字取自 OSCAT Basic B_TRIG：双边沿脉冲 *)
yPulse := xClk XOR edge;
edge := xClk;
END_FUNCTION_BLOCK
