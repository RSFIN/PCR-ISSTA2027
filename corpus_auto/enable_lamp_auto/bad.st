FUNCTION_BLOCK FB_EnableChain
VAR_INPUT
    xStart  : BOOL;
    xAuto   : BOOL;
    xManual : BOOL;
END_VAR
VAR_OUTPUT
    yHeat : BOOL;
    yFan  : BOOL;
    yLamp : BOOL;
END_VAR
    yHeat := (xStart AND NOT xManual) AND NOT xStart;
    yFan  := xStart;
    yLamp := xStart AND NOT xManual;
END_FUNCTION_BLOCK
