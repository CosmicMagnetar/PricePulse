# PricePulse Codebase Documentation

## Project Structure

```
PricePulse/
├── backend/
│   ├── main.py              # FastAPI application entry point
│   ├── models.py            # Database models
│   ├── auth.py             # Authentication logic
│   ├── scraper.py          # Amazon scraping logic
│   ├── scheduler.py        # Continuous price tracking
│   ├── email_service.py    # FastMail integration
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.tsx         # Main React component
│   │   ├── components/     # Reusable components
│   │   │   ├── auth/      # Authentication components
│   │   │   ├── dashboard/ # Dashboard components
│   │   │   └── products/  # Product tracking components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── context/       # React context providers
│   │   └── types/         # TypeScript interfaces
│   └── package.json       # Node.js dependencies
└── README.md              # Project documentation
```

## Backend Implementation

### 1. Authentication (auth.py)

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/register")
async def register(user: UserCreate):
    # Check if user exists
    if get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    hashed_password = pwd_context.hash(user.password)
    user = create_user(user.email, hashed_password)

    return {"message": "User created successfully"}

@router.post("/login")
async def login(user_data: UserLogin):
    user = authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
```

### 2. Database Models (models.py)

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    products = relationship("Product", back_populates="user")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amazon_id = Column(String)
    name = Column(String)
    current_price = Column(Float)
    image_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="products")
    price_history = relationship("PriceHistory", back_populates="product")

    __table_args__ = (UniqueConstraint('user_id', 'amazon_id'),)
```

### 3. Continuous Price Tracking (scheduler.py)

```python
class PriceTracker:
    def __init__(self):
        self.scheduler = APScheduler()
        self.scraper = AmazonScraper()

    def start(self):
        # Schedule price checks every 30 minutes
        self.scheduler.add_job(
            self.track_prices,
            'interval',
            minutes=30,
            id='price_tracking'
        )
        self.scheduler.start()

    async def track_prices(self):
        # Get all tracked products
        products = self.get_all_tracked_products()

        for product in products:
            try:
                # Fetch current price
                current_price = await self.scraper.get_price(product.amazon_id)

                # Store price point
                await self.store_price_point(product.id, current_price)

                # Check alerts
                await self.check_price_alerts(product, current_price)

            except Exception as e:
                logger.error(f"Error tracking product {product.id}: {str(e)}")

    async def store_price_point(self, product_id: int, price: float):
        # Store price point in history
        price_history = PriceHistory(
            product_id=product_id,
            price=price,
            timestamp=datetime.utcnow()
        )
        db.add(price_history)
        await db.commit()
```

### 4. Frontend Authentication (App.tsx)

```typescript
function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for stored token
    const token = localStorage.getItem("token");
    if (token) {
      // Validate token and get user data
      validateToken(token).then(setUser);
    }
    setLoading(false);
  }, []);

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <Router>
      <AuthProvider value={{ user, setUser }}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </Router>
  );
}
```

### 5. Product Tracking Component

```typescript
const ProductTracker: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch user's tracked products
    const fetchProducts = async () => {
      const response = await axios.get("/api/products");
      setProducts(response.data);
      setLoading(false);
    };
    fetchProducts();
  }, []);

  const addProduct = async (url: string) => {
    const response = await axios.post("/api/products", { url });
    setProducts([...products, response.data]);
  };

  return (
    <div>
      <AddProductForm onSubmit={addProduct} />
      <ProductList products={products} />
    </div>
  );
};
```

### 6. Price History Chart

```typescript
const PriceHistoryChart: React.FC<{ productId: string }> = ({ productId }) => {
  const [priceHistory, setPriceHistory] = useState<PricePoint[]>([]);

  useEffect(() => {
    // Fetch 48 data points (24 hours)
    const fetchPriceHistory = async () => {
      const response = await axios.get(`/api/products/${productId}/history`);
      setPriceHistory(response.data);
    };
    fetchPriceHistory();
  }, [productId]);

  const chartData = {
    labels: priceHistory.map((point) =>
      new Date(point.timestamp).toLocaleTimeString()
    ),
    datasets: [
      {
        label: "Price History",
        data: priceHistory.map((point) => point.price),
        borderColor: "rgb(59, 130, 246)",
        tension: 0.1,
      },
    ],
  };

  return (
    <div className="h-80">
      <Line data={chartData} options={chartOptions} />
    </div>
  );
};
```

## Assignment Requirements Mapping

1. **User Authentication**

   - JWT-based authentication
   - Protected routes
   - User profile management

2. **Continuous Price Tracking**

   - 30-minute interval scheduling
   - 48 data points per day
   - Historical data storage

3. **Product Management**

   - Add/remove tracked products
   - Price history visualization
   - Cross-platform comparison

4. **Price Alerts**

   - Email notifications
   - Price threshold monitoring
   - Alert management

5. **Data Visualization**

   - Interactive price charts
   - Historical trend analysis
   - Real-time updates

6. **Security**
   - JWT token encryption
   - Password hashing
   - API authentication
   - Data isolation
