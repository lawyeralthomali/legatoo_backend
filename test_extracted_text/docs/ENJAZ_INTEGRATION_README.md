# Enjaz Integration - FastAPI Backend

This document provides a comprehensive guide for the Enjaz integration feature in the FastAPI backend.

## Overview

The Enjaz integration allows users to:
- Connect their Enjaz accounts with encrypted credentials
- Automatically sync case data from the Enjaz system
- View and manage their imported cases

## Architecture

### Database Models

1. **EnjazAccount** (`app/models/enjaz_account.py`)
   - Stores encrypted Enjaz credentials
   - Linked to users via foreign key
   - Automatic timestamps for audit trail

2. **CaseImported** (`app/models/case_imported.py`)
   - Stores case data scraped from Enjaz
   - Linked to users and Enjaz accounts
   - Supports additional case metadata

### Security Features

- **Credential Encryption**: All Enjaz credentials are encrypted using Fernet symmetric encryption
- **JWT Authentication**: All endpoints require valid JWT tokens
- **User Isolation**: Users can only access their own data
- **Audit Logging**: All operations are logged with correlation IDs

## API Endpoints

### 1. Connect Enjaz Account
```
POST /api/v1/enjaz/connect
```

**Request Body:**
```json
{
  "username": "enjaz_username",
  "password": "enjaz_password"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Enjaz account connected successfully",
  "data": {
    "id": 1,
    "username": "***masked***",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": null
  },
  "errors": []
}
```

### 2. Sync Cases
```
POST /api/v1/enjaz/sync-cases
```

**Response:**
```json
{
  "success": true,
  "message": "Cases synced successfully",
  "data": {
    "success": true,
    "message": "Successfully synced 15 cases",
    "cases_imported": 12,
    "cases_updated": 3,
    "total_cases": 15
  },
  "errors": []
}
```

### 3. Get Cases
```
GET /api/v1/enjaz/cases?limit=10&offset=0
```

**Response:**
```json
{
  "success": true,
  "message": "Cases retrieved successfully",
  "data": {
    "success": true,
    "message": "Retrieved 10 cases",
    "data": [
      {
        "id": 1,
        "case_number": "CASE-2024-001",
        "case_type": "Civil",
        "status": "Active",
        "case_data": "{\"additional_info\": \"...\"}",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z"
      }
    ],
    "total_count": 25
  },
  "errors": []
}
```

### 4. Account Status
```
GET /api/v1/enjaz/account-status
```

### 5. Disconnect Account
```
DELETE /api/v1/enjaz/disconnect
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
playwright install chromium
```

### 3. Environment Configuration

Add the following to your `supabase.env` file:

```env
# Encryption Key for Enjaz Credentials
ENCRYPTION_KEY=your-encryption-key-here
```

Generate an encryption key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 4. Database Migration

Run the migration script to create the new tables:

```bash
python migrate_enjaz_tables.py
```

### 5. Start the Server

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## RPA Integration

The system uses Playwright for web scraping the Enjaz system:

### EnjazBot Class (`app/utils/enjaz_bot.py`)

- **Headless Browser**: Runs Chrome in headless mode by default
- **Login Automation**: Handles Enjaz login process
- **Case Scraping**: Extracts case data from Enjaz interface
- **Error Handling**: Robust error handling for network issues

### Usage Example

```python
from app.utils.enjaz_bot import scrape_enjaz_cases

# Scrape cases
cases = await scrape_enjaz_cases("username", "password")
```

## Security Considerations

1. **Credential Encryption**: All Enjaz credentials are encrypted using industry-standard Fernet encryption
2. **Environment Variables**: Encryption keys are stored in environment variables
3. **JWT Authentication**: All API endpoints require valid authentication
4. **User Isolation**: Users can only access their own data
5. **Audit Logging**: All operations are logged for security auditing

## Error Handling

The system provides comprehensive error handling:

- **Authentication Errors**: Invalid or expired JWT tokens
- **Validation Errors**: Invalid request data
- **Network Errors**: Connection issues with Enjaz system
- **Scraping Errors**: Failed data extraction
- **Database Errors**: Database operation failures

## Testing

### Manual Testing

1. **Connect Account**: Test with valid Enjaz credentials
2. **Sync Cases**: Verify case data is properly imported
3. **View Cases**: Check pagination and data display
4. **Error Scenarios**: Test with invalid credentials

### API Testing

Use the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Troubleshooting

### Common Issues

1. **Encryption Key Missing**: Ensure `ENCRYPTION_KEY` is set in environment
2. **Playwright Browser Issues**: Run `playwright install chromium`
3. **Database Connection**: Check database configuration
4. **CORS Issues**: Verify CORS origins configuration

### Logs

Check the application logs for detailed error information:
- Log file: `logs/app.log`
- Console output for real-time debugging

## Future Enhancements

1. **Scheduled Sync**: Automatic periodic case synchronization
2. **Case Filtering**: Advanced filtering and search capabilities
3. **Notifications**: Real-time notifications for case updates
4. **Analytics**: Case statistics and reporting
5. **Multi-tenant Support**: Support for multiple Enjaz accounts per user

## Support

For issues or questions regarding the Enjaz integration:
1. Check the logs for error details
2. Verify environment configuration
3. Test API endpoints using the interactive documentation
4. Review the troubleshooting section above
