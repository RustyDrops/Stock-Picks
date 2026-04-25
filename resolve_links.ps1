param(
    [Parameter(Mandatory=$true)]
    [string[]]$Urls
)

foreach ($Url in $Urls) {
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Head -MaximumRedirection 10 -ErrorAction Stop
        $finalUrl = $response.BaseResponse.ResponseUri.AbsoluteUri
        Write-Output "[$Url] -> $finalUrl"
    } catch {
        Write-Error "Failed to resolve $Url : $($_.Exception.Message)"
    }
}
