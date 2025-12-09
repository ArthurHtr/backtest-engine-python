from typing import Any, Dict, List, Optional
import requests

class TradeTpClient:
    """Client HTTP pour l'API distante avec auth Bearer."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def _full_url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def get_symbols(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Récupère la liste des symboles supportés."""
        params = {"symbols": ",".join(symbols)} if symbols else None
        resp = self.session.get(self._full_url("/symbols"), params=params, timeout=self.timeout)
        if not resp.ok:
            raise RuntimeError(f"Failed to fetch symbols: {resp.status_code} {resp.text}")
        return resp.json() or []

    def get_candles(self, symbols: List[str], start: str, end: str) -> Dict[str, List[Dict[str, Any]]]:
        """Récupère les candles pour les symboles et période donnés."""
        payload = {"symbols": symbols, "start": start, "end": end}
        resp = self.session.post(self._full_url("/candles"), json=payload, timeout=self.timeout)
        if not resp.ok:
            raise RuntimeError(f"Failed to fetch candles: {resp.status_code} {resp.text}")
        return resp.json() or {}

    def post_results(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Envoie les résultats du backtest à l'API."""
        resp = self.session.post(self._full_url("/backtests"), json=payload, timeout=self.timeout)
        if not resp.ok:
            raise RuntimeError(f"Failed to export results: {resp.status_code} {resp.text}")
        return resp.json() or {}