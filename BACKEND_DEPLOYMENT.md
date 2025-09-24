# Legatoo Backend Deployment Guide

This guide will help you deploy the Legatoo backend to Hostinger server.

## Prerequisites

1. **Hostinger VPS/Cloud Hosting** with SSH access
2. **Docker** and **Docker Compose** installed on the server
3. **Git** installed on the server
4. **Domain name** pointing to your server (optional but recommended)

## Server Setup

### 1. Install Docker and Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again to apply docker group changes
```

### 2. Clone the Repository

```bash
# Navigate to home directory
cd /home/$USER

# Clone your repository
git clone git@github.com:lawyeralthomali/lagatoo-app.git
cd legatoo-app/legatoo_backend
```

## Environment Configuration

### 1. Create Production Environment File

```bash
# Copy the example environment file
cp env.production.example .env.production

# Edit the environment file
nano .env.production
```

### 2. Update Environment Variables

Update the following variables in `.env.production`:

```env
# Supabase Configuration (keep your existing values)
SUPABASE_URL=https://otiivelflvidgyfshmjn.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# Database Configuration (keep your existing values)
DATABASE_URL=postgresql+asyncpg://postgres.otiivelflvidgyfshmjn:uWytSFyq-6cgJ%2AX@aws-0-eu-north-1.pooler.supabase.com:5432/postgres

# Security (CHANGE THESE!)
SECRET_KEY=your-super-secret-production-key
SUPABASE_JWT_SECRET=your-supabase-jwt-secret

# Environment
ENVIRONMENT=production

# CORS Origins (add your frontend domain)
CORS_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com
```

## Deployment Methods

### Method 1: Manual Deployment

1. **Run the deployment script:**
```bash
chmod +x deploy.sh
./deploy.sh
```

2. **Or manually:**
```bash
# Stop existing containers
docker-compose down

# Build and start
docker-compose up -d --build

# Check status
docker-compose ps
docker-compose logs backend
```

### Method 2: GitHub Actions (Recommended)

1. **Set up GitHub Secrets:**
   - Go to your GitHub repository
   - Navigate to Settings > Secrets and variables > Actions
   - Add the following secrets:
     - `HOSTINGER_HOST`: Your server IP address
     - `HOSTINGER_USERNAME`: Your server username
     - `HOSTINGER_SSH_KEY`: Your private SSH key
     - `HOSTINGER_PORT`: SSH port (usually 22)

2. **Push to master branch:**
```bash
git add .
git commit -m "Deploy backend"
git push origin master
```

The GitHub Action will automatically deploy your backend.

## Verification

### 1. Health Check

```bash
# Check if the service is running
curl http://localhost:8000/health

# Expected response:
{"status": "healthy", "service": "supabase-auth-fastapi"}
```

### 2. API Documentation

Visit `http://your-server-ip:8000/docs` to see the interactive API documentation.

### 3. Check Logs

```bash
# View logs
docker-compose logs backend

# Follow logs in real-time
docker-compose logs -f backend
```

## Nginx Configuration (Optional)

If you want to use a custom domain and SSL, set up Nginx:

### 1. Install Nginx

```bash
sudo apt install nginx -y
```

### 2. Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/legatoo-backend
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Enable the Site

```bash
sudo ln -s /etc/nginx/sites-available/legatoo-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Set up SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

## Monitoring and Maintenance

### 1. View Container Status

```bash
docker-compose ps
```

### 2. Restart Services

```bash
docker-compose restart backend
```

### 3. Update Application

```bash
# Pull latest changes
git pull origin master

# Rebuild and restart
docker-compose up -d --build
```

### 4. Backup Database

Since you're using Supabase, your database is automatically backed up. However, you can export data if needed through the Supabase dashboard.

## Troubleshooting

### Common Issues

1. **Port already in use:**
```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

2. **Docker permission issues:**
```bash
sudo usermod -aG docker $USER
# Logout and login again
```

3. **Environment variables not loading:**
   - Check `.env.production` file exists
   - Verify file permissions
   - Restart containers

4. **Database connection issues:**
   - Verify Supabase credentials
   - Check network connectivity
   - Review database URL format

### Logs and Debugging

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend

# View logs with timestamps
docker-compose logs -t backend

# Follow logs in real-time
docker-compose logs -f backend
```

## Security Considerations

1. **Change default secrets** in production
2. **Use HTTPS** in production
3. **Restrict CORS origins** to your frontend domains only
4. **Keep dependencies updated**
5. **Monitor logs** for suspicious activity
6. **Use environment variables** for sensitive data

## Support

If you encounter any issues:

1. Check the logs: `docker-compose logs backend`
2. Verify environment variables
3. Test database connectivity
4. Check server resources (CPU, memory, disk)

Your backend should now be successfully deployed and accessible at `http://your-server-ip:8000`!
