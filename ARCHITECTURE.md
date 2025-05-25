# PricePulse System Architecture

## System Overview

```mermaid
graph TD
    A[User] -->|Login/Register| B[Frontend]
    B -->|Auth Request| C[FastAPI Backend]
    C -->|Validate| D[Auth Service]
    D -->|JWT Token| B
    B -->|API Request| C
    C -->|Scrape| E[Amazon]
    C -->|Store| F[SQLite DB]
    C -->|Schedule| G[APScheduler]
    G -->|Every 30min| C
    C -->|Email Alert| H[FastMail]
    C -->|AI Request| I[OpenRouter API]
    I -->|Price Data| J[Other Platforms]
    C -->|Response| B
    B -->|Render| K[Price History Chart]
    B -->|Display| L[Price Comparison]
```

## Component Details

### 1. Frontend (React + TypeScript)

- **Authentication Components**

  - Login form
  - Registration form
  - Protected routes
  - JWT token management

- **Dashboard Component**

  - User's tracked products list
  - Quick price overview
  - Add new product form

- **Product Tracking Component**
  - Product details display
  - Price history chart (48 points/day)
  - Price alerts management
  - Cross-platform comparison

### 2. Backend (FastAPI)

- **Authentication Routes**

  ```
  /auth
  ├── POST /register: Create new user
  ├── POST /login: User authentication
  └── GET /me: Get user profile
  ```

- **Product Management Routes**

  ```
  /products
  ├── GET /: List user's products
  ├── POST /: Add new product
  ├── GET /{id}: Get product details
  ├── GET /{id}/history: Get price history
  └── DELETE /{id}: Remove product
  ```

- **Continuous Tracking Service**
  - APScheduler configuration
  - 30-minute intervals
  - Price update triggers
  - Data point collection

### 3. Database Schema

```sql
-- Users Table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE,
    password_hash TEXT,
    created_at TIMESTAMP
);

-- Products Table
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    amazon_id TEXT,
    name TEXT,
    current_price REAL,
    image_url TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, amazon_id)
);

-- Price History Table
CREATE TABLE price_history (
    id INTEGER PRIMARY KEY,
    product_id INTEGER,
    price REAL,
    timestamp TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Alerts Table
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    product_id INTEGER,
    email TEXT,
    target_price REAL,
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

### 4. Continuous Price Tracking Flow

```mermaid
sequenceDiagram
    participant S as Scheduler
    participant B as Backend
    participant D as Database
    participant E as Email Service

    loop Every 30 minutes
        S->>B: Trigger price check
        B->>D: Get all tracked products
        D-->>B: Return products
        loop For each product
            B->>B: Fetch current price
            B->>D: Store price point
            B->>D: Get product alerts
            alt Price <= Target
                B->>E: Send alert email
                E-->>B: Email sent
            end
        end
    end
```

### 5. User Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant D as Database

    U->>F: Enter credentials
    F->>B: Login request
    B->>D: Validate credentials
    D-->>B: User data
    B->>B: Generate JWT
    B-->>F: Return token
    F->>F: Store token
    F->>B: API requests with token
    B->>B: Validate token
    B-->>F: Protected data
```

## Data Flow

1. **User Authentication**

   - User registers/logs in
   - JWT token generated
   - Token used for subsequent requests

2. **Product Tracking**

   - User adds product to track
   - System starts 30-minute monitoring
   - Price history collected continuously
   - 48 data points per day stored

3. **Price Monitoring**

   - Scheduler triggers every 30 minutes
   - All tracked products updated
   - Price history maintained
   - Alerts triggered if needed

4. **Data Visualization**
   - Frontend requests price history
   - Backend returns 48 daily points
   - Chart.js renders interactive graph
   - User can view trends over time

## Security Considerations

1. **Authentication Security**

   - JWT token encryption
   - Password hashing
   - Token expiration
   - Secure cookie storage

2. **API Security**

   - Rate limiting
   - Input validation
   - CORS configuration
   - Request authentication

3. **Data Protection**

   - Email encryption
   - Secure storage
   - API key management
   - User data isolation

4. **Error Handling**
   - Graceful degradation
   - Retry mechanisms
   - User feedback
   - Error logging
