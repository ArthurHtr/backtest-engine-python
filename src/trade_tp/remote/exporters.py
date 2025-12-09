from typing import Any, Dict, List, Optional
from .client import TradeTpClient

class ResultExporter:
    """Envoie directement les `candles_logs` (brut) vers l'API distante.

    Le serveur recevra le payload brut `{run_id, params, candles_logs}` et
    pourra effectuer son propre post-traitement/stockage.
    """

    def __init__(self, client: TradeTpClient):
        self.client = client

    def export(self, run_id: Optional[str], params: Dict[str, Any], candles_logs: List[dict]) -> Dict[str, Any]:
        """Envoie le payload complet contenant `candles_logs`.
        """
        payload = {
            "run_id": run_id,
            "params": params,
            "candles_logs": candles_logs,
        }
        return self.client.post_results(payload)