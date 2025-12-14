from typing import Type, Dict, Any, Optional
from trade_tp.backtest_engine.models.strategy import BaseStrategy
from trade_tp.remote.client import TradeTpClient
from trade_tp.remote.exporters import ResultExporter
from trade_tp.runner import run_backtest

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
    print(f"--- Remote Backtest Job: {run_id} ---")
    
    # 1. Init Client & Fetch Config
    client = TradeTpClient(base_url=base_url, api_key=api_key)
    try:
        config = client.get_backtest_config(run_id)
    except Exception as e:
        raise RuntimeError(f"Impossible de récupérer la configuration: {e}")

    print(f"Configuration chargée: {config.get('symbols')}")

    # 2. Use provided strategy instance
    strategy_instance = strategy

    # 3. Run Backtest
    print("Lancement du backtest...")
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
    print("Envoi des résultats...")
    try:
        exporter = ResultExporter(client)
        
        # Reconstitution des params pour le log
        # On récupère le nom de la classe et ses attributs publics comme paramètres
        strategy_name = strategy_instance.__class__.__name__
        strategy_params = {k: v for k, v in strategy_instance.__dict__.items() if not k.startswith('_')}

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
        print("Succès ! Résultats envoyés.")
    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'envoi des résultats: {e}")

    return results
