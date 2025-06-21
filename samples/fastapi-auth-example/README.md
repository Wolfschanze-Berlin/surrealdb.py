# FastAPI SurrealDB Authentication Example

A complete FastAPI authentication and CRUD example using SurrealDB as the database backend.

## Features

- **JWT Authentication** with bcrypt password hashing
- **User Management** with registration, login, and CRUD operations
- **Profile Management** with user profiles
- **Role-based Access Control** (admin/user roles)
- **SurrealDB Integration** for modern database operations
- **OpenAPI/Swagger Documentation** auto-generated
- **Docker Support** with multi-stage builds
- **Production Ready** with proper error handling and validation

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login (returns JWT)
- `POST /auth/logout` - User logout

### Users
- `GET /users/me` - Get current user
- `PUT /users/me` - Update current user
- `GET /users/{user_id}` - Get user by ID (admin only)
- `GET /users/` - List users (admin only)
- `DELETE /users/{user_id}` - Delete user (admin only)

### Profiles
- `GET /profiles/me` - Get current user profile
- `PUT /profiles/me` - Update current user profile
- `POST /profiles/` - Create profile
- `GET /profiles/{user_id}` - Get user profile

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone and navigate to the project:**
   ```bash
   cd fastapi-auth-example
   ```

2. **Start the services:**
   ```bash
   docker-compose up -d
   ```

3. **Access the application:**
   - FastAPI App: http://localhost:8001
   - API Documentation: http://localhost:8001/docs
   - SurrealDB: http://localhost:8000

### Manual Setup with UV (Recommended for Development)

1. **Create and activate virtual environment:**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   uv pip install -r requirements.txt
   ```

3. **Install SurrealDB:**
   ```bash
   # Install SurrealDB
   curl -sSf https://install.surrealdb.com | sh
   
   # Start SurrealDB
   surreal start --log trace --user root --pass root memory
   ```

4. **Set environment variables:**
   ```bash
   export SURREALDB_URL="ws://localhost:8000/rpc"
   export SURREALDB_NAMESPACE="test"
   export SURREALDB_DATABASE="test"
   export SURREALDB_USERNAME="root"
   export SURREALDB_PASSWORD="root"
   export SECRET_KEY="your-super-secret-key"
   ```

5. **Run the application:**
   ```bash
   python main.py
   ```

### Manual Setup (Alternative)

1. **Install SurrealDB:**
   ```bash
   # Install SurrealDB
   curl -sSf https://install.surrealdb.com | sh
   
   # Start SurrealDB
   surreal start --log trace --user root --pass root memory
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables:**
   ```bash
   export SURREALDB_URL="ws://localhost:8000/rpc"
   export SURREALDB_NAMESPACE="test"
   export SURREALDB_DATABASE="test"
   export SURREALDB_USERNAME="root"
   export SURREALDB_PASSWORD="root"
   export SECRET_KEY="your-super-secret-key"
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

## Usage Examples

### 1. Register a new user
```bash
curl -X POST "http://localhost:8001/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "username": "testuser",
       "password": "password123"
     }'
```

### 2. Login and get JWT token
```bash
curl -X POST "http://localhost:8001/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=user@example.com&password=password123"
```

### 3. Access protected endpoint
```bash
curl -X GET "http://localhost:8001/users/me" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 4. Create user profile
```bash
curl -X POST "http://localhost:8001/profiles/" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "first_name": "John",
       "last_name": "Doe",
       "bio": "Software Developer"
     }'
```

## Configuration

Environment variables can be set in a `.env` file or passed directly:

```env
# SurrealDB Configuration
SURREALDB_URL=ws://localhost:8000/rpc
SURREALDB_NAMESPACE=test
SURREALDB_DATABASE=test
SURREALDB_USERNAME=root
SURREALDB_PASSWORD=root

# JWT Configuration
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# App Configuration
DEBUG=false
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123
```

## Database Schema

### Users Table
- `id` - Unique identifier
- `email` - User email (unique)
- `username` - Username (unique)
- `hashed_password` - Bcrypt hashed password
- `is_active` - Account status
- `is_admin` - Admin privileges
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### Profiles Table
- `id` - Unique identifier
- `user_id` - Reference to users table
- `first_name` - First name
- `last_name` - Last name
- `bio` - User biography
- `avatar_url` - Profile picture URL
- `phone` - Phone number
- `location` - User location
- `website` - Personal website
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## Production Deployment

1. **Set secure environment variables**
2. **Use HTTPS in production**
3. **Configure CORS appropriately**
4. **Set up proper logging**
5. **Use a production WSGI server**
6. **Set up database backups**

## Security Considerations

- Change the default `SECRET_KEY` in production
- Use strong passwords for database access
- Configure CORS for your specific domains
- Implement rate limiting
- Use HTTPS in production
- Regularly update dependencies

## License

This project is licensed under the MIT License.