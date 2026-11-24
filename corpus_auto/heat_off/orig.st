FUNCTION_BLOCK FB_HeatBand
VAR_INPUT
    rTemp : REAL;
END_VAR
VAR_OUTPUT
    yHeat  : BOOL;
    yAlarm : BOOL;
END_VAR
    IF rTemp < 45 THEN
        yHeat  := TRUE;
        yAlarm := FALSE;
    ELSIF rTemp > 60 THEN
        yHeat  := FALSE;
        yAlarm := TRUE;
    ELSE
        yHeat  := FALSE;
        yAlarm := FALSE;
    END_IF;
END_FUNCTION_BLOCK
