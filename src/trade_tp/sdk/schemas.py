# Schemas for backtest configurations and results

class BacktestConfig:
    def __init__(self, strategy, start_date, end_date):
        self.strategy = strategy
        self.start_date = start_date
        self.end_date = end_date

class BacktestResult:
    def __init__(self, performance, trades):
        self.performance = performance
        self.trades = trades