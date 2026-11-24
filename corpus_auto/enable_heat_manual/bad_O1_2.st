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
    yHeat := xStart;
    yFan  := (xStart) AND NOT xAuto;
    yLamp := xStart AND NOT xManual AND NOT xAuto;
END_FUNCTION_BLOCK
