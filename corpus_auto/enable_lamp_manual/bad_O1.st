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
    yHeat := xStart AND NOT xManual;
    yFan  := (xStart) AND NOT xStart;
    yLamp := xStart AND NOT xAuto;
END_FUNCTION_BLOCK
