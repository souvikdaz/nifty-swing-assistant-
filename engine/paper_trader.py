import os
import json
import uuid
from datetime import datetime

PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "paper_portfolio.json")

def load_portfolio() -> dict:
    if os.path.exists(PORTFOLIO_FILE):
        try:
            with open(PORTFOLIO_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass

    # Default initial state
    default_state = {
        "initial_capital": 500000.0,
        "cash_balance": 500000.0,
        "open_trades": [],
        "closed_trades": []
    }
    save_portfolio(default_state)
    return default_state

def save_portfolio(portfolio: dict):
    os.makedirs(os.path.dirname(PORTFOLIO_FILE), exist_ok=True)
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2)

def open_paper_trade(symbol: str, name: str, entry_price: float, stop_loss: float, target_1: float, target_2: float, quantity: int) -> dict:
    portfolio = load_portfolio()
    total_cost = entry_price * quantity

    if total_cost > portfolio["cash_balance"]:
        return {
            "success": False,
            "message": f"Insufficient paper cash. Required: ₹{total_cost:,.2f}, Available: ₹{portfolio['cash_balance']:,.2f}"
        }

    trade = {
        "id": str(uuid.uuid4())[:8],
        "symbol": symbol,
        "name": name,
        "entry_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "entry_price": round(entry_price, 2),
        "stop_loss": round(stop_loss, 2),
        "target_1": round(target_1, 2),
        "target_2": round(target_2, 2),
        "quantity": int(quantity),
        "remaining_quantity": int(quantity),
        "cost_basis": round(total_cost, 2),
        "target_1_hit": False,
        "status": "OPEN",
        "current_price": round(entry_price, 2),
        "unrealized_pnl": 0.0,
        "unrealized_pnl_pct": 0.0
    }

    portfolio["cash_balance"] -= total_cost
    portfolio["open_trades"].append(trade)
    save_portfolio(portfolio)
    return {"success": True, "trade": trade}

def close_paper_trade(trade_id: str, exit_price: float, reason: str = "Manual Exit") -> dict:
    portfolio = load_portfolio()
    trade = None
    trade_idx = -1

    for idx, t in enumerate(portfolio["open_trades"]):
        if t["id"] == trade_id:
            trade = t
            trade_idx = idx
            break

    if not trade:
        return {"success": False, "message": "Trade ID not found in open positions."}

    remaining_qty = trade.get("remaining_quantity", trade["quantity"])
    exit_value = exit_price * remaining_qty
    cost_value = trade["entry_price"] * remaining_qty
    realized_pnl = exit_value - cost_value
    pnl_pct = ((exit_price - trade["entry_price"]) / trade["entry_price"]) * 100.0

    trade["exit_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    trade["exit_price"] = round(exit_price, 2)
    trade["exit_reason"] = reason
    trade["realized_pnl"] = round(realized_pnl, 2)
    trade["pnl_pct"] = round(pnl_pct, 2)
    trade["status"] = "CLOSED"

    portfolio["cash_balance"] += exit_value
    portfolio["open_trades"].pop(trade_idx)
    portfolio["closed_trades"].append(trade)
    save_portfolio(portfolio)

    return {"success": True, "closed_trade": trade}

def update_open_trades_with_live_prices(live_prices: dict) -> dict:
    """Updates live P&L and checks for automatic Stop Loss / Target triggers."""
    portfolio = load_portfolio()
    changed = False

    for trade in portfolio["open_trades"]:
        sym = trade["symbol"]
        if sym in live_prices:
            curr_p = float(live_prices[sym])
            trade["current_price"] = round(curr_p, 2)
            rem_qty = trade.get("remaining_quantity", trade["quantity"])
            cost = trade["entry_price"] * rem_qty
            curr_val = curr_p * rem_qty
            trade["unrealized_pnl"] = round(curr_val - cost, 2)
            trade["unrealized_pnl_pct"] = round(((curr_p - trade["entry_price"]) / trade["entry_price"]) * 100.0, 2)
            changed = True

    if changed:
        save_portfolio(portfolio)
    return portfolio

def get_portfolio_metrics(portfolio: dict) -> dict:
    closed = portfolio.get("closed_trades", [])
    open_t = portfolio.get("open_trades", [])

    total_realized_pnl = sum(t.get("realized_pnl", 0.0) for t in closed)
    total_unrealized_pnl = sum(t.get("unrealized_pnl", 0.0) for t in open_t)
    
    total_open_value = sum(t.get("current_price", t["entry_price"]) * t.get("remaining_quantity", t["quantity"]) for t in open_t)
    current_net_worth = portfolio["cash_balance"] + total_open_value

    wins = [t for t in closed if t.get("realized_pnl", 0) > 0]
    losses = [t for t in closed if t.get("realized_pnl", 0) <= 0]
    win_rate = (len(wins) / len(closed) * 100.0) if closed else 0.0

    gross_profit = sum(t.get("realized_pnl", 0) for t in wins)
    gross_loss = abs(sum(t.get("realized_pnl", 0) for t in losses))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (999.0 if gross_profit > 0 else 1.0)

    return {
        "initial_capital": portfolio.get("initial_capital", 500000.0),
        "cash_balance": round(portfolio["cash_balance"], 2),
        "total_open_value": round(total_open_value, 2),
        "current_net_worth": round(current_net_worth, 2),
        "total_realized_pnl": round(total_realized_pnl, 2),
        "total_unrealized_pnl": round(total_unrealized_pnl, 2),
        "total_pnl": round(total_realized_pnl + total_unrealized_pnl, 2),
        "total_pnl_pct": round(((current_net_worth - portfolio.get("initial_capital", 500000.0)) / portfolio.get("initial_capital", 500000.0)) * 100.0, 2),
        "total_closed_trades": len(closed),
        "win_rate": round(win_rate, 1),
        "profit_factor": round(profit_factor, 2),
        "open_trades_count": len(open_t)
    }

def reset_paper_portfolio(initial_amount: float = 500000.0):
    default_state = {
        "initial_capital": initial_amount,
        "cash_balance": initial_amount,
        "open_trades": [],
        "closed_trades": []
    }
    save_portfolio(default_state)
    return default_state
