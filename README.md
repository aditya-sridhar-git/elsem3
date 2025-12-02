# E-commerce Agent Dashboard

Interactive dashboard to visualize AI agents analyzing e-commerce data in real-time.

## Features

- 🎯 **Real-time Agent Monitoring** - Watch Profit Doctor, Inventory Sentinel, and Strategy Supervisor in action
- 📊 **Interactive Charts** - Visualize risk distribution and category-wise profit/loss
- 📈 **Live Metrics** - Track SKUs, profitability, and risk levels
- 🔄 **Auto-refresh** - Data updates every 30 seconds
- 🎨 **Modern UI** - Dark mode with glassmorphism effects

## Tech Stack

**Backend:**
- FastAPI
- Python 3.8+
- Pandas, NumPy

**Frontend:**
- React 18
- TypeScript
- Vite
- Tailwind CSS
- Chart.js

## Quick Start

### 1. Setup Virtual Environment (First Time Only)

```powershell
# Create virtual environment
python -m venv venv

# Activate it (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements-api.txt
```

### 2. Start the API Server

**Option A: Using the convenience script**
```powershell
.\start-api.ps1
```

**Option B: Manual start**
```powershell
.\venv\Scripts\Activate.ps1
python api.py
```

The API will start on `http://localhost:8000`
- API docs: http://localhost:8000/docs

### 3. Install Frontend Dependencies (First Time Only)

```powershell
cd dashboard
npm install
cd ..
```

### 4. Start the Dashboard

**Option A: Using the convenience script**
```powershell
.\start-dashboard.ps1
```

**Option B: Manual start**
```powershell
cd dashboard
npm run dev
```

The dashboard will open at `http://localhost:5173`

## Usage

1. **Start the API** - The backend will automatically run the agent pipeline on startup
2. **Open the Dashboard** - View real-time agent metrics and recommendations
3. **Refresh Data** - Click the refresh button to re-run agents
4. **Explore Insights** - Sort recommendations, view charts, and analyze SKU performance

## Dashboard Sections

### Overview Cards
- Total SKUs processed
- Profitable vs Loss-making products
- Critical risk alerts

### Agent Status
- Profit Doctor metrics
- Inventory Sentinel risk distribution
- Strategy Supervisor action counts

### Analytics Charts
- Risk level distribution (Doughnut chart)
- Profit/Loss by category (Bar chart)

### Recommendations Table
- Sortable columns
- Color-coded risk levels
- Actionable recommendations per SKU

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/agents/status` - Get agent execution status
- `POST /api/agents/run` - Trigger pipeline execution
- `GET /api/metrics/summary` - Get metrics summary
- `GET /api/recommendations` - Get all recommendations
- `GET /api/sku/{sku_id}` - Get SKU details

## Development

### Build for Production

```powershell
cd dashboard
npm run build
```

### Preview Production Build

```powershell
npm run preview
```

## Architecture

```
┌─────────────────┐         ┌──────────────────┐
│  React + TS     │ ◄─HTTP─►│  FastAPI Server  │
│  Dashboard      │         │  (Port 8000)     │
│  (Port 5173)    │         └──────────────────┘
└─────────────────┘                  │
                                     ▼
                            ┌─────────────────┐
                            │  Agent Pipeline │
                            │  - Profit Doctor│
                            │  - Inventory    │
                            │  - Strategy     │
                            └─────────────────┘
```

## Troubleshooting

**API not connecting:**
- Ensure `api.py` is running on port 8000
- Check CORS settings in `api.py`

**Charts not rendering:**
- Clear browser cache
- Check browser console for errors

**Dependencies issues:**
- Delete `node_modules` and run `npm install` again
- For Python, use a virtual environment

## License

MIT
