# PowerShell test script for the upload endpoint

$uri = "http://localhost:8000/api/v1/rag/upload-document"

# Create test file content
$testContent = @"
نظام اختبار

المادة 1: هذا نص اختبار قصير.
المادة 2: يجب أن يعمل النظام دون تحميل أي نماذج.
المادة 3: هذا اختبار للوضع بدون تعلم آلة.
"@

# Create temporary test file
$testFile = "test_upload.txt"
$testContent | Out-File -FilePath $testFile -Encoding UTF8

try {
    Write-Host "🧪 Testing upload-document endpoint..." -ForegroundColor Yellow
    Write-Host "📤 Uploading test file..." -ForegroundColor Cyan
    
    # Prepare form data
    $boundary = [System.Guid]::NewGuid().ToString()
    $LF = "`r`n"
    
    # File content
    $fileBytes = [System.IO.File]::ReadAllBytes($testFile)
    $fileContent = [System.Text.Encoding]::UTF8.GetString($fileBytes)
    
    # Build multipart form data
    $bodyLines = @(
        "--$boundary",
        "Content-Disposition: form-data; name=`"file`"; filename=`"test_upload.txt`"",
        "Content-Type: text/plain",
        "",
        $fileContent,
        "--$boundary",
        "Content-Disposition: form-data; name=`"law_name`"",
        "",
        "اختبار بدون تعلم آلة",
        "--$boundary",
        "Content-Disposition: form-data; name=`"law_type`"",
        "",
        "law",
        "--$boundary",
        "Content-Disposition: form-data; name=`"jurisdiction`"",
        "",
        "السعودية",
        "--$boundary",
        "Content-Disposition: form-data; name=`"description`"",
        "",
        "اختبار الوضع بدون ML",
        "--$boundary--"
    )
    
    $body = $bodyLines -join $LF
    $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)
    
    # Make request
    $headers = @{
        "Content-Type" = "multipart/form-data; boundary=$boundary"
    }
    
    $startTime = Get-Date
    
    try {
        $response = Invoke-WebRequest -Uri $uri -Method POST -Body $bodyBytes -Headers $headers -TimeoutSec 30
        
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        
        Write-Host "⏱️  Response time: $([math]::Round($duration, 2)) seconds" -ForegroundColor Green
        Write-Host "📊 Status: $($response.StatusCode)" -ForegroundColor Green
        
        $result = $response.Content | ConvertFrom-Json
        Write-Host "📝 Response:" -ForegroundColor Cyan
        $result | ConvertTo-Json -Depth 3 | Write-Host
        
        if ($response.StatusCode -eq 200 -and $result.success) {
            Write-Host "✅ Test PASSED - Upload working!" -ForegroundColor Green
            Write-Host "   - Chunks created: $($result.data.chunks_created)" -ForegroundColor Green
            Write-Host "   - Processing time: $($result.data.processing_time)s" -ForegroundColor Green
            exit 0
        } else {
            Write-Host "❌ Test FAILED" -ForegroundColor Red
            Write-Host "   Error: $($result.message)" -ForegroundColor Red
            exit 1
        }
        
    } catch {
        Write-Host "❌ Request failed: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
    
} finally {
    # Clean up test file
    if (Test-Path $testFile) {
        Remove-Item $testFile
        Write-Host "🧹 Cleaned up test file" -ForegroundColor Yellow
    }
}

