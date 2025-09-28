# Manual Deployment Guide for Hostinger Server

## Step-by-Step Instructions

### 1. Upload Your Code to Hostinger
```bash
# Option A: Using Git (if you have git access)
git clone https://github.com/lawyeralthomali/legatoo_backend.git
cd legatoo_backend

# Option B: Upload files via File Manager or FTP
# Upload all project files to your Hostinger directory
```

### 2. Set Up Environment Variables
```bash
# Copy the template file
cp supabase.env.template supabase.env

# Edit the supabase.env file with your actual values:
# SUPABASE_URL=your_supabase_url
# SUPABASE_ANON_KEY=your_supabase_anon_key
# SUPABASE_JWT_SECRET=your_supabase_jwt_secret
# DATABASE_URL=your_database_url
```

### 3. Run the Deployment Script
```bash
# Make sure you're in the project directory
cd /path/to/your/legatoo_backend

# Run the deployment script
./deploy_manual.sh
```

### 4. Verify Deployment
```bash
# Check if the app is running
curl http://localhost:8000/health

# Check logs
tail -f logs/app.log

# Check running processes
ps aux | grep uvicorn
```

### 5. Configure Hostinger (if needed)
- **Port Configuration**: Make sure port 8000 is open
- **Domain Setup**: Configure your domain to point to the server
- **SSL Certificate**: Set up SSL if needed

## Troubleshooting

### If Python is not found:
```bash
# Check available Python versions
which python3
which python3.8
which python3.9

# Install Python if needed (contact Hostinger support)
```

### If packages fail to install:
```bash
# Try installing without --user flag
python3 -m pip install -r requirements.txt

# Or try with specific Python version
python3.8 -m pip install -r requirements.txt
```

### If the app doesn't start:
```bash
# Check logs for errors
cat logs/app.log

# Try running manually to see errors
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Management Commands

### Stop the application:
```bash
kill $(cat app.pid)
```

### Restart the application:
```bash
./deploy_manual.sh
```

### View logs:
```bash
tail -f logs/app.log
```

### Check status:
```bash
ps aux | grep uvicorn
curl http://localhost:8000/health
```

## Important Notes

1. **Environment Variables**: Make sure all required environment variables are set in `supabase.env`
2. **Port Access**: Ensure port 8000 is accessible from outside
3. **File Permissions**: Make sure the script has execute permissions
4. **Python Version**: The script will automatically detect the best available Python version
5. **Dependencies**: All required packages will be installed automatically

## Support

If you encounter issues:
1. Check the logs: `tail -f logs/app.log`
2. Verify environment variables are set correctly
3. Ensure all files are uploaded properly
4. Contact Hostinger support if Python/dependencies are missing
