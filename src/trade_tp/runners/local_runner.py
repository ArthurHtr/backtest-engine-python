from typing import Any, Dict, List, Optional
import uuid
import os

from trade_tp.remote.provider import RemoteDataProvider
from trade_tp.backtest_engine.broker import BacktestBroker
from trade_tp.backtest_engine.engine import BacktestEngine
from trade_tp.backtest_engine.strategy.base import BaseStrategy
from trade_tp.remote.client import TradeTpClient
from trade_tp.backtest_engine.analysis.report import export_backtest_analysis
from trade_tp.backtest_engine.analysis.metrics import compute_summary

def run_local_backtest(
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
    verbose: bool = True,
    # Optional pre-fetched data to avoid API calls
    candles_by_symbol: Optional[Dict[str, List[Any]]] = None,
    symbols_map: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Exécute un backtest localement en utilisant des données distantes.
    """

    if run_id is None:
        run_id = uuid.uuid4().hex

    # If data is not provided, we need api_key to fetch it
    if (candles_by_symbol is None or symbols_map is None) and not api_key:
        raise ValueError("api_key is required for remote backtest if data is not provided.")

    if candles_by_symbol is None or symbols_map is None:
        client = TradeTpClient(
            base_url=base_url,
            api_key=api_key,
        )
        # Use remote data provider
        data_provider = RemoteDataProvider(client)

        if symbols_map is None:
            # Fetch symbol info
            symbol_objects = data_provider.get_symbols(symbols)
            symbols_map = {s.symbol: s for s in symbol_objects}

        if candles_by_symbol is None:
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
        symbols_map=symbols_map,
    )

    engine = BacktestEngine(
        broker=broker,
        strategy=strategy,
        verbose=verbose,
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
            "api_mode": "remote",
            "base_url": base_url,
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
            output_dir = "backtest_analysis"
            os.makedirs(output_dir, exist_ok=True)
            export_backtest_analysis(
                candles_logs,
                run_id=run_id,
                base_dir=output_dir,
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
        output_dir = "backtest_analysis"
        os.makedirs(output_dir, exist_ok=True)
        export_backtest_analysis(
            candles_logs,
            run_id=run_id,
            base_dir=output_dir,
            summary=summary,
        )

    return {"candles_logs": candles_logs, "summary": summary}
