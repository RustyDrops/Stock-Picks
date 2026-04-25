param(
    [Parameter(Mandatory=$true)]
    [string]$CurrentDate,
    [Parameter(Mandatory=$true)]
    [PSCustomObject[]]$TradeData
)

# TradeData should be an array of objects with: 
# Ticker, Entry, SL, TP, ReportDate, High, Low, Current

$results = foreach ($trade in $TradeData) {
    $status = "ACTIVE"
    $currentPL = (($trade.Current - $trade.Entry) / $trade.Entry) * 100
    $notes = "Maintaining above support."
    $trailingSL = $trade.SL

    # 1. Check if previously Stopped Out (passed in from state if we had a DB, but here we check the Low)
    if ($trade.Low -le $trade.SL) {
        $status = "STOPPED OUT"
        $currentPL = (($trade.SL - $trade.Entry) / $trade.Entry) * 100
        $notes = "Hit Hard Stop at $($trade.SL)."
    }
    # 2. Check if Target was Hit
    elseif ($trade.High -ge $trade.TP) {
        $status = "TARGET HIT (TRAILING)"
        # Trailing Stop Logic: 5% below High, but at least at Entry (Break Even)
        $potentialTrailing = $trade.High * 0.95
        $trailingSL = [Math]::Max($trade.Entry, $potentialTrailing)
        
        # Check if currently below the new Trailing SL
        if ($trade.Current -le $trailingSL) {
            $status = "CLOSED (TRAILING SL)"
            $currentPL = (($trailingSL - $trade.Entry) / $trade.Entry) * 100
            $notes = "Trailing Stop hit at $trailingSL after reaching target."
        } else {
            $notes = "Target hit! Trailing Stop active at $trailingSL."
        }
    }

    [PSCustomObject]@{
        "Trade Date" = $trade.ReportDate
        Ticker      = $trade.Ticker
        Status      = $status
        "Current P/L" = "$([Math]::Round($currentPL, 2))%"
        "7D High/Low"= "$($trade.High) / $($trade.Low)"
        Notes       = $notes
    }
}

$results | ConvertTo-Json
