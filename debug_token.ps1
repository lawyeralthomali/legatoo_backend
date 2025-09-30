# Simple Token Test - Debug Version
Write-Host "Debug Token Test" -ForegroundColor Cyan

# Login
$loginResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/auth/login" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"email": "info@legatoo.westlinktowing.com", "password": "Zaq1zaq1"}'
$loginData = $loginResponse.Content | ConvertFrom-Json
$accessToken = $loginData.data.access_token

Write-Host "Login successful!" -ForegroundColor Green
Write-Host "Token expires in: $($loginData.data.expires_in) seconds" -ForegroundColor Green
Write-Host "Full token: $accessToken" -ForegroundColor Gray

# Test different endpoints
Write-Host "`nTesting different endpoints..." -ForegroundColor Yellow

# Test 1: Root endpoint (no auth required)
try {
    $rootResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8000/" -Method GET
    Write-Host "Root endpoint: Status $($rootResponse.StatusCode) - Works" -ForegroundColor Green
} catch {
    Write-Host "Root endpoint: Error - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Health endpoint (no auth required)
try {
    $healthResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -Method GET
    Write-Host "Health endpoint: Status $($healthResponse.StatusCode) - Works" -ForegroundColor Green
} catch {
    Write-Host "Health endpoint: Error - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Profile endpoint (auth required)
try {
    $profileResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/profiles/me" -Method GET -Headers @{"Authorization"="Bearer $accessToken"}
    Write-Host "Profile endpoint: Status $($profileResponse.StatusCode) - Works" -ForegroundColor Green
    $profileData = $profileResponse.Content | ConvertFrom-Json
    Write-Host "Profile data: $($profileData.data.email)" -ForegroundColor Green
} catch {
    Write-Host "Profile endpoint: Status $($_.Exception.Response.StatusCode) - Failed" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Users endpoint (auth required)
try {
    $usersResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/users/" -Method GET -Headers @{"Authorization"="Bearer $accessToken"}
    Write-Host "Users endpoint: Status $($usersResponse.StatusCode) - Works" -ForegroundColor Green
} catch {
    Write-Host "Users endpoint: Status $($_.Exception.Response.StatusCode) - Failed" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nDebug test completed!" -ForegroundColor Cyan
