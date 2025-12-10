# E-commerce Agent Dashboard

Interactive dashboard to visualize AI agents analyzing e-commerce data in real-time.

## Features

- 🎯 **Real-time Agent Monitoring** - Watch Profit Doctor, Inventory Sentinel, and Strategy Supervisor in action
- 📊 **Interactive Charts** - Visualize risk distribution and category-wise profit/loss
- 📈 **Live Metrics** - Track SKUs, profitability, and risk levels
- 🔄 **Auto-refresh** - Data updates every 30 seconds
- 🎨 **Modern UI** - Dark mode with glassmorphism effects
- 🤖 **n8n Automation** - Orchestrate agent workflows with scheduled runs, alerts, and human approvals

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

### n8n Integration Endpoints

- `POST /api/n8n/analyze` - Trigger analysis from n8n workflow
- `POST /api/n8n/log-action` - Log n8n workflow actions
- `POST /api/n8n/workflow-complete` - Mark workflow completion
- `GET /api/n8n/logs` - Get n8n action logs
- `GET /api/n8n/workflow-history` - Get workflow execution history

## 🤖 n8n Automation (Optional)

This project includes **n8n workflow automation** for production deployments.

### What n8n Adds

- ⏰ **Scheduled Execution** - Run agents automatically (daily, hourly, etc.)
- 🔔 **Smart Alerts** - Email/Slack notifications for critical issues
- ✅ **Human Approval** - Approve/reject high-impact actions
- 📝 **Audit Logging** - Track all automated actions
- 🔄 **Shopify Integration** - Fetch real-time store data (optional)

### Quick Setup

1. **Install n8n**
   ```powershell
   # Docker (recommended)
   docker run -it --rm -p 5678:5678 n8nio/n8n
   
   # Or npm
   npm install n8n -g
   n8n start
   ```

2. **Import Workflow**
   - Open n8n at http://localhost:5678
   - Import `n8n_workflow.json`
   - Configure email/Slack credentials

3. **Test**
   - Execute workflow manually
   - Check alerts and logs

📖 **Full Setup Guide**: See [`N8N_SETUP_GUIDE.md`](./N8N_SETUP_GUIDE.md)

### n8n Workflow Architecture

```
Scheduled Trigger (Daily 9 AM)
      ↓
Fetch Data (Shopify/CSV)
      ↓
Send to FastAPI (/api/n8n/analyze)
      ↓
Agents Analyze (Profit Doctor → Inventory Sentinel → Strategy Supervisor)
      ↓
Route by Risk Level (Critical/Warning/Safe)
      ↓
Send Alerts (Email/Slack)
      ↓
Request Approval (for critical actions)
      ↓
Log Actions (/api/n8n/log-action)
      ↓
Complete (/api/n8n/workflow-complete)
```

---

## 🔄 **BIDIRECTIONAL WORKFLOW - USER RESPONSE SYSTEM**

### **✨ NEW FEATURE: Email-Based Actions**

The system now supports **bidirectional communication**! Users can reply to email recommendations with simple commands, and the system automatically executes the actions.

#### **How It Works:**

```
1. System Analyzes → 2. Email Sent → 3. User Replies → 4. Action Executed
         ↓                  ↓               ↓                  ↓
   AI runs daily    "Restock needed?"  APPROVE_RESTOCK   Shopify updated!
```

#### **Email Commands:**

Simply reply to recommendation emails with these keywords:

| Action | Command Format | Example |
|--------|----------------|---------|
| **Approve Restock** | `APPROVE_RESTOCK_{SKU}` | `APPROVE_RESTOCK_IPH001` |
| **Custom Quantity** | `RESTOCK_{SKU}_{QTY}` | `RESTOCK_IPH001_150` |
| **Change Price** | `CHANGE_PRICE_{SKU}_{PRICE}` | `CHANGE_PRICE_IPH001_1250` |
| **Pause Ads** | `PAUSE_ADS_{SKU}` | `PAUSE_ADS_IPH001` |
| **Reject** | `REJECT_{SKU}` | `REJECT_IPH001` |

#### **New API Endpoints:**

- `POST /api/n8n/user-action` - Receive user actions from emails
- `GET /api/user-actions/pending` - Get pending user actions
- `GET /api/user-actions/completed` - Get completed actions
- `GET /api/user-actions/history` - Get full action history

#### **New Dashboard View:**

Access the actions panel at: **http://localhost:5173/actions**

Features:
- ✅ View pending actions (awaiting execution)
- ✅ View completed actions with details
- ✅ Real-time updates (auto-refreshes every 30 seconds)
- ✅ Filter by SKU
- ✅ Complete audit trail

#### **Quick Setup:**

```powershell
# 1. Import new workflow to n8n
# Open n8n → Import from File → Select "User-Response-Handler-Workflow.json"

# 2. Update existing workflow with new email templates
# Copy templates from: EMAIL_TEMPLATES_BIDIRECTIONAL.md

# 3. Activate both workflows in n8n
# Toggle the switch to activate

# 4. Test the system
# See SETUP_GUIDE_BIDIRECTIONAL.md for testing instructions
```



#### **What You Get:**

✅ **Email-based approvals** - No login required, just reply  
✅ **Automatic execution** - System updates Shopify automatically  
✅ **Real-time tracking** - Dashboard shows all actions  
✅ **Confirmation emails** - Know when actions complete  
✅ **Complete audit trail** - Every action logged  
✅ **Time savings** - ~20 hours/month automation  

---

## 📊 Complete Feature List

### **Core AI Agents:**
- 🧠 **Profit Doctor** - Profitability analysis
- 📦 **Inventory Sentinel** - Stock risk assessment
- 🎯 **Strategy Supervisor** - Action recommendations

### **n8n Workflows:**
- ⏰ **Daily Analysis** - Scheduled execution at 9 AM
- 📧 **Smart Alerts** - Email notifications for critical issues
- 🔄 **User Response Handler** - Process email replies (NEW!)
- ✅ **Action Execution** - Automatic Shopify updates (NEW!)

### **Dashboard Views:**
- 📊 **Main Dashboard** - Metrics, charts, recommendations
- 🎯 **Actions Panel** - Pending/completed user actions (NEW!)
- 🤖 **Agent Status** - Real-time agent monitoring
- 📈 **Analytics** - Risk distribution & profit analysis

### **Integrations:**
- 🛍️ **Shopify** - Products, inventory, orders
- 📧 **Gmail** - Email notifications & responses
- 🤖 **LangChain + Groq AI** - Intelligent insights
- 🔔 **Slack** - Team notifications (optional)

---


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
