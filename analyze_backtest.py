from simple_broker.models import Candle

# Fonction pour analyser les résultats du backtest
def analyze_backtest(candles, snapshots):
    with open("backtest_analysis.txt", "w") as file:
        file.write("Backtest Analysis\n")
        file.write("================\n\n")

        for i, (candle, snapshot) in enumerate(zip(candles, snapshots)):
            file.write(f"Step {i + 1}:\n")
            file.write(f"Candle: Symbol={candle.symbol}, Time={candle.timestamp}, Open={candle.open}, High={candle.high}, Low={candle.low}, Close={candle.close}, Volume={candle.volume}\n")
            file.write(f"Portfolio: Cash={snapshot.cash:.2f}, Equity={snapshot.equity:.2f}\n")
            file.write("Positions:\n")
            for position in snapshot.positions:
                file.write(f"  - Symbol={position.symbol}, Side={position.side}, Quantity={position.quantity}, Entry Price={position.entry_price:.2f}, Realized PnL={position.realized_pnl:.2f}\n")
            file.write("\n")

# Exemple d'utilisation
if __name__ == "__main__":
    from run_backtest import candles, snapshots

    analyze_backtest(candles, snapshots)
    print("Backtest analysis written to backtest_analysis.txt")