from simple_broker.models import Candle

# Fonction pour analyser les résultats du backtest
# Inclut les détails des ordres et des rejets

def analyze_backtest(candle_logs):
    with open("backtest_analysis.txt", "w") as file:
        file.write("Backtest Analysis\n")
        file.write("================\n\n")

        for i, log in enumerate(candle_logs):
            candle = log["candle"]
            snapshot_before = log["snapshot_before"]
            snapshot_after = log["snapshot_after"]
            order_intents = log["order_intents"]
            execution_details = log["execution_details"]

            file.write(f"Step {i + 1}:\n")
            file.write(f"Candle: Symbol={candle.symbol}, Time={candle.timestamp}, Open={candle.open}, High={candle.high}, Low={candle.low}, Close={candle.close}, Volume={candle.volume}\n")
            file.write(f"Portfolio Before: Cash={snapshot_before.cash:.2f}, Equity={snapshot_before.equity:.2f}\n")
            file.write(f"Portfolio After: Cash={snapshot_after.cash:.2f}, Equity={snapshot_after.equity:.2f}\n")

            file.write("Order Intents:\n")
            for intent in order_intents:
                file.write(f"  - Symbol={intent.symbol}, Side={intent.side}, Quantity={intent.quantity}, Type={intent.order_type}, Limit Price={intent.limit_price}\n")

            file.write("Execution Details:\n")
            for detail in execution_details:
                status = detail["status"]
                reason = detail.get("reason", "N/A")
                trade = detail.get("trade")
                file.write(f"  - Intent: Symbol={detail['intent'].symbol}, Status={status}, Reason={reason}\n")
                if trade:
                    file.write(f"    Trade: Quantity={trade.quantity}, Price={trade.price}, Fee={trade.fee}, Timestamp={trade.timestamp}\n")

            file.write("\n")

# Exemple d'utilisation
if __name__ == "__main__":
    from run_backtest import engine

    analyze_backtest(engine.candle_logs)
    print("Backtest analysis written to backtest_analysis.txt")