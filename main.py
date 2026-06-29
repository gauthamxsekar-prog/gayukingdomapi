from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from collections import defaultdict
import json
from pathlib import Path


app = FastAPI(
    title="Gayu + Kingdom",
    description="Gayu + Kingdom is a sample FastAPI application deployed on Vercel. It provides a simple API endpoint that returns sample data in JSON format, along with an interactive Swagger UI for exploring the API.",
    version="1.0.0",
)

# ==================== Data Models ====================
class Stock(BaseModel):
    id: str = None
    name: str
    symbol: str
    sort_order: int = 0
    created_at: str = None

class StockCreateRequest(BaseModel):
    name: str
    symbol: Optional[str] = None

class Trade(BaseModel):
    id: str = None
    stock_id: str
    month: int
    year: int
    c0: str  # date
    c1: Optional[float] = None  # entry price
    c2: Optional[float] = None  # quantity
    c3: bool = False
    c4: Optional[float] = None  # sell price
    c5: Optional[str] = None
    c6: Optional[str] = None
    c7: Optional[str] = None
    c8: Optional[str] = None
    c9: Optional[str] = None
    profit: Optional[float] = None
    loss: Optional[float] = None
    sort_order: int = 0
    created_at: str = None

class TradeCreateRequest(BaseModel):
    stock_id: str
    month: int
    year: int
    c0: str
    c1: Optional[float] = None
    c2: Optional[float] = None
    c3: bool = False
    c4: Optional[float] = None
    c5: Optional[str] = None
    c6: Optional[str] = None
    c7: Optional[str] = None
    c8: Optional[str] = None
    c9: Optional[str] = None
    profit: Optional[float] = None
    loss: Optional[float] = None
    sort_order: int = 0

class TradeUpdateRequest(BaseModel):
    stock_id: Optional[str] = None
    month: Optional[int] = None
    year: Optional[int] = None
    c0: Optional[str] = None
    c1: Optional[float] = None
    c2: Optional[float] = None
    c3: Optional[bool] = None
    c4: Optional[float] = None
    c5: Optional[str] = None
    c6: Optional[str] = None
    c7: Optional[str] = None
    c8: Optional[str] = None
    c9: Optional[str] = None
    profit: Optional[float] = None
    loss: Optional[float] = None
    sort_order: Optional[int] = None

class Column(BaseModel):
    id: str = None
    position: int
    label: str
    col_type: str  # "text", "number", "boolean", "date"
    field: Optional[str] = None
    created_at: str = None

class ColumnCreateRequest(BaseModel):
    position: int
    label: str
    col_type: str
    field: Optional[str] = None

class ColumnUpdateRequest(BaseModel):
    position: Optional[int] = None
    label: Optional[str] = None
    col_type: Optional[str] = None
    field: Optional[str] = None

class ColumnProxyUpdateRequest(BaseModel):
    label: Optional[str] = None
    position: Optional[int] = None

class SummaryResponse(BaseModel):
    invested: float
    profit: float
    loss: float
    net: float

class MonthlySummaryItem(BaseModel):
    month: int
    invested: float
    profit: float
    loss: float
    net: float

# ==================== Data Persistence ====================
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

STOCKS_FILE = DATA_DIR / "stocks.json"
TRADES_FILE = DATA_DIR / "trades.json"
COLUMNS_FILE = DATA_DIR / "columns.json"

# ==================== In-Memory Storage ====================
stocks_db: Dict[str, Stock] = {}
trades_db: Dict[str, Trade] = {}
columns_db: Dict[str, Column] = {}
column_id_counter: int = 0  # Counter for sequential column IDs

# ==================== Persistence Functions ====================
def save_stocks():
    """Save stocks to JSON file"""
    stocks_data = {sid: stock.dict() for sid, stock in stocks_db.items()}
    with open(STOCKS_FILE, "w") as f:
        json.dump(stocks_data, f, indent=2)

def load_stocks():
    """Load stocks from JSON file"""
    global stocks_db
    if STOCKS_FILE.exists():
        with open(STOCKS_FILE, "r") as f:
            stocks_data = json.load(f)
            for sid, stock_dict in stocks_data.items():
                stocks_db[sid] = Stock(**stock_dict)

def save_trades():
    """Save trades to JSON file"""
    trades_data = {tid: trade.dict() for tid, trade in trades_db.items()}
    with open(TRADES_FILE, "w") as f:
        json.dump(trades_data, f, indent=2)

def load_trades():
    """Load trades from JSON file"""
    global trades_db
    if TRADES_FILE.exists():
        with open(TRADES_FILE, "r") as f:
            trades_data = json.load(f)
            for tid, trade_dict in trades_data.items():
                trades_db[tid] = Trade(**trade_dict)

def save_columns():
    """Save columns to JSON file"""
    columns_data = {cid: column.dict() for cid, column in columns_db.items()}
    with open(COLUMNS_FILE, "w") as f:
        json.dump(columns_data, f, indent=2)

def load_columns():
    """Load columns from JSON file"""
    global columns_db, column_id_counter
    if COLUMNS_FILE.exists():
        with open(COLUMNS_FILE, "r") as f:
            columns_data = json.load(f)
            for cid, column_dict in columns_data.items():
                columns_db[cid] = Column(**column_dict)
                # Update counter based on loaded column IDs
                try:
                    col_num = int(cid.split("-")[1])
                    column_id_counter = max(column_id_counter, col_num + 1)
                except:
                    pass

# Initialize default columns
def initialize_default_columns():
    """Initialize default columns on app startup"""
    global column_id_counter
    default_columns = [
        {"label": "Date", "col_type": "date"},
        {"label": "Entry Price", "col_type": "number"},
        {"label": "Quantity", "col_type": "number"},
        {"label": "Sell Price", "col_type": "number"},
        {"label": "Profit", "col_type": "number"},
        {"label": "Loss", "col_type": "number"},
    ]
    
    for idx, col_data in enumerate(default_columns):
        col_id = f"col-{idx}"
        new_column = Column(
            id=col_id,
            position=idx,
            label=col_data["label"],
            col_type=col_data["col_type"],
            field=None,
            created_at=datetime.now().isoformat()
        )
        columns_db[col_id] = new_column
        column_id_counter = idx + 1

@app.on_event("startup")
def startup_event():
    """Initialize on app startup"""
    # Load existing data from files
    load_stocks()
    load_trades()
    load_columns()
    
    # If no columns exist, create defaults
    if not columns_db:
        initialize_default_columns()
        save_columns()

# ==================== Helper Functions ====================
def calculate_profit_loss(entry_price: Optional[float], quantity: Optional[float], sell_price: Optional[float]) -> tuple[Optional[float], Optional[float]]:
    """Calculate profit and loss from trade data"""
    if entry_price is None or quantity is None or sell_price is None:
        return None, None
    
    pl = (sell_price - entry_price) * quantity
    if pl > 0:
        return pl, 0.0
    else:
        return 0.0, abs(pl)

def calculate_invested(entry_price: Optional[float], quantity: Optional[float]) -> Optional[float]:
    """Calculate total invested amount"""
    if entry_price is None or quantity is None:
        return None
    return entry_price * quantity

def get_summary_for_trades(trades: List[Trade]) -> SummaryResponse:
    """Calculate summary statistics from list of trades"""
    total_invested = 0.0
    total_profit = 0.0
    total_loss = 0.0
    
    for trade in trades:
        invested = calculate_invested(trade.c1, trade.c2)
        if invested is not None:
            total_invested += invested
        
        if trade.profit is not None:
            total_profit += trade.profit
        if trade.loss is not None:
            total_loss += trade.loss
    
    net = total_invested + (total_profit - total_loss)
    
    return SummaryResponse(
        invested=round(total_invested, 2),
        profit=round(total_profit, 2),
        loss=round(total_loss, 2),
        net=round(net, 2)
    )

# ==================== Stock Endpoints ====================
@app.post("/api/stocks", response_model=Stock)
def add_stock(stock_data: StockCreateRequest):
    """Add a new stock"""
    stock_id = str(uuid.uuid4())
    new_stock = Stock(
        id=stock_id,
        name=stock_data.name,
        symbol=stock_data.symbol or stock_data.name,
        sort_order=0,
        created_at=datetime.now().isoformat()
    )
    stocks_db[stock_id] = new_stock
    save_stocks()
    return new_stock

@app.get("/api/stocks", response_model=List[Stock])
def get_stocks():
    """Get all stocks"""
    stocks = list(stocks_db.values())
    stocks.sort(key=lambda x: x.sort_order)
    return stocks

@app.delete("/api/stocks/{stock_id}")
def delete_stock(stock_id: str):
    """Delete a stock"""
    if stock_id not in stocks_db:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    deleted_stock = stocks_db.pop(stock_id)
    # Also delete related trades
    trades_to_delete = [tid for tid, trade in trades_db.items() if trade.stock_id == stock_id]
    for tid in trades_to_delete:
        trades_db.pop(tid)
    
    save_stocks()
    save_trades()
    return {"message": f"Stock {deleted_stock.name} deleted successfully", "stock_id": stock_id}

# ==================== Trade Endpoints ====================
@app.post("/api/trades", response_model=Trade)
def add_trade(trade_data: TradeCreateRequest):
    """Add a new trade"""
    trade_id = str(uuid.uuid4())
    
    # Calculate profit and loss if sell price is provided
    profit, loss = calculate_profit_loss(trade_data.c1, trade_data.c2, trade_data.c4)
    
    new_trade = Trade(
        id=trade_id,
        stock_id=trade_data.stock_id,
        month=trade_data.month,
        year=trade_data.year,
        c0=trade_data.c0,
        c1=trade_data.c1,
        c2=trade_data.c2,
        c3=trade_data.c3,
        c4=trade_data.c4,
        c5=trade_data.c5,
        c6=trade_data.c6,
        c7=trade_data.c7,
        c8=trade_data.c8,
        c9=trade_data.c9,
        profit=profit,
        loss=loss,
        sort_order=trade_data.sort_order,
        created_at=datetime.now().isoformat()
    )
    trades_db[trade_id] = new_trade
    save_trades()
    return new_trade

@app.get("/api/trades", response_model=List[Trade])
def get_trades(
    stock_id: Optional[str] = Query(None),
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None)
):
    """Get trades with optional filtering"""
    trades = list(trades_db.values())
    
    if stock_id:
        trades = [t for t in trades if t.stock_id == stock_id]
    if month is not None:
        trades = [t for t in trades if t.month == month]
    if year is not None:
        trades = [t for t in trades if t.year == year]
    
    trades.sort(key=lambda x: x.sort_order)
    return trades

@app.put("/api/trades/{trade_id}", response_model=Trade)
def update_trade(trade_id: str, trade_data: TradeUpdateRequest):
    """Update a trade"""
    if trade_id not in trades_db:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    existing_trade = trades_db[trade_id]
    
    # Update fields
    for field, value in trade_data.dict(exclude_unset=True).items():
        if hasattr(existing_trade, field):
            setattr(existing_trade, field, value)
    
    # Recalculate profit/loss if relevant fields changed
    profit, loss = calculate_profit_loss(existing_trade.c1, existing_trade.c2, existing_trade.c4)
    existing_trade.profit = profit
    existing_trade.loss = loss
    
    save_trades()
    return existing_trade

@app.delete("/api/trades/{trade_id}")
def delete_trade(trade_id: str):
    """Delete a trade"""
    if trade_id not in trades_db:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    deleted_trade = trades_db.pop(trade_id)
    save_trades()
    return {"message": "Trade deleted successfully", "trade_id": trade_id}

# ==================== Column Endpoints ====================
@app.post("/api/columns", response_model=Column)
def add_column(column_data: ColumnCreateRequest):
    """Add a new column"""
    global column_id_counter
    column_id = f"col-{column_id_counter}"
    column_id_counter += 1
    
    new_column = Column(
        id=column_id,
        position=column_data.position,
        label=column_data.label,
        col_type=column_data.col_type,
        field=column_data.field,
        created_at=datetime.now().isoformat()
    )
    columns_db[column_id] = new_column
    save_columns()
    return new_column

@app.get("/api/columns", response_model=List[Column])
def get_columns():
    """Get all columns"""
    columns = list(columns_db.values())
    columns.sort(key=lambda x: x.position)
    return columns

@app.get("/api/columns/{column_id}", response_model=Column)
def get_column(column_id: str):
    """Get a specific column by ID"""
    if column_id not in columns_db:
        raise HTTPException(status_code=404, detail="Column not found")
    return columns_db[column_id]

@app.put("/api/columns/{column_id}", response_model=Column)
def update_column(column_id: str, column_data: ColumnUpdateRequest):
    """Update a column"""
    if column_id not in columns_db:
        raise HTTPException(status_code=404, detail="Column not found")
    
    existing_column = columns_db[column_id]
    
    for field, value in column_data.dict(exclude_unset=True).items():
        if hasattr(existing_column, field):
            setattr(existing_column, field, value)
    
    save_columns()
    return existing_column

@app.delete("/api/columns/{column_id}")
def delete_column(column_id: str):
    """Delete a column"""
    if column_id not in columns_db:
        raise HTTPException(status_code=404, detail="Column not found")
    
    deleted_column = columns_db.pop(column_id)
    save_columns()
    return {"message": "Column deleted successfully", "column_id": column_id}

# ==================== Proxy Column Endpoints ====================
@app.put("/api/proxy/columns/{column_id}", response_model=Column)
def update_column_proxy(column_id: str, column_data: ColumnProxyUpdateRequest):
    """Update a column (proxy endpoint for frontend integration)
    
    Accepts partial updates for label and/or position fields.
    """
    if column_id not in columns_db:
        raise HTTPException(status_code=404, detail="Column not found")
    
    existing_column = columns_db[column_id]
    
    # Update only the provided fields
    if column_data.label is not None:
        existing_column.label = column_data.label
    if column_data.position is not None:
        existing_column.position = column_data.position
    
    save_columns()
    return existing_column

# ==================== Summary Endpoints ====================
@app.get("/api/summary/overall", response_model=SummaryResponse)
def get_overall_summary(
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None)
):
    """Get global aggregated values"""
    trades = list(trades_db.values())
    
    if month is not None:
        trades = [t for t in trades if t.month == month]
    if year is not None:
        trades = [t for t in trades if t.year == year]
    
    return get_summary_for_trades(trades)

@app.get("/api/summary/stock/{stock_id}", response_model=SummaryResponse)
def get_stock_summary(
    stock_id: str,
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None)
):
    """Get summary for a specific stock"""
    trades = [t for t in trades_db.values() if t.stock_id == stock_id]
    
    if month is not None:
        trades = [t for t in trades if t.month == month]
    if year is not None:
        trades = [t for t in trades if t.year == year]
    
    return get_summary_for_trades(trades)

@app.get("/api/summary/monthly", response_model=List[MonthlySummaryItem])
def get_monthly_summary(
    stock_id: Optional[str] = Query(None),
    year: int = Query(...)
):
    """Get monthly breakdowns"""
    trades = list(trades_db.values())
    
    # Filter by stock if provided
    if stock_id:
        trades = [t for t in trades if t.stock_id == stock_id]
    
    # Filter by year
    trades = [t for t in trades if t.year == year]
    
    # Group by month
    monthly_data: Dict[int, List[Trade]] = defaultdict(list)
    for trade in trades:
        monthly_data[trade.month].append(trade)
    
    # Generate summary for each month
    result = []
    for month in sorted(monthly_data.keys()):
        summary = get_summary_for_trades(monthly_data[month])
        result.append(MonthlySummaryItem(
            month=month,
            invested=summary.invested,
            profit=summary.profit,
            loss=summary.loss,
            net=summary.net
        ))
    
    return result

@app.get("/api/users")
def get_sample_data():
    return {
        "data": [
            {"id": 1, "name": "Sample Item 1", "value": 100},
            {"id": 2, "name": "Sample Item 2", "value": 200},
            {"id": 3, "name": "Sample Item 3", "value": 300}
        ],
        "total": 3,
        "timestamp": "2024-01-01T00:00:00Z"
    }


@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gayu Kingdom</title>
        <link rel="icon" type="image/x-icon" href="/favicon.ico">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
                background-color: #000000;
                color: #ffffff;
                line-height: 1.6;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }
            
            header {
                border-bottom: 1px solid #333333;
                padding: 0;
            }
            
            nav {
                max-width: 1200px;
                margin: 0 auto;
                display: flex;
                align-items: center;
                padding: 1rem 2rem;
                gap: 2rem;
            }
            
            .logo {
                font-size: 1.25rem;
                font-weight: 600;
                color: #ffffff;
                text-decoration: none;
            }
            
            .nav-links {
                display: flex;
                gap: 1.5rem;
                margin-left: auto;
            }
            
            .nav-links a {
                text-decoration: none;
                color: #888888;
                padding: 0.5rem 1rem;
                border-radius: 6px;
                transition: all 0.2s ease;
                font-size: 0.875rem;
                font-weight: 500;
            }
            
            .nav-links a:hover {
                color: #ffffff;
                background-color: #111111;
            }
            
            main {
                flex: 1;
                max-width: 1200px;
                margin: 0 auto;
                padding: 4rem 2rem;
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
            }
            
            .hero {
                margin-bottom: 3rem;
            }
            
            .hero-code {
                margin-top: 2rem;
                width: 100%;
                max-width: 900px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            }
            
            .hero-code pre {
                background-color: #0a0a0a;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 1.5rem;
                text-align: left;
                grid-column: 1 / -1;
            }
            
            h1 {
                font-size: 3rem;
                font-weight: 700;
                margin-bottom: 1rem;
                background: linear-gradient(to right, #ffffff, #888888);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .subtitle {
                font-size: 1.25rem;
                color: #888888;
                margin-bottom: 2rem;
                max-width: 600px;
            }
            
            .cards {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1.5rem;
                width: 100%;
                max-width: 900px;
            }
            
            .card {
                background-color: #111111;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 1.5rem;
                transition: all 0.2s ease;
                text-align: left;
            }
            
            .card:hover {
                border-color: #555555;
                transform: translateY(-2px);
            }
            
            .card h3 {
                font-size: 1.125rem;
                font-weight: 600;
                margin-bottom: 0.5rem;
                color: #ffffff;
            }
            
            .card p {
                color: #888888;
                font-size: 0.875rem;
                margin-bottom: 1rem;
            }
            
            .card a {
                display: inline-flex;
                align-items: center;
                color: #ffffff;
                text-decoration: none;
                font-size: 0.875rem;
                font-weight: 500;
                padding: 0.5rem 1rem;
                background-color: #222222;
                border-radius: 6px;
                border: 1px solid #333333;
                transition: all 0.2s ease;
            }
            
            .card a:hover {
                background-color: #333333;
                border-color: #555555;
            }
            
            .status-badge {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                background-color: #0070f3;
                color: #ffffff;
                padding: 0.25rem 0.75rem;
                border-radius: 20px;
                font-size: 0.75rem;
                font-weight: 500;
                margin-bottom: 2rem;
            }
            
            .status-dot {
                width: 6px;
                height: 6px;
                background-color: #00ff88;
                border-radius: 50%;
            }
            
            pre {
                background-color: #0a0a0a;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 1rem;
                overflow-x: auto;
                margin: 0;
            }
            
            code {
                font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
                font-size: 0.85rem;
                line-height: 1.5;
                color: #ffffff;
            }
            
            /* Syntax highlighting */
            .keyword {
                color: #ff79c6;
            }
            
            .string {
                color: #f1fa8c;
            }
            
            .function {
                color: #50fa7b;
            }
            
            .class {
                color: #8be9fd;
            }
            
            .module {
                color: #8be9fd;
            }
            
            .variable {
                color: #f8f8f2;
            }
            
            .decorator {
                color: #ffb86c;
            }
            
            @media (max-width: 768px) {
                nav {
                    padding: 1rem;
                    flex-direction: column;
                    gap: 1rem;
                }
                
                .nav-links {
                    margin-left: 0;
                }
                
                main {
                    padding: 2rem 1rem;
                }
                
                h1 {
                    font-size: 2rem;
                }
                
                .hero-code {
                    grid-template-columns: 1fr;
                }
                
                .cards {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <header>
            <nav>
                <a href="/" class="logo">Gayu Kingdom</a>
                <div class="nav-links">
                    <a href="/docs">API Docs</a>
                    <a href="/api/data">API</a>
                </div>
            </nav>
        </header>
        <main>
            <div class="hero">
                <h1>Gayu Kingdom</h1>
                <div class="hero-code">
                    <pre><code><span class="keyword">from</span> <span class="module">fastapi</span> <span class="keyword">import</span> <span class="class">FastAPI</span>

<span class="variable">app</span> = <span class="class">FastAPI</span>()

<span class="decorator">@app.get</span>(<span class="string">"/"</span>)
<span class="keyword">def</span> <span class="function">read_root</span>():
    <span class="keyword">return</span> {<span class="string">"Python"</span>: <span class="string">"on Vercel"</span>}</code></pre>
                </div>
            </div>
            
            <div class="cards">
                <div class="card">
                    <h3>Interactive API Docs</h3>
                    <p>Explore this API's endpoints with the interactive Swagger UI. Test requests and view response schemas in real-time.</p>
                    <a href="/docs">Open Swagger UI →</a>
                </div>
                
                <div class="card">
                    <h3>Sample Data</h3>
                    <p>Access sample JSON data through our REST API. Perfect for testing and development purposes.</p>
                    <a href="/api/data">Get Data →</a>
                </div>
                
            </div>
        </main>
    </body>
    </html>
    """
