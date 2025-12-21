from typing import Any, Dict, List, Optional
import requests

class TradeTpClient:
    """Client HTTP pour l'API distante avec auth Bearer."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 60.0):
        base_url = base_url.rstrip("/")
        self.base_url = base_url + "/api"
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"x-api-key": self.api_key})

    def _full_url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _check_response(self, resp: requests.Response, context: str):
        if resp.status_code == 401:
            raise PermissionError(f"Invalid API Key during {context}. Please check your API key.")
        if not resp.ok:
            raise RuntimeError(f"Failed to {context}: {resp.status_code} {resp.text}")

    def get_symbols(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Récupère la liste des symboles supportés."""
        params = {"symbols": ",".join(symbols)} if symbols else None
        resp = self.session.get(self._full_url("/symbols"), params=params, timeout=self.timeout)
        self._check_response(resp, "fetch symbols")
        return resp.json() or []

    def get_candles(self, symbols: List[str], start: str, end: str, timeframe: str = "1d") -> Dict[str, List[Dict[str, Any]]]:
        """Récupère les candles pour les symboles et période donnés."""
        payload = {"symbols": symbols, "start": start, "end": end, "timeframe": timeframe}
        resp = self.session.post(self._full_url("/candles"), json=payload, timeout=self.timeout)
        self._check_response(resp, "fetch candles")
        return resp.json() or {}

    def get_backtest_config(self, run_id: str) -> Dict[str, Any]:
        """Récupère la configuration d'un backtest."""
        resp = self.session.get(self._full_url(f"/backtests/{run_id}"), timeout=self.timeout)
        self._check_response(resp, "fetch backtest config")
        return resp.json()

    def post_results(self, run_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Envoie les résultats du backtest à l'API."""
        resp = self.session.post(self._full_url(f"/backtests/{run_id}/results"), json=payload, timeout=self.timeout)
        self._check_response(resp, "export results")
        return resp.json() or {}