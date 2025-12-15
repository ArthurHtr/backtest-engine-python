from __future__ import annotations
from typing import Any, Dict, List, Optional
import uuid
import os

from trade_tp.remote.importers import RemoteDataProvider
from trade_tp.backtest_engine.broker import BacktestBroker
from trade_tp.engine import BacktestEngine
from trade_tp.backtest_engine.models.strategy import BaseStrategy
from trade_tp.remote.client import TradeTpClient
from trade_tp.remote.exporters import ResultExporter

from trade_tp.data.backtest_data_analysis.report import logs_visualisation
from trade_tp.data.backtest_data_analysis.analysis import compute_summary


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

    if not api_key:
        raise ValueError("api_key is required for remote backtest. Local simulation is no longer supported.")

    client = TradeTpClient(
        base_url=base_url,
        api_key=api_key,
    )

    # Use remote data provider
    data_provider = RemoteDataProvider(client)

    # Fetch symbol info
    symbol_objects = data_provider.get_symbols(symbols)
    symbols_map = {s.symbol: s for s in symbol_objects}

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
            logs_visualisation(
                candles_logs,
                filepath=f"{output_dir}/ba_{run_id}.txt",
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
        logs_visualisation(
            candles_logs,
            filepath=f"{output_dir}/bt_{run_id}.txt",
            summary=summary,
        )

    return {"candles_logs": candles_logs, "summary": summary}


def run_remote_backtest_job(
    run_id: str,
    api_key: str,
    strategy: BaseStrategy,
    base_url: str = "http://localhost:3000/api",
    save_local: bool = False
) -> Dict[str, Any]:
    """
    Exécute un backtest configuré à distance.
    
    1. Récupère la configuration depuis l'API (via run_id).
    2. Utilise l'instance de stratégie fournie.
    3. Lance le backtest (téléchargement des données inclus).
    4. Envoie les résultats à l'API.
    """
    
    # 1. Init Client & Fetch Config
    client = TradeTpClient(base_url=base_url, api_key=api_key)
    try:
        config = client.get_backtest_config(run_id)
    except Exception as e:
        raise RuntimeError(f"Impossible de récupérer la configuration: {e}")

    # 2. Use provided strategy instance
    strategy_instance = strategy

    # 3. Run Backtest
    try:
        # run_backtest va utiliser api_key/base_url pour fetcher les candles via le DataProvider
        results = run_backtest(
            symbols=config['symbols'],
            start=config['start'],
            end=config['end'],
            timeframe=config['timeframe'],
            initial_cash=float(config['initialCash']),
            strategy=strategy_instance,
            api_key=api_key,
            base_url=base_url,
            fee_rate=float(config['feeRate']),
            margin_requirement=float(config['marginRequirement']),
            save_results=save_local,
            seed=config.get('seed'),
            run_id=run_id
        )
    except Exception as e:
        raise RuntimeError(f"Erreur pendant l'exécution du backtest: {e}")

    # 4. Upload Results
    try:
        exporter = ResultExporter(client)
        
        # Reconstitution des params pour le log
        # On récupère le nom de la classe et ses attributs publics comme paramètres
        strategy_name = strategy_instance.__class__.__name__
        # Filter out internal state variables like 'prices' or large objects
        strategy_params = {
            k: v for k, v in strategy_instance.__dict__.items() 
            if not k.startswith('_') and k != 'prices'
        }

        params_for_export = {
            "symbols": config['symbols'],
            "start": config['start'],
            "end": config['end'],
            "timeframe": config['timeframe'],
            "initial_cash": config['initialCash'],
            "strategy": strategy_name,
            "strategy_params": strategy_params
        }
        
        exporter.export(
            run_id=run_id, 
            params=params_for_export, 
            candles_logs=results['candles_logs']
        )
    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'envoi des résultats: {e}")

    return results
