from simple_broker.models import Candle, OrderIntent, Trade, Side, PositionSide
from simple_broker.portfolio import PortfolioState

class BacktestBroker:
    """
    Simulates a broker for backtesting, supporting long and short positions.
    """
    def __init__(self, initial_cash: float, fee_rate: float):
        self.portfolio = PortfolioState(initial_cash)
        self.fee_rate = fee_rate
        self.margin_requirement = 0.5  # 50% margin requirement for short positions

    def get_snapshot(self, candle: Candle):
        """
        Returns a snapshot of the portfolio before processing orders.
        """
        return self.portfolio.build_snapshot({candle.symbol: candle.close}, candle.timestamp)

    def process_bar(self, candle: Candle, order_intents: list[OrderIntent]):
        """
        Processes a single bar (candle) and executes the given order intents.
        Tracks reasons for order rejections.
        """
        execution_details = []  # Track execution and rejection details

        for intent in order_intents:
            if intent.order_type == "MARKET":
                price = candle.close
                fee = abs(intent.quantity * price) * self.fee_rate
                total_cost = abs(intent.quantity * price) + fee

                if intent.side == Side.BUY:
                    if intent.symbol in self.portfolio.positions:
                        position = self.portfolio.positions[intent.symbol]
                        if position.side == PositionSide.SHORT:
                            if abs(position.quantity) < intent.quantity:
                                execution_details.append({
                                    "intent": intent,
                                    "status": "rejected",
                                    "reason": "Insufficient short quantity to cover."
                                })
                                continue
                    if self.portfolio.cash < total_cost:
                        execution_details.append({
                            "intent": intent,
                            "status": "rejected",
                            "reason": "Insufficient cash."
                        })
                        continue

                elif intent.side == Side.SELL:
                    if intent.symbol in self.portfolio.positions:
                        position = self.portfolio.positions[intent.symbol]
                        if position.side == PositionSide.LONG:
                            if position.quantity < abs(intent.quantity):
                                execution_details.append({
                                    "intent": intent,
                                    "status": "rejected",
                                    "reason": "Insufficient long quantity to sell."
                                })
                                continue

                    required_margin = abs(intent.quantity * price) * self.margin_requirement
                    equity = self.portfolio.cash
                    for pos in self.portfolio.positions.values():
                        current_price = candle.close
                        unrealized_pnl = (
                            (current_price - pos.entry_price) * pos.quantity
                            if pos.side == PositionSide.LONG
                            else (pos.entry_price - current_price) * abs(pos.quantity)
                        )
                        equity += unrealized_pnl

                    if equity < required_margin:
                        execution_details.append({
                            "intent": intent,
                            "status": "rejected",
                            "reason": "Insufficient margin."
                        })
                        continue

                trade_quantity = intent.quantity if intent.side == Side.BUY else -intent.quantity
                trade = Trade(
                    symbol=intent.symbol,
                    quantity=trade_quantity,
                    price=price,
                    fee=fee,
                    timestamp=candle.timestamp
                )
                self.portfolio.apply_trade(trade)
                execution_details.append({
                    "intent": intent,
                    "status": "executed",
                    "trade": trade
                })

        return self.portfolio.build_snapshot({candle.symbol: candle.close}, candle.timestamp), execution_details
