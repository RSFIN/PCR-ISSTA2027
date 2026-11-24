FUNCTION_BLOCK FB_PulseStretch
VAR_INPUT
    xTrig  : BOOL;
    xInh   : BOOL;
END_VAR
VAR_OUTPUT
    yPulse : BOOL;
    yBusy  : BOOL;
    yFault : BOOL;
END_VAR
VAR
    rtTrig   : R_TRIG;
    tonPulse : TON;
END_VAR
    rtTrig(CLK := xTrig);
    IF rtTrig.Q THEN
        yPulse := TRUE;
    END_IF;
    tonPulse(IN := yPulse, PT := T#600MS);
    IF tonPulse.Q THEN
        yPulse := FALSE;
    END_IF;
    yBusy  := yPulse;
    yFault := xInh AND NOT yPulse;
END_FUNCTION_BLOCK
