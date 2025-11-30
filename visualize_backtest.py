import matplotlib.pyplot as plt
from simple_broker.models import Candle

# Fonction pour visualiser les résultats du backtest
def visualize_backtest(candles, snapshots):
    timestamps = [candle.timestamp for candle in candles]
    close_prices = [candle.close for candle in candles]
    equity = [snapshot.equity for snapshot in snapshots]

    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 8))

    # Sous-graphe pour les prix de clôture
    ax1.set_title('Prix de Clôture')
    ax1.plot(timestamps, close_prices, label='Prix de Clôture', color='tab:blue')
    ax1.set_ylabel('Prix de Clôture')
    ax1.legend()

    # Sous-graphe pour l'équité
    ax2.set_title('Équité')
    ax2.plot(timestamps, equity, label='Équité', color='tab:green')
    ax2.set_ylabel('Équité')
    ax2.set_xlabel('Temps')
    ax2.legend()

    plt.tight_layout()
    plt.show()

# Exemple d'utilisation
if __name__ == "__main__":
    from run_backtest import candles, snapshots

    visualize_backtest(candles, snapshots)