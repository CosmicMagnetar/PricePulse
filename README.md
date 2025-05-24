# PricePulse

A real-time Amazon price tracking application that helps users monitor product prices and get notified when prices drop to their target amount.

## Features

- 🔍 Real-time price tracking for Amazon products
- 📊 Price history visualization with charts
- 🔔 Email notifications for price drops
- 🌓 Dark/Light mode
- 📱 Responsive design
- ⏰ Automated price updates every 30 minutes
- 📈 Historical price data storage

## Tech Stack

- **Frontend**: React, TypeScript, Tailwind CSS, Chart.js
- **Backend**: FastAPI, Python
- **Database**: SQLite
- **Email**: FastAPI-Mail
- **Scheduler**: APScheduler
- **Web Scraping**: BeautifulSoup4

## Setup Instructions

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/PricePulse.git
   cd PricePulse
   ```

2. **Backend Setup**

   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

   # Set up environment variables
   cp .env.example .env
   # Edit .env with your email settings

   # Run backend
   uvicorn backend.main:app --reload
   ```

3. **Frontend Setup**

   ```bash
   cd frontend
   npm install
   npm start
   ```

4. **Database Setup**
   ```bash
   # The database will be automatically created on first run
   # It will be located at prices.db in the root directory
   ```

## Environment Variables

Create a `.env` file in the root directory:

```env
# Email Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Database
DATABASE_URL=sqlite:///prices.db

# Frontend
REACT_APP_API_URL=http://localhost:8000
```

## Architecture

```
Frontend (React) <-> Backend (FastAPI) <-> Database (SQLite)
                              |
                              v
                        Email Service
                              |
                              v
                        Web Scraper
```

## API Endpoints

- `POST /track` - Track a new product
- `POST /alerts` - Set a price alert
- `GET /products/{id}/price-history` - Get price history

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details
