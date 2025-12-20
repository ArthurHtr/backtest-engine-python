from typing import Any, Dict, List, Optional
from collections import defaultdict


def compute_summary(
    candles_logs,
    run_id: str,
    symbols: List[str],
    start: str,
    end: str,
    timeframe: str,
    strategy: str,
    initial_cash: float,
    fee_rate: float,
    margin_requirement: float,
    seed: Optional[int] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Aggregate global summary statistics from engine logs.

    This function extracts fees, order counts, equity series, timestamps
    and computes drawdowns and PnL.
    """

    # Empty backtest
    if not candles_logs:
        return {
            "run_id": run_id,
            "symbols": symbols,
            "start": start,
            "end": end,
            "timeframe": timeframe,
            "strategy": strategy,
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

    total_fees = 0.0
    fees_by_symbol: Dict[str, float] = defaultdict(float)
    orders_by_symbol_and_side: Dict[str, Dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )

    equity_series: List[float] = []

    first_timestamp = candles_logs[0].get("timestamp")
    last_timestamp = candles_logs[-1].get("timestamp")

    for log in candles_logs:
        snapshot_after = log["snapshot_after"]
        equity_series.append(snapshot_after.equity)

        for intent in log.get("order_intents", []) or []:
            sym = getattr(intent, "symbol", "UNKNOWN")
            side = str(getattr(intent, "side", "UNKNOWN"))
            orders_by_symbol_and_side[sym][side] += 1
            orders_by_symbol_and_side[sym]["TOTAL"] += 1

        for detail in log.get("execution_details", []) or []:
            trade = detail.get("trade")
            if trade is not None:
                fee = getattr(trade, "fee", 0.0) or 0.0
                total_fees += fee

                sym = getattr(trade, "symbol", None)
                if sym is None:
                    intent = detail.get("intent")
                    if intent is not None:
                        sym = getattr(intent, "symbol", None)

                if sym is not None:
                    fees_by_symbol[sym] += fee

    initial_snapshot = candles_logs[0]["snapshot_before"]
    final_snapshot = candles_logs[-1]["snapshot_after"]

    init_eq = initial_snapshot.equity
    final_eq = final_snapshot.equity
    pnl_abs = final_eq - init_eq
    pnl_pct = (pnl_abs / init_eq * 100.0) if init_eq else 0.0

    max_eq = max(equity_series) if equity_series else init_eq
    min_eq = min(equity_series) if equity_series else init_eq

    max_equity_seen = equity_series[0] if equity_series else init_eq
    max_dd_abs = 0.0
    max_dd_pct = 0.0
    for eq in equity_series:
        if eq > max_equity_seen:
            max_equity_seen = eq
        drawdown = eq - max_equity_seen
        if drawdown < max_dd_abs:
            max_dd_abs = drawdown
            max_dd_pct = (
                (drawdown / max_equity_seen * 100.0) if max_equity_seen else 0.0
            )

    orders_stats_serializable: Dict[str, Dict[str, int]] = {
        sym: dict(sides) for sym, sides in orders_by_symbol_and_side.items()
    }

    summary: Dict[str, Any] = {
        "run_id": run_id,
        "symbols": symbols,
        "start": start,
        "end": end,
        "timeframe": timeframe,
        "strategy": strategy,
        "initial_cash": initial_cash,
        "initial_equity": init_eq,
        "final_cash": final_snapshot.cash,
        "final_equity": final_eq,
        "pnl_abs": pnl_abs,
        "pnl_pct": pnl_pct,
        "max_equity": max_eq,
        "min_equity": min_eq,
        "max_drawdown_abs": max_dd_abs,
        "max_drawdown_pct": max_dd_pct,
        "fee_rate": fee_rate,
        "margin_requirement": margin_requirement,
        "seed": seed,
        "api_mode": "remote" if api_key else "local",
        "base_url": base_url if api_key else None,
        "num_steps": len(candles_logs),
        "total_fees": total_fees,
        "fees_by_symbol": dict(fees_by_symbol),
        "orders_by_symbol_and_side": orders_stats_serializable,
        "first_timestamp": first_timestamp,
        "last_timestamp": last_timestamp,
    }

    return summary
