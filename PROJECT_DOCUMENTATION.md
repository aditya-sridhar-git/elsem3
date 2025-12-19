# AI-Powered E-commerce Operations Agent: System Documentation

## 1. Project Overview
This project is an **Autonomous AI Agent System** designed to optimize e-commerce operations. It acts as a super-intelligent "Operations Manager" that monitors your Shopify store 24/7. 

Instead of checking spreadsheets or manually calculating reorder points, this system:
1.  **Analyzes** your entire product catalog using AI.
2.  **Identifies** risks (stockouts) and opportunities (price optimizations).
3.  **Visualizes** actionable insights on a real-time dashboard.
4.  **Executes** actions directly to your Shopify store (restocking, repricing) via an automated loop.

---

## 2. System Architecture
The system consists of four main pillars working in harmony:

### A. The Source of Truth: **Shopify**
*   **Role**: Your live e-commerce store.
*   **Data**: Contains Products, Variants, Inventory Levels, Prices, and Orders.
*   **Interaction**: The system reads from Shopify to get the current state and writes back to Shopify to execute decisions.

### B. The Orchestrator: **n8n (Workflow Automation)**
*   **Role**: The "Schedule Manager" and "Connector".
*   **Function**: 
    *   Runs on a schedule (e.g., every morning).
    *   Fetches raw data from Shopify.
    *   Sends this data to the **AI Backend** for analysis.
    *   Can handle downstream tasks like emailing suppliers or sending PDF reports.

### C. The Brain: **Python Backend (FastAPI + LangChain)**
*   **Role**: The Intelligence Core.
*   **Tech Stack**: Python, FastAPI, Pandas, LangChain, Groq (Llama 3).
*   **Function**:
    *   Receives data from n8n.
    *   Runs the **3-Agent Pipeline** (detailed below) to analyze every SKU.
    *   Serves the API endpoints for the dashboard.
    *   Handles the logic to update Shopify when a user clicks a button.

### D. The Interface: **React Dashboard**
*   **Role**: The Control Center.
*   **Tech Stack**: React, TypeScript, Vite, TailwindCSS.
*   **Function**:
    *   Displays the health of the store (Profitable vs Loss-making SKUs).
    *   Shows a prioritized "Alerts" list of items needing immediate attention.
    *   Allows the human user to "Resolve" issues (Restock/Price Change) with one click.

---

## 3. The "Day in the Life" Workflow
Here is exactly what happens from start to finish when the system runs:

### Step 1: Ingestion (Data Loading)
1.  **Trigger**: The n8n workflow starts (e.g., scheduled or manual trigger).
2.  **Fetch**: n8n requests all **Products** and **Orders** from Shopify.
3.  **Send**: n8n sends this raw JSON data to the Python Backend endpoint: `POST /api/n8n/analyze`.
    *   *Note: The backend waits in a "Listening" state until this data arrives.*

### Step 2: Analysis ( The 3-Agent Pipeline)
Once the backend receives the data, it triggers the Multi-Agent System. The data is passed sequentially through three specialized AI agents:

1.  **Agent 1: The Profit Doctor** 💰
    *   **Goal**: Calculate financial health.
    *   **Logic**: Looks at Selling Price vs. Cost (COGS), Platform Fees, and Ad Spend.
    *   **Output**: Determines `Profit Per Unit`, `Daily Loss`, and categorizes items as "High Margin" or "Loss Maker".

2.  **Agent 2: The Inventory Sentinel** 📦
    *   **Goal**: Prevent stockouts and overstocking.
    *   **Logic**: analyzing Sales Velocity (how fast items sell) vs. Current Stock.
    *   **Output**: Calculates `Days of Stock Left` and assigns a `Risk Level` (CRITICAL, WARNING, SAFE).
    *   *Example: "You have 5 units left, selling 2 per day -> Stockout in 2.5 days -> CRITICAL RISK."*

3.  **Agent 3: The Strategy Supervisor** 🧠
    *   **Goal**: Prioritize and Recommend.
    *   **Logic**: Takes inputs from the previous two agents. It asks: "Is this high-profit item running out of stock?" (High Priority) or "Is this low-profit item doing fine?" (Low Priority).
    *   **Output**: Assigns an `Impact Score` (0-100) and a `Recommended Action` (e.g., "RESTOCK_URGENT", "PRICE_CHANGE", "LIQUIDATE").
    *   **LLM Insight**: It uses **Llama 3 (via Groq)** to generate a human-readable explanation (e.g., *"Profitable hero product risking stockout in 3 days. Restock immediately to avoid ₹5,000 revenue loss."*).

### Step 3: Visualization (The Dashboard)
1.  **Live View**: The React Dashboard polls the backend API.
2.  **Alerts Tab**: The dashboard filters the data to show only **Actionable Alerts** (Critical Risks).
3.  **Insights**: Displays the AI's explanation and the calculated numbers.

### Step 4: Resolution (Closing the Loop)
1.  **User Action**: You see a "Critical Low Stock" alert. You click **"Resolve"** -> **"Restock"**.
2.  **Input**: You enter the quantity (e.g., "50 units").
3.  **Execution**: 
    *   The Dashboard sends this command to the Backend (`POST /api/alerts/action`).
    *   The Backend uses the **Shopify Admin API** to instantly update the inventory level on your real Shopify store.
    *   The Backend updates its local memory so the alert disappears immediately.
4.  **Logging**: The action is logged (`completed_user_actions`), which provides an audit trail.

---

## 4. Key Files & folder Structure

*   **`api.py`**: The main server. Handles APIs, runs the pipeline, and coordinates updates.
*   **`pipeline.py`**: Orchestrates the flow of data through the 3 agents.
*   **`shopify_loader.py`**: A specialized utility to talk to Shopify (Fetch Data / Update Stock / Update Price).
*   **`config.py`**: manages settings and API keys (Shopify Tokens, Groq Keys).
*   **`dashboard/`**: The frontend code (React).
    *   `src/components/AlertsTab.tsx`: The UI for the alerts feed and resolution modals.
    *   `src/services/api.ts`: The bridge between the frontend and the Python backend.

---

## 5. Technology Summary
*   **Backend**: Python 3.10+
*   **Framework**: FastAPI
*   **AI/LLM**: LangChain + Groq (Llama 3.3 70B)
*   **Data Processing**: Pandas (DataFrames)
*   **Frontend**: React + TypeScript + Vite
*   **Styling**: TailwindCSS
*   **Automation**: n8n
