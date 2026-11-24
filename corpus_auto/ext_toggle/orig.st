FUNCTION_BLOCK FB_ToggleGuard
VAR_INPUT
    CLK : BOOL;
    RST : BOOL;
    xEn : BOOL;
END_VAR
VAR_OUTPUT
    Q : BOOL;
END_VAR
VAR
    edge : BOOL;
END_VAR
(* 正文逐字取自 OSCAT Basic TOGGLE：翻转 + 复位，大小写按声明统一。
   xEn 在本版声明但未使用——联锁是下一张变更单要加的。 *)
IF RST THEN
    Q := FALSE;
ELSIF CLK AND NOT edge THEN
    Q := NOT Q;
END_IF;
edge := CLK;
END_FUNCTION_BLOCK
