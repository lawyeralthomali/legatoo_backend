@echo off
echo ================================================
echo Starting Supabase Auth FastAPI Server
echo ================================================

REM Set environment variables
set SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im90aWl2ZWxmbHZpZGd5ZnNobWpuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE4NTQ2MDksImV4cCI6MjA2NzQzMDYwOX0.aoJZdCUfLngPLO0uDoYHp3GdiQpZlf5PlEZlr2BIr1h9c
set SUPABASE_URL=https://otiivelflvidgyfshmjn.supabase.co
set SUPABASE_JWT_SECRET=fHvCDR3sCJKCNYI0qsp34AolLlsolf5Zvow3NkQfZov/SZcP/5pUNBWExbLLbIfDCemnBZiMUTjv4vxurt/xCA==

REM Start the server
python start_server.py

pause
