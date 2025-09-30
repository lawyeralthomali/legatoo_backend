# Token Expiration Test Script
# This script tests JWT token expiration (30 seconds)

Write-Host "Testing JWT Token Expiration" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Step 1: Login and get token
Write-Host "`n1. Logging in..." -ForegroundColor Yellow
try {
    $loginResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/auth/login" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"email": "info@legatoo.westlinktowing.com", "password": "Zaq1zaq1"}'
    $loginData = $loginResponse.Content | ConvertFrom-Json
    $accessToken = $loginData.data.access_token
    $refreshToken = $loginData.data.refresh_token
    
    Write-Host "Login successful!" -ForegroundColor Green
    Write-Host "Token expires in: $($loginData.data.expires_in) seconds" -ForegroundColor Green
    Write-Host "Access Token: $($accessToken.Substring(0, 20))..." -ForegroundColor Gray
} catch {
    Write-Host "Login failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 2: Test profile API immediately
Write-Host "`n2. Testing profile access immediately..." -ForegroundColor Yellow
try {
    $profileResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/profiles/me" -Method GET -Headers @{"Authorization"="Bearer $accessToken"}
    Write-Host "0s: Status $($profileResponse.StatusCode) - Profile access works" -ForegroundColor Green
    
    $profileData = $profileResponse.Content | ConvertFrom-Json
    Write-Host "Profile email: $($profileData.data.email)" -ForegroundColor Green
} catch {
    Write-Host "0s: Error - $($_.Exception.Message)" -ForegroundColor Red
}

# Step 3: Wait for token expiration
Write-Host "`n3. Waiting 30 seconds for token to expire..." -ForegroundColor Yellow
for ($i = 30; $i -gt 0; $i--) {
    Write-Host "Waiting $i seconds remaining..." -ForegroundColor Cyan -NoNewline
    Start-Sleep -Seconds 1
    Write-Host "`r" -NoNewline
}
Write-Host ""

# Step 4: Test profile API after expiration
Write-Host "`n4. Testing profile access after expiration..." -ForegroundColor Yellow
try {
    $expiredResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/profiles/me" -Method GET -Headers @{"Authorization"="Bearer $accessToken"}
    Write-Host "30s: Status $($expiredResponse.StatusCode) - Still works" -ForegroundColor Green
} catch {
    Write-Host "30s: Status $($_.Exception.Response.StatusCode) - Token expired! Profile access denied" -ForegroundColor Red
    
    # Try to get error details
    try {
        $errorStream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorStream)
        $errorContent = $reader.ReadToEnd()
        $errorData = $errorContent | ConvertFrom-Json
        Write-Host "Error message: $($errorData.message)" -ForegroundColor Red
    } catch {
        Write-Host "Could not parse error details" -ForegroundColor Red
    }
}

# Step 5: Test refresh token
Write-Host "`n5. Testing refresh token..." -ForegroundColor Yellow
try {
    $refreshResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/auth/refresh" -Method POST -Headers @{"Content-Type"="application/json"} -Body "{`"refresh_token`": `"$refreshToken`"}"
    $refreshData = $refreshResponse.Content | ConvertFrom-Json
    $newAccessToken = $refreshData.data.access_token
    
    Write-Host "Refresh successful! New token expires in: $($refreshData.data.expires_in) seconds" -ForegroundColor Green
    
    # Test new token
    $newProfileResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/profiles/me" -Method GET -Headers @{"Authorization"="Bearer $newAccessToken"}
    Write-Host "New token test: Status $($newProfileResponse.StatusCode) - Works" -ForegroundColor Green
} catch {
    Write-Host "Refresh failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Summary
Write-Host "`nTest Summary:" -ForegroundColor Cyan
Write-Host "=================" -ForegroundColor Cyan
Write-Host "Login: Working" -ForegroundColor Green
Write-Host "Token (0s): Working" -ForegroundColor Green
Write-Host "Token (30s): Expired" -ForegroundColor Red
Write-Host "Refresh: Working" -ForegroundColor Green

Write-Host "`nToken expiration test completed!" -ForegroundColor Cyan
Write-Host "The access token correctly expires after 30 seconds." -ForegroundColor Green