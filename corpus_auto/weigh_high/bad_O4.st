FUNCTION_BLOCK FB_WeighSort
VAR_INPUT
    iWeight : INT;
    xFeed   : BOOL;
END_VAR
VAR_OUTPUT
    ySort   : BOOL;
    yReject : BOOL;
    yReady  : BOOL;
END_VAR
    yReady := xFeed;
    IF iWeight < 25 THEN
        ySort   := FALSE;
        yReject := TRUE;
    ELSIF iWeight > 50 THEN
        ySort   := FALSE;
        yReject := TRUE;
    ELSE
        ySort   := TRUE;
        yReject := FALSE;
    END_IF;
END_FUNCTION_BLOCK
