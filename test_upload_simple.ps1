# Simple PowerShell test for upload endpoint

$uri = "http://localhost:8000/api/v1/rag/upload-document"

# Create simple test file
$testContent = @"
Test Law Document

Article 1: This is a test document.
Article 2: The system should work without loading models.
Article 3: This is a test for NO-ML mode.
"@

$testFile = "test_simple.txt"
$testContent | Out-File -FilePath $testFile -Encoding UTF8

try {
    Write-Host "Testing upload endpoint..." -ForegroundColor Yellow
    
    # Use Invoke-RestMethod for simpler handling
    $form = @{
        file = Get-Item $testFile
        law_name = "Test Law"
        law_type = "law"
        jurisdiction = "Saudi Arabia"
        description = "Test for NO-ML mode"
    }
    
    $startTime = Get-Date
    
    try {
        $response = Invoke-RestMethod -Uri $uri -Method POST -Form $form -TimeoutSec 30
        
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        
        Write-Host "Response time: $([math]::Round($duration, 2)) seconds" -ForegroundColor Green
        Write-Host "Response:" -ForegroundColor Cyan
        $response | ConvertTo-Json -Depth 3 | Write-Host
        
        if ($response.success) {
            Write-Host "SUCCESS - Upload working!" -ForegroundColor Green
            Write-Host "Chunks created: $($response.data.chunks_created)" -ForegroundColor Green
        } else {
            Write-Host "FAILED - $($response.message)" -ForegroundColor Red
        }
        
    } catch {
        Write-Host "Request failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
} finally {
    if (Test-Path $testFile) {
        Remove-Item $testFile
        Write-Host "Cleaned up test file" -ForegroundColor Yellow
    }
}

