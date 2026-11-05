import math

class RiskManager:
    """
    Implements institutional-grade capital preservation and position sizing rules.
    Designed specifically to ensure losses are strictly capped and controlled.
    """

    @staticmethod
    def calculate_position(
        account_capital: float,
        risk_per_trade_pct: float,
        entry_price: float,
        stop_loss_price: float
    ) -> dict:
        """
        Calculates exact share quantity such that if the stop loss is triggered,
        the total rupee loss will NOT exceed the planned risk amount.
        """
        if account_capital <= 0 or entry_price <= 0 or stop_loss_price >= entry_price:
            return {
                "valid": False,
                "error": "Invalid input prices. Stop loss must be lower than entry price for a long swing trade."
            }

        # Maximum rupees the trader is allowed to lose on this trade
        max_rupee_risk = account_capital * (risk_per_trade_pct / 100.0)
        
        # Risk per individual share
        risk_per_share = entry_price - stop_loss_price
        risk_pct = (risk_per_share / entry_price) * 100.0

        # Exact number of shares to buy
        suggested_quantity = math.floor(max_rupee_risk / risk_per_share)

        if suggested_quantity <= 0:
            return {
                "valid": False,
                "error": f"Calculated position size is 0 shares. Risk per share (₹{risk_per_share:.2f}) is too wide for ₹{max_rupee_risk:.0f} risk budget."
            }

        total_investment = suggested_quantity * entry_price
        
        # Cap check: Single position shouldn't exceed 25% of account capital to prevent concentration risk
        max_allowed_allocation = account_capital * 0.25
        capped_by_allocation = False

        if total_investment > max_allowed_allocation:
            capped_quantity = math.floor(max_allowed_allocation / entry_price)
            if capped_quantity > 0:
                suggested_quantity = capped_quantity
                total_investment = suggested_quantity * entry_price
                capped_by_allocation = True

        actual_max_loss = suggested_quantity * risk_per_share
        actual_loss_pct_of_capital = (actual_max_loss / account_capital) * 100.0

        return {
            "valid": True,
            "account_capital": account_capital,
            "max_risk_allowed": round(max_rupee_risk, 2),
            "risk_per_share": round(risk_per_share, 2),
            "risk_percentage_on_stock": round(risk_pct, 2),
            "shares_to_buy": int(suggested_quantity),
            "total_capital_required": round(total_investment, 2),
            "capital_allocation_pct": round((total_investment / account_capital) * 100.0, 2),
            "maximum_loss_rupees": round(actual_max_loss, 2),
            "maximum_loss_of_portfolio_pct": round(actual_loss_pct_of_capital, 2),
            "capped_by_concentration_limit": capped_by_allocation
        }

    @staticmethod
    def get_golden_rules() -> list:
        """Core risk management tenets for zero catastrophic loss mindset."""
        return [
            {
                "rule": "1% Rule per Trade",
                "desc": "Never risk more than 1% to 1.5% of total capital on a single swing idea."
            },
            {
                "rule": "Hard Stop-Loss Placed at Order Entry",
                "desc": "Always place a GTT (Good-Till-Triggered) or Stop-Loss-Market order immediately after entering. Never trade with 'mental' stops."
            },
            {
                "rule": "Move Stop to Cost after Target 1 (1:2 RR)",
                "desc": "Once the stock hits Target 1, trail your stop loss to your entry price. This turns the remaining position into a 100% risk-free trade."
            },
            {
                "rule": "Never Average Down on a Losing Swing",
                "desc": "If a setup breaks its technical invalidation level, cut the trade as planned. Averaging down is the #1 cause of catastrophic trading losses."
            },
            {
                "rule": "Maximum 4 to 5 Open Positions",
                "desc": "Keep portfolio exposure diversified. Never put 50%+ of capital into a single sector or stock."
            }
        ]
