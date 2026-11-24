FUNCTION_BLOCK FB_Compressor
VAR_INPUT
    xAuto      : BOOL;
    xManual    : BOOL;
    xOil       : BOOL;
    xPress     : BOOL;
END_VAR
VAR_OUTPUT
    yLoad      : BOOL;
    yBlow      : BOOL;
    yUnload    : BOOL;
    yAlarm     : BOOL;
END_VAR
    yLoad := xAuto AND xPress AND xOil;
    yBlow := xAuto AND xPress AND xOil AND NOT xManual;
    yUnload := (xAuto AND xPress AND xOil) OR (NOT xOil AND xManual);
    yAlarm := NOT xOil;
END_FUNCTION_BLOCK
