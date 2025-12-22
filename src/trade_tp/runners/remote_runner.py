from typing import Any, Dict
from trade_tp.backtest_engine.strategy.base import BaseStrategy
from trade_tp.remote.client import TradeTpClient
from trade_tp.remote.exporter import ResultExporter
from trade_tp.runners.local_runner import run_local_backtest

def run_remote_backtest(
    run_id: str,
    api_key: str,
    strategy: BaseStrategy,
    base_url: str,
    save_local: bool = False,
    export_to_server: bool = True,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Exécute un backtest configuré à distance.
    
    1. Récupère la configuration depuis l'API (via run_id).
    2. Utilise l'instance de stratégie fournie.
    3. Lance le backtest (téléchargement des données inclus).
    4. Envoie les résultats à l'API (si export_to_server=True).
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
        results = run_local_backtest(
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
            run_id=run_id,
            verbose=verbose
        )
    except Exception as e:
        raise RuntimeError(f"Erreur pendant l'exécution du backtest: {e}")

    # 4. Upload Results
    if export_to_server:
        try:
            exporter = ResultExporter(client)
            
            # Reconstitution des params pour le log
            strategy_name = strategy_instance.__class__.__name__
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

    # 5. Compute & Attach Quick Metrics
    total_trades = sum(
        1 for log in results['candles_logs']
        for detail in log.get("execution_details", []) or []
        if detail.get("trade")
    )

    results['metrics'] = {
        "total_return": results['summary']['pnl_pct'],
        "final_equity": results['summary']['final_equity'],
        "total_fees": results['summary']['total_fees'],
        "total_trades": total_trades
    }

    return results
