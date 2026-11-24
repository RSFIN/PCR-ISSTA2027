FUNCTION_BLOCK FB_FlowAlarm
VAR_INPUT
    rFlow   : REAL;
    xPumpOn : BOOL;
END_VAR
VAR_OUTPUT
    yLowFlow : BOOL;
    yTrip    : BOOL;
END_VAR
    yLowFlow := rFlow < 50;
    IF xPumpOn AND yLowFlow THEN
        yTrip := TRUE;
    ELSE
        yTrip := FALSE;
    END_IF;
END_FUNCTION_BLOCK
