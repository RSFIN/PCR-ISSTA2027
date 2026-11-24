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
    yPumpA     := xAuto AND NOT xFault;
    yPumpB     := xAuto;
    ySwapAlarm := xFault AND NOT xManual;
    yLamp      := xAuto;
END_FUNCTION_BLOCK
