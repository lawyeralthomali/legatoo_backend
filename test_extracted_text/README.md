# Legatoo Backend API

Enhanced FastAPI backend for the Legatoo legal services platform with Clean Architecture and Legal AI Assistant integration.

## 🚀 Features

- **Enhanced Authentication System** - Supabase integration with email verification
- **Legal Assistant AI** - AI-powered legal advice and document analysis
- **Document Management** - Secure document storage and processing
- **User Profiles** - Comprehensive user profile management
- **Subscription Management** - Billing and plan management system
- **Clean Architecture** - Repository pattern with proper separation of concerns
- **Email Services** - Automated email notifications and verification
- **API Documentation** - Interactive Swagger UI documentation

## 🏗️ Architecture

This backend follows Clean Architecture principles with:

- **Domain Layer** - Business logic and entities
- **Application Layer** - Use cases and application services
- **Infrastructure Layer** - Database, external services, and frameworks
- **Presentation Layer** - API endpoints and controllers

## 📋 API Endpoints

### Core Endpoints
- `GET /` - API root and information
- `GET /health` - Health check endpoint
- `GET /docs` - API documentation

### Authentication (`/api/v1/auth`)
- `POST /signin` - User sign in
- `POST /signup` - User registration
- `GET /user` - Get user information
- `POST /verify-email` - Email verification
- `POST /reset-password` - Password reset

### User Profiles (`/api/v1/profiles`)
- `GET /me` - Get current user profile
- `POST /create` - Create new profile
- `PUT /update` - Update profile
- `DELETE /delete` - Delete profile

### Subscriptions (`/api/v1/subscriptions`)
- `GET /status` - Get subscription status
- `GET /plans` - Available subscription plans
- `POST /upgrade` - Upgrade subscription
- `GET /billing` - Billing information

### Legal Assistant (`/api/v1/legal-assistant`)
- `POST /chat` - AI legal chat
- `POST /analyze` - Document analysis
- `POST /research` - Legal research
- `POST /generate` - Generate legal documents

### Document Management (`/api/v1/documents`)
- `POST /upload` - Upload documents
- `GET /download` - Download documents
- `POST /process` - Process documents
- `GET /templates` - Legal document templates

## 🛠️ Development

### Prerequisites
- Python 3.11+
- PostgreSQL database
- Supabase account for authentication
- Docker (optional, for containerized deployment)

### Installation

1. Clone the repository:
```bash
git clone git@github.com:lawyeralthomali/legatoo_backend.git
cd legatoo_backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the development server:
```bash
python run.py
```

### Testing

Run the test suite:
```bash
pytest tests/ -v
```

## 🚀 Deployment

This repository includes automated deployment to Hostinger via GitHub Actions.

### Manual Deployment

1. Connect to your Hostinger server via SSH
2. Navigate to the backend directory
3. Pull the latest changes:
```bash
git pull origin master
```
4. Start the backend:
```bash
python3 deploy_backend.py
```

### Automated Deployment

The repository is configured with GitHub Actions that automatically deploy to Hostinger when changes are pushed to the `master` branch.

**Required GitHub Secrets:**
- `HOSTINGER_HOST` - Your Hostinger server IP
- `HOSTINGER_USERNAME` - SSH username
- `HOSTINGER_PASSWORD` - SSH password
- `HOSTINGER_PORT` - SSH port (usually 65002)

## 📚 Documentation

### Interactive API Documentation
- **Swagger UI**: https://legatoo.westlinktowing.com/api/swagger.html
- **OpenAPI Spec**: https://legatoo.westlinktowing.com/api/swagger.json

### Health Check
- **Health Endpoint**: https://legatoo.westlinktowing.com/api/health

## 🔧 Configuration

### Environment Variables

Key environment variables for production:

```env
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Security
SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 📊 Monitoring

The backend includes comprehensive monitoring:

- Health check endpoint for service status
- Structured logging for debugging
- Performance metrics
- Error tracking and reporting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/new-feature`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Email: support@legatoo.com
- Documentation: https://legatoo.westlinktowing.com/api/swagger.html
- Issues: GitHub Issues

---

**Legatoo Backend v2.0.0** - Enhanced with Legal AI and Clean Architecture
