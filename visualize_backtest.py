import matplotlib.pyplot as plt
from simple_broker.models import Candle

# Fonction pour visualiser les résultats du backtest
def visualize_backtest(candles, snapshots):
    timestamps = [candle.timestamp for candle in candles]
    close_prices = [candle.close for candle in candles]
    equity = [snapshot.equity for snapshot in snapshots]

    fig, ax1 = plt.subplots()

    # Tracer les prix de clôture
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Close Price', color='tab:blue')
    ax1.plot(timestamps, close_prices, label='Close Price', color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    # Ajouter une deuxième échelle pour l'équité
    ax2 = ax1.twinx()
    ax2.set_ylabel('Equity', color='tab:green')
    ax2.plot(timestamps, equity, label='Equity', color='tab:green')
    ax2.tick_params(axis='y', labelcolor='tab:green')

    # Ajouter une légende
    fig.tight_layout()
    plt.title('Backtest Results')
    plt.show()

# Exemple d'utilisation
if __name__ == "__main__":
    from run_backtest import candles, snapshots

    visualize_backtest(candles, snapshots)