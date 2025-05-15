# E-Commerce Order Discount Engine

## Problem Statement

Design and implement a discount engine for an e-commerce store that applies different types of discounts to orders based on predefined rules. The system should:

1. Allow users to place orders for multiple products
2. Calculate discounts dynamically based on different conditions:
   - **Percentage Discount**: 10% off when total order value exceeds ₹5000
   - **Flat Discount**: ₹500 off when a user has placed more than 5 orders previously
   - **Category-Based Discount**: 5% off on electronics items when more than 3 items are purchased from that category
3. Display a breakdown of applied discounts in order details
4. Store orders and discounts in a database
5. Implement basic authentication so users can only view and create their own orders

## Solution Approach

### Architecture

The solution is built using:
- **Django & Django REST Framework** for the backend API
- **PostgreSQL/SQLite** for the database
- **Redis/In-memory Caching** for caching discount rules
- **JWT** for authentication

### Core Components

#### 1. User Authentication System
- JWT-based authentication for secure API access
- User registration and login endpoints
- Permission checks to ensure users can only access their own orders

#### 2. Product and Category Management
- Products categorized into different groups (Electronics, Clothing, etc.)
- Product information includes name, description, price, and category

#### 3. Cart Management
- Add items into Cart
- List of Cart items
- Increase or Decrease Items of Cart

#### 4. Order Management
- Order creation with multiple order items
- Order status tracking
- Order history for users

#### 5. Discount Engine
- Rule-based discount calculation logic
- Stackable discounts with priority ordering
- Discount application and validation

#### 6. Admin Panel
- Django admin customization for discount rule management
- Dynamic configuration of discount rules
- Analytics for discount usage

#### 7. Caching Layer
- Redis-based caching for frequently accessed discount rules
- Cache invalidation strategy for rule updates

#### 8. Logging System

- Comprehensive logging across all application components
- Configurable log levels for development and production environments
- Structured log format for better parsing and analysis

#### 9. Error Handling Framework

- Custom exception classes for different error scenarios
- Consistent error response structure across the API

### Discount Application Logic

1. **Order Creation Flow**:
   - User adds products to cart
   - System calculates preliminary total
   - Discount engine evaluates applicable rules
   - Discounts are applied based on priority
   - Final amount is calculated
   - Order is stored with discount information

2. **Discount Calculation**:
   - Check order total for percentage discount
   - Query user's order history for flat discount
   - Count category items for category-based discounts
   - Apply stackable discounts in priority order

3. **Caching Strategy**:
   - Cache discount rules with configurable TTL
   - Invalidate cache on rule updates
   - Store user order counts in cache for quick access

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login and receive JWT token
- `POST /api/auth/token/refresh/` - Refresh JWT token

### Products
- `GET /api/products/` - List all products
- `GET /api/products/{slug}/` - Get product details
- `POST /api/products/` - Create Product (Only for admin)
- `PUT /api/products/{slug}/` - Update a particular Product (Only for admin)
- `PATCH /api/products/{slug}/` - Partial Update a particular Product (Only for admin)
- `DELETE /api/products/{slug}/` - Delete a particular Product (Only for admin)
- `GET /api/products/categories/` - List all categories
- `GET /api/products/categories/{id}/` - Get categories details
- `POST /api/products/categories/{id}/` - Create Cateory (Only for admin)
- `PUT /api/products/categories/{id}/` - Update a particular Cateory (Only for admin)
- `PATCH /api/products/categories/{id}/` - Partial Update a particular Cateory (Only for admin)
- `DELETE /api/products/categories/{id}/` - Delete a particular Cateory (Only for admin)

### Carts
- `GET /api/cart/` - List Cart of a user
- `POST /api/cart/` - Add item into the user cart
- `GET /api/cart/{id}/` - Detail of Single item of the cart
- `PUT /api/cart/{id}/` - Update the Single item of the cart
- `DELETE /api/cart/{id}/` - Delete the Single item of the cart
- `POST /api/cart/{id}/increase/` - Increase quantity of Single item of the cart
- `POST /api/cart/{id}/decrease/` - Decrease quantity of Single item of the cart

### Orders
- `POST /api/orders/create-order/` - Create a new order
- `GET /api/orders/` - List user's orders with discount breakdown
- `GET /api/orders/{id}/` - Get order details with discount breakdown

### Discount
- `GET /api/discount-rule/` - List all discount rules
- `POST /api/discount-rule/` - Create new discount rule
- `GET /api/discount-rule/{id}/` - Get a discount rules
- `PUT /api/discount-rule/{id}/` - Update discount rule
- `DELETE /api/discount-rule/{id}/` - Delete discount rule

## Installation and Setup

### Prerequisites
- Python 3.8+
- Django
- PostgreSQL
- Redis (optional, for caching)

### Installation Steps

1. Clone the repository
```bash
git clone https://github.com/yourusername/order-discount-engine.git
cd order-discount-engine
```

2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment variables
```bash
cp .env.example .env
# Edit .env file with your database and Redis configuration
```

5. Run migrations
```bash
python manage.py migrate
```

6. Create a superuser for admin access
```bash
python manage.py createsuperuser
```

7. Run the development server
```bash
python manage.py runserver
```

8. Access the application
   - API: http://localhost:8000/api/
   - Admin panel: http://localhost:8000/admin/

## Testing

Run the test suite to verify functionality:
```bash
python manage.py test
```

## Advanced Features Implemented

### Stackable Discounts
- Discounts are applied in order of priority
- Each discount can be configured to apply to the original amount or the previously discounted amount
- Admin can reorder discount priority through the admin panel

### Dynamic Discount Configuration
- Admin panel allows creating, updating, and deleting discount rules
- Rules can be activated/deactivated without deletion
- Time-based discounts can be scheduled

### Performance Optimization
- Redis cache for discount rules
- Database query optimization using select_related and prefetch_related
- Bulk discount calculation for improved performance

### Comprehensive Logging

- Structured logging throughout the application
- Different log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Log rotation and retention policies
- Custom log formatters for enhanced readability

### Robust Error Handling

- Custom exception classes for different error scenarios
- Global exception handler for consistent API responses
- Detailed error messages for debugging
- User-friendly error messages in production

## Future Enhancements

1. **Coupon System**: Allow users to enter coupon codes for additional discounts
2. **Time-limited Discounts**: Discounts that are only valid for specific time periods
3. **Personalized Discounts**: User-specific discounts based on browsing and purchase history
4. **A/B Testing**: Test different discount strategies for effectiveness
5. **Analytics Dashboard**: Track discount usage and effectiveness
6. **Webhooks**: Notify external systems when discounts are applied
7. **Mobile App Integration**: Extend API for mobile application use