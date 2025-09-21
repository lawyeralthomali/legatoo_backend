# Supabase Auth FastAPI Backend

A production-ready FastAPI backend that integrates seamlessly with Supabase Authentication. This project uses Supabase's built-in `auth.users` table for authentication and creates a separate `profiles` table for additional user information.

## Project Structure

```
my_project/
│
├── app/
│   ├── __init__.py
│   ├── main.py                           # Entry point to run the FastAPI app
│   ├── api/
│   │   ├── __init__.py
│   │   ├── users.py                      # Contains everything related to users (models, schemas, services, endpoints)
│   │   └── items.py                      # (can be added later with the same structure)
│   ├── models/
│   │   ├── __init__.py
│   │   └── item.py                       # Only item model (users model is inside users.py)
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── item.py                       # Only item schema (users schema is inside users.py)
│   ├── services/
│   │   ├── __init__.py
│   │   └── item_service.py               # Service logic for items (user logic is inside users.py)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py                   # SQLAlchemy async engine and session
│   │   └── models.py                     # Optional: SQLAlchemy base metadata
│   └── utils/
│       ├── __init__.py
│       └── hashing.py                    # Password hashing using passlib
│
├── requirements.txt                      # Required libraries
├── alembic/                              # Alembic migration setup
├── tests/
│   ├── __init__.py
│   ├── test_users.py                     # Tests for users API
│   └── test_items.py                     # Tests for items API
└── README.md                             # Project documentation
```

## Features

- **User Management**: Complete user registration, authentication, and management
- **Password Security**: Secure password hashing using bcrypt
- **Async Database**: Async SQLAlchemy with PostgreSQL support
- **Database Migrations**: Alembic setup for database schema management
- **API Documentation**: Automatic OpenAPI/Swagger documentation
- **Testing**: Comprehensive test suite with pytest
- **Type Safety**: Full type hints and Pydantic models

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd my_project
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database**:
   - Install PostgreSQL
   - Create a database named `my_project_db`
   - Update the database URL in `app/db/database.py` if needed

5. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

## Running the Application

1. **Start the development server**:
   ```bash
   python run.py
   # or
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Access the API documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Users

- `POST /api/v1/users/register` - Register a new user
- `POST /api/v1/users/login` - Login user
- `GET /api/v1/users/` - Get list of users (with pagination)
- `GET /api/v1/users/{user_id}` - Get user by ID
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user

### General

- `GET /` - Root endpoint
- `GET /health` - Health check

## Database Models

### User Model
- `id`: Primary key
- `email`: Unique email address
- `username`: Unique username
- `hashed_password`: Bcrypt hashed password
- `is_active`: Account status
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Item Model
- `id`: Primary key
- `title`: Item title
- `description`: Item description
- `price`: Item price
- `is_available`: Availability status
- `owner_id`: Foreign key to User
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

## Environment Variables

Set the following environment variables:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/my_project_db
```

## Testing

Run the test suite:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=app
```

## Database Migrations

Create a new migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:

```bash
alembic upgrade head
```

Rollback migrations:

```bash
alembic downgrade -1
```

## Development

### Adding New Features

1. **For new models**: Add them to the appropriate directory in `models/`
2. **For new schemas**: Add them to the appropriate directory in `schemas/`
3. **For new services**: Add them to the appropriate directory in `services/`
4. **For new API endpoints**: Add them to the appropriate file in `api/`

### Code Style

This project follows Python best practices:
- Type hints for all functions
- Async/await for database operations
- Pydantic models for data validation
- Comprehensive error handling

## Security Features

- Password hashing with bcrypt
- Input validation with Pydantic
- SQL injection protection with SQLAlchemy ORM
- CORS middleware for cross-origin requests

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License.
