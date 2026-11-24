FUNCTION_BLOCK FB_HeatZone
VAR_INPUT
    xAuto   : BOOL;
    xManual : BOOL;
    iTemp   : INT;
END_VAR
VAR_OUTPUT
    yHeat1    : BOOL;
    yHeat2    : BOOL;
    yOverTemp : BOOL;
END_VAR
    yHeat1    := xAuto;
    yHeat2    := (xAuto) AND NOT xAuto;
    yOverTemp := iTemp >= 80 AND NOT xManual;
END_FUNCTION_BLOCK
