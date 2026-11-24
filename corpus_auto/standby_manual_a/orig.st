FUNCTION_BLOCK FB_PumpStandby
VAR_INPUT
    xAuto   : BOOL;
    xManual : BOOL;
    xFault  : BOOL;
END_VAR
VAR_OUTPUT
    yPumpA     : BOOL;
    yPumpB     : BOOL;
    ySwapAlarm : BOOL;
    yLamp      : BOOL;
END_VAR
    yPumpA     := xAuto AND NOT xFault AND NOT xManual;
    yPumpB     := xAuto AND xFault;
    ySwapAlarm := xFault AND NOT xManual;
    yLamp      := xAuto;
END_FUNCTION_BLOCK
