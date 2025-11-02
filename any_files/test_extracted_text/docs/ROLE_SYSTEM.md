# Role-Based Access Control System

This document explains the role-based access control (RBAC) system implemented in the application.

## Overview

The system implements three distinct user roles with hierarchical permissions:

- **super_admin**: Highest level access, created only during database initialization
- **admin**: Default role for new user signups
- **user**: Regular user role (for future use)

## Role Hierarchy

```
super_admin (Level 3) - Highest access
    ↓
admin (Level 2) - Default for new signups
    ↓
user (Level 1) - Basic access
```

## Implementation Details

### 1. Role Model (`app/models/role.py`)

```python
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"

# Default role for new signups
DEFAULT_USER_ROLE = ROLE_ADMIN
```

### 2. User Model Updates (`app/models/user.py`)

- Added `role` field with default value `DEFAULT_USER_ROLE` (admin)
- Added helper properties: `is_super_admin`, `is_admin`, `is_user`
- Role field is indexed for performance

### 3. Database Schema

#### Users Table
```sql
ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'admin' NOT NULL;
```

#### Roles Table
```sql
CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME
);
```

## Role Creation Rules

### Super Admin
- **Creation**: Only through `create_super_admin.py` script
- **Default Credentials**: 
  - Email: `superadmin@legatoo.com`
  - Password: `superadmin123`
- **Security**: Must change password after first login
- **Access**: Cannot be created through normal signup process

### Admin (Default Role)
- **Creation**: Automatically assigned to all new signups
- **Assignment**: Set in `auth_service.py` during user creation
- **Access**: Full administrative privileges (except super admin functions)

### User Role
- **Creation**: Reserved for future implementation
- **Assignment**: To be determined based on business requirements
- **Access**: Basic user privileges

## Permission System

### Role Permissions

#### Super Admin Permissions
- `user.create` - Create new users
- `user.read` - Read user information
- `user.update` - Update user information
- `user.delete` - Delete users
- `role.manage` - Manage user roles
- `system.admin` - System administration
- `database.admin` - Database administration

#### Admin Permissions
- `user.create` - Create new users
- `user.read` - Read user information
- `user.update` - Update user information
- `profile.manage` - Manage user profiles
- `subscription.manage` - Manage subscriptions

#### User Permissions
- `profile.read` - Read own profile
- `profile.update` - Update own profile
- `subscription.read` - Read subscription information

## Usage Examples

### 1. Creating Super Admin

```bash
# Run the super admin creation script
python create_super_admin.py
```

### 2. Running Migration

```bash
# Add role field to existing users
python add_role_migration.py
```

### 3. Using Role Dependencies in FastAPI

```python
from app.utils.role_auth import require_super_admin_role, require_admin_role

@app.get("/admin/users")
async def get_users(current_user = Depends(require_admin_role)):
    # Only admins and super admins can access
    pass

@app.get("/super-admin/system")
async def system_admin(current_user = Depends(require_super_admin_role)):
    # Only super admins can access
    pass
```

### 4. Checking Permissions

```python
from app.models.role import has_permission, UserRole

# Check if user has admin permission
if has_permission(user.role, UserRole.ADMIN):
    # User has admin or higher access
    pass
```

## API Endpoints

### User Management (Admin+)
- `GET /api/v1/users` - List users
- `GET /api/v1/users/{id}` - Get user details
- `PUT /api/v1/users/{id}/role` - Update user role
- `DELETE /api/v1/users/{id}` - Delete user

### System Administration (Super Admin)
- `GET /api/v1/admin/system` - System information
- `POST /api/v1/admin/roles` - Create new roles
- `GET /api/v1/admin/logs` - System logs

## Security Considerations

### 1. Role Assignment
- Super admin can only be created through initialization script
- New signups automatically get admin role (no frontend control)
- Role changes require appropriate permissions

### 2. Token Security
- JWT tokens include role information
- Role validation happens on each request
- Tokens are validated against database roles

### 3. Database Security
- Role field is indexed for performance
- Foreign key constraints prevent orphaned roles
- Audit trail for role changes

## Migration Guide

### For Existing Applications

1. **Run Migration Script**:
   ```bash
   python add_role_migration.py
   ```

2. **Create Super Admin**:
   ```bash
   python create_super_admin.py
   ```

3. **Update Application Code**:
   - Import role dependencies where needed
   - Add role checks to protected endpoints
   - Update user creation logic

### For New Applications

1. **Initialize Database**:
   ```bash
   python create_tables.py
   python create_super_admin.py
   ```

2. **Configure Default Role**:
   - Modify `DEFAULT_USER_ROLE` in `role.py` if needed
   - Update signup service if different default required

## Testing

### Test Super Admin Creation
```bash
python create_super_admin.py
```

### Test Role Migration
```bash
python add_role_migration.py
```

### Test Role Permissions
```python
from app.models.role import has_permission, UserRole

# Test permission checking
assert has_permission(UserRole.SUPER_ADMIN, UserRole.ADMIN) == True
assert has_permission(UserRole.ADMIN, UserRole.SUPER_ADMIN) == False
```

## Future Enhancements

### 1. Dynamic Roles
- Create custom roles through admin interface
- Assign specific permissions to custom roles
- Role inheritance and composition

### 2. Permission Granularity
- Resource-level permissions
- Action-based permissions
- Context-aware permissions

### 3. Audit Logging
- Track role changes
- Log permission usage
- Security event monitoring

## Troubleshooting

### Common Issues

1. **Role Field Missing**:
   - Run `add_role_migration.py`
   - Check database schema

2. **Super Admin Not Created**:
   - Run `create_super_admin.py`
   - Check database connection

3. **Permission Denied**:
   - Verify user role in database
   - Check role hierarchy
   - Validate JWT token

### Debug Commands

```python
# Check user role
from app.db.database import get_db
from app.models.user import User
from sqlalchemy import select

async def check_user_role(email: str):
    async for db in get_db():
        result = await db.execute(
            select(User.role).where(User.email == email)
        )
        role = result.scalar_one_or_none()
        print(f"User {email} has role: {role}")
```

## Security Best Practices

1. **Change Default Passwords**: Always change super admin password after first login
2. **Regular Audits**: Periodically review user roles and permissions
3. **Principle of Least Privilege**: Assign minimum required permissions
4. **Monitor Access**: Log and monitor role-based access attempts
5. **Secure Token Handling**: Implement proper JWT token validation
