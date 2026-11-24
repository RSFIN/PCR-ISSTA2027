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
    yReady := (xFeed) AND NOT xFeed;
    IF iWeight < 40 THEN
        ySort   := FALSE;
        yReject := TRUE;
    ELSIF iWeight > 60 THEN
        ySort   := FALSE;
        yReject := TRUE;
    ELSE
        ySort   := TRUE;
        yReject := FALSE;
    END_IF;
END_FUNCTION_BLOCK
