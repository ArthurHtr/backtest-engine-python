from __future__ import annotations

from typing import Any, Dict, List, Optional
import uuid
from collections import defaultdict

from .data.simulated_market_data.data_provider import DataProvider as SimDataProvider
from .backtest_engine.broker import BacktestBroker
from .engine import BacktestEngine
from .backtest_engine.models.strategy import BaseStrategy
from .remote.client import TradeTpClient

# Delegated analysis & reporting utilities
from .data.backtest_data_analysis.report import logs_visualisation
from .data.backtest_data_analysis.analysis import compute_summary


# (Reporting and aggregation logic moved to `data.backtest_data_analysis`)


# ======================================================================
# Backtest runner
# ======================================================================

def run_backtest(
    symbols: List[str],
    start: str,
    end: str,
    timeframe: str,
    initial_cash: float,
    strategy: BaseStrategy,
    api_key: Optional[str],
    base_url: str,
    fee_rate: float,
    margin_requirement: float,
    save_results: bool = True,
    seed: Optional[int] = None,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function to run a backtest and export a detailed report.

    Returns:
        {
            "candles_logs": ...,
            "summary": ...
        }
    """

    if run_id is None:
        run_id = uuid.uuid4().hex

    client = TradeTpClient(
        base_url=base_url,
        api_key=api_key,
    )

    data_provider = SimDataProvider(
        seed=seed,
        base_price=100.0,
        drift=0.1,
        volatility=0.02,
        base_daily_volume=1_000_000,
    )

    candles_by_symbol = data_provider.get_multiple_candles(
        symbols=symbols,
        start=start,
        end=end,
        timeframe=timeframe,
    )

    broker = BacktestBroker(
        initial_cash=initial_cash,
        fee_rate=fee_rate,
        margin_requirement=margin_requirement,
    )

    engine = BacktestEngine(
        broker=broker,
        strategy=strategy,
        data_provider=data_provider,
    )

    candles_logs = engine.run(candles_by_symbol)

    if not candles_logs:
        # backtest vide : on renvoie un résumé minimal
        summary: Dict[str, Any] = {
            "run_id": run_id,
            "symbols": symbols,
            "start": start,
            "end": end,
            "timeframe": timeframe,
            "strategy": strategy.__class__.__name__,
            "initial_cash": initial_cash,
            "initial_equity": initial_cash,
            "final_cash": initial_cash,
            "final_equity": initial_cash,
            "pnl_abs": 0.0,
            "pnl_pct": 0.0,
            "fee_rate": fee_rate,
            "margin_requirement": margin_requirement,
            "seed": seed,
            "api_mode": "remote" if api_key else "local",
            "base_url": base_url if api_key else None,
            "num_steps": 0,
            "total_fees": 0.0,
            "fees_by_symbol": {},
            "orders_by_symbol_and_side": {},
            "max_equity": initial_cash,
            "min_equity": initial_cash,
            "max_drawdown_abs": 0.0,
            "max_drawdown_pct": 0.0,
            "first_timestamp": None,
            "last_timestamp": None,
        }

        if save_results:
            logs_visualisation(
                candles_logs,
                filepath=f"backtest_analysis/ba_{run_id}.txt",
                summary=summary,
            )

        return {"candles_logs": candles_logs, "summary": summary}

    # --- Agrégation des stats globales (déléguée) ---
    summary = compute_summary(
        candles_logs=candles_logs,
        run_id=run_id,
        symbols=symbols,
        start=start,
        end=end,
        timeframe=timeframe,
        strategy=strategy.__class__.__name__,
        initial_cash=initial_cash,
        fee_rate=fee_rate,
        margin_requirement=margin_requirement,
        seed=seed,
        api_key=api_key,
        base_url=base_url,
    )

    if save_results:
        logs_visualisation(
            candles_logs,
            filepath=f"backtest_analysis/ba_{run_id}.txt",
            summary=summary,
        )

    return {"candles_logs": candles_logs, "summary": summary}
