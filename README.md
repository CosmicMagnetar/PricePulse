# PricePulse 📊

A full-stack price tracking application that continuously monitors Amazon product prices over time, providing detailed historical analysis and cross-platform price comparisons using AI.

## 🌟 Features

### Core Features

- User authentication and profile management
- Continuous price tracking at 30-minute intervals
- Product tracking list management
- Real-time price history visualization with 48 data points per day
- Automatic price monitoring and data collection
- Email alerts when prices drop below user-defined thresholds
- Responsive, dark-mode supported UI

### Bonus Features

- AI-powered price comparison across multiple platforms (Flipkart, Meesho, BigBasket)
- Cross-platform price alerts
- Historical price trend analysis
- Price prediction based on historical data
- Export price history data

## 🛠️ Tech Stack

### Frontend

- React.js with TypeScript
- Tailwind CSS for styling
- Chart.js for price history visualization
- Axios for API communication
- React Router for navigation
- JWT for authentication

### Backend

- FastAPI (Python)
- BeautifulSoup4 for web scraping
- APScheduler for continuous price tracking
- SQLite database
- FastMail for email notifications
- JWT authentication
- SQLAlchemy for ORM

### AI Integration

- OpenRouter API for cross-platform price comparison
- LLM-powered price analysis

## 🚀 Project Setup

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn
- Chrome/Chromium (for web scraping)

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/CosmicMagnetar/PricePulse.git
cd PricePulse

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials:
# - JWT_SECRET_KEY
# - SMTP credentials
# - OPENROUTER_API_KEY

# Initialize the database
python init_db.py

# Run the backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
# In a new terminal
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your API URL

# Start development server
npm run dev
```

## 📡 API Endpoints

### Authentication

- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user profile

### Product Tracking

- `POST /track` - Add product to tracking list
- `GET /products` - List user's tracked products
- `GET /products/{product_id}` - Get product details
- `GET /products/{product_id}/history` - Get price history (48 data points per day)
- `DELETE /products/{product_id}` - Remove product from tracking

### Price Alerts

- `POST /alerts` - Set up price alert
- `GET /alerts` - List user alerts
- `DELETE /alerts/{alert_id}` - Remove alert

### Price Comparison

- `GET /compare/{product_id}` - Get cross-platform price comparison

## 📸 Screenshots

_[Screenshots will be added here]_

## 🚀 Deployment

### Frontend

- Hosted on Vercel
- Automatic deployments from main branch
- Environment variables configured in Vercel dashboard

### Backend

- Deployed on Render
- PostgreSQL database
- Scheduled tasks running on Render's cron service
- Continuous price tracking maintained across deployments

## 👥 Credits & Contact

### Developer

- Krishna
- GitHub: [CosmicMagnetar](https://github.com/CosmicMagnetar)

### Contact

- Email: nexiumiq@gmail.com
- GitHub Issues: [PricePulse Issues](https://github.com/CosmicMagnetar/PricePulse/issues)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
