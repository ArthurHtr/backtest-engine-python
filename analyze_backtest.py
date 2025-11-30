from simple_broker.models import Candle

# Fonction pour analyser les résultats du backtest
# Inclut les détails des ordres et des rejets

def analyze_backtest(candle_logs):
    with open("backtest_analysis.txt", "w") as file:
        file.write("Backtest Analysis\n")
        file.write("================\n\n")

        for i, log in enumerate(candle_logs):
            candles = log.get("candles")
            if candles:
                for symbol, candle in candles.items():
                    file.write(f"Step {i + 1} - Symbol: {symbol}\n")
                    file.write(f"Candle: Time={candle.timestamp}, Open={candle.open}, High={candle.high}, Low={candle.low}, Close={candle.close}, Volume={candle.volume}\n")
            else:
                candle = log["candle"]  # Fallback for single-symbol logs
                file.write(f"Step {i + 1}:\n")
                file.write(f"Candle: Symbol={candle.symbol}, Time={candle.timestamp}, Open={candle.open}, High={candle.high}, Low={candle.low}, Close={candle.close}, Volume={candle.volume}\n")

            snapshot_before = log["snapshot_before"]
            snapshot_after = log["snapshot_after"]
            order_intents = log["order_intents"]
            execution_details = log["execution_details"]

            file.write(f"Portfolio Before: Cash={snapshot_before.cash:.2f}, Equity={snapshot_before.equity:.2f}\n")
            file.write(f"Portfolio After: Cash={snapshot_after.cash:.2f}, Equity={snapshot_after.equity:.2f}\n")

            file.write("Order Intents:\n")
            for intent in order_intents:
                file.write(f"  - Order ID={intent.order_id}, Symbol={intent.symbol}, Side={intent.side}, Quantity={intent.quantity}, Type={intent.order_type}, Limit Price={intent.limit_price}\n")

            file.write("Execution Details:\n")
            for detail in execution_details:
                status = detail["status"]
                reason = detail.get("reason", "N/A")
                trade = detail.get("trade")
                order_id = detail["intent"].order_id  # Retrieve order ID
                file.write(f"  - Order ID={order_id}, Status={status}, Reason={reason}\n")
                if trade:
                    file.write(f"    Trade ID={trade.trade_id}, Quantity={trade.quantity}, Price={trade.price}, Fee={trade.fee}, Timestamp={trade.timestamp}\n")

            file.write("\n")

# Exemple d'utilisation
if __name__ == "__main__":
    from run_backtest import engine

    analyze_backtest(engine.candle_logs)
    print("Backtest analysis written to backtest_analysis.txt")