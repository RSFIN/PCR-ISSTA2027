FUNCTION_BLOCK FB_RedundantVote
VAR_INPUT
    xS1 : BOOL;
    xS2 : BOOL;
    xS3 : BOOL;
END_VAR
VAR_OUTPUT
    yVote : BOOL;
    yDisagree : BOOL;
END_VAR
VAR
    tonDisagree : TON;
END_VAR
(* 正文逐字取自 OSCAT Basic SEL2_OF_3B：三取二表决 + 不一致去抖 *)
yVote := (xS1 AND xS2) OR (xS1 AND xS3) OR (xS2 AND xS3);
tonDisagree(IN := (xS1 XOR xS2) OR (xS1 XOR xS3) OR (xS2 XOR xS3), PT := T#1020MS);
yDisagree := tonDisagree.Q;
END_FUNCTION_BLOCK
