import os
import csv
from typing import Any, Dict, List, Optional
from trade_tp.backtest_engine.analysis.report_utils import (
    write_line,
    write_header,
    write_summary_header,
    write_global_portfolio_section,
    write_per_symbol_table
)

def export_backtest_analysis(
    candles_logs: List[Dict[str, Any]], 
    run_id: str, 
    base_dir: str = "backtest_analysis", 
    summary: Optional[Dict[str, Any]] = None
) -> None:
    """
    Export a structured backtest analysis to a dedicated folder.
    
    Structure:
    backtest_analysis/
        <run_id>/
            summary.txt
            full_log.txt
            trades.csv
            equity.csv
    """
    
    # Create directory
    run_dir = os.path.join(base_dir, run_id)
    os.makedirs(run_dir, exist_ok=True)
    
    # 1. Summary File
    _write_summary_file(os.path.join(run_dir, "summary.txt"), summary)
    
    # 2. Full Log File
    _write_full_log_file(os.path.join(run_dir, "full_log.txt"), candles_logs)
    
    # 3. Trades CSV
    _write_trades_csv(os.path.join(run_dir, "trades.csv"), candles_logs)
    
    # 4. Equity CSV
    _write_equity_csv(os.path.join(run_dir, "equity.csv"), candles_logs)

    # 5. Order Intents CSV
    _write_order_intents_csv(os.path.join(run_dir, "order_intents.csv"), candles_logs)



def _write_summary_file(filepath: str, summary: Optional[Dict[str, Any]]) -> None:
    with open(filepath, "w") as file:
        write_header(file, "Backtest Summary")
        write_line(file)
        
        if summary:
            write_summary_header(file, summary)
            write_global_portfolio_section(file, summary)
            write_per_symbol_table(file, summary)
        else:
            write_line(file, "No summary available.")

def _write_full_log_file(filepath: str, candles_logs: List[Dict[str, Any]]) -> None:
    with open(filepath, "w") as file:
        write_header(file, "Detailed Backtest Logs")
        
        for step_idx, log in enumerate(candles_logs, start=1):
            candles = log.get("candles")
            snapshot_before = log["snapshot_before"]
            timestamp = log.get("timestamp")

            if timestamp:
                write_line(file, f"Step {step_idx} - Timestamp: {timestamp}")
            else:
                write_line(file, f"Step {step_idx}")

            write_line(file, "-" * 80)

            if candles:
                write_line(file, "Candles:")
                for symbol, candle in candles.items():
                    write_line(
                        file,
                        (
                            f"  {symbol}: "
                            f"O={candle.open:.2f}, "
                            f"H={candle.high:.2f}, "
                            f"L={candle.low:.2f}, "
                            f"C={candle.close:.2f}, "
                            f"V={candle.volume}"
                        ),
                    )
            else:
                candle = log.get("candle")
                if candle is not None:
                    write_line(file, "Candle:")
                    write_line(
                        file,
                        (
                            f"  {candle.symbol}: "
                            f"O={candle.open:.2f}, "
                            f"H={candle.high:.2f}, "
                            f"L={candle.low:.2f}, "
                            f"C={candle.close:.2f}, "
                            f"V={candle.volume}"
                        ),
                    )

            write_line(file)

            write_line(file, "Portfolio Before:")
            write_line(file, f"  Cash:   {snapshot_before.cash:,.2f}")
            write_line(file, f"  Equity: {snapshot_before.equity:,.2f}")
            if hasattr(snapshot_before, 'unrealized_pnl'):
                write_line(file, f"  Unrealized PnL: {snapshot_before.unrealized_pnl:,.2f}")
            if hasattr(snapshot_before, 'total_realized_pnl'):
                net_realized = snapshot_before.total_realized_pnl - snapshot_before.total_fees
                write_line(file, f"  Total Realized PnL (Gross): {snapshot_before.total_realized_pnl:,.2f}")
                write_line(file, f"  Total Fees:                 {snapshot_before.total_fees:,.2f}")
                write_line(file, f"  Net Realized PnL:           {net_realized:,.2f}")

            positions_before = snapshot_before.summarize_positions()
            if positions_before:
                write_line(file, "  Positions:")
                for symbol, details in positions_before.items():
                    write_line(
                        file,
                        (
                            f"    {symbol}: "
                            f"Side={details['side']}, "
                            f"Qty={details['quantity']}, "
                            f"Entry={details['entry_price']:.2f}"
                        ),
                    )
            else:
                write_line(file, "  Positions: (none)")
            
            # Order Intents
            order_intents = log.get("order_intents", [])
            if order_intents:
                write_line(file)
                write_line(file, "  Order Intents:")
                for intent in order_intents:
                    price_display = f"{intent.limit_price:.2f}" if intent.limit_price else "MARKET"
                    write_line(file, f"    {intent.side} {intent.quantity} {intent.symbol} @ {price_display}")

            # Execution Details
            execution_details = log.get("execution_details", [])
            if execution_details:
                write_line(file)
                write_line(file, "  Executions:")
                for detail in execution_details:
                    trade = detail.get("trade")
                    if trade:
                        side = "BUY" if trade.quantity > 0 else "SELL"
                        qty = abs(trade.quantity)
                        write_line(file, f"    TRADE: {side} {qty} {trade.symbol} @ {trade.price:.2f} (Fee: {trade.fee:.2f})")
                    else:
                        # Rejected or other status
                        intent = detail.get("intent")
                        status = detail.get("status")
                        reason = detail.get("reason")
                        if intent:
                            write_line(file, f"    {status}: {intent.side} {intent.quantity} {intent.symbol} - {reason}")
                        else:
                            write_line(file, f"    {status}: {reason}")

            # Portfolio After
            snapshot_after = log.get("snapshot_after")
            if snapshot_after:
                write_line(file)
                write_line(file, "Portfolio After:")
                write_line(file, f"  Cash:   {snapshot_after.cash:,.2f}")
                write_line(file, f"  Equity: {snapshot_after.equity:,.2f}")
                positions_after = snapshot_after.summarize_positions()
                if positions_after:
                    write_line(file, "  Positions:")
                    for symbol, details in positions_after.items():
                        write_line(
                            file,
                            (
                                f"    {symbol}: "
                                f"Side={details['side']}, "
                                f"Qty={details['quantity']}, "
                                f"Entry={details['entry_price']:.2f}"
                            ),
                        )
                else:
                    write_line(file, "  Positions: (none)")

            write_line(file)

def _write_trades_csv(filepath: str, candles_logs: List[Dict[str, Any]]) -> None:
    trades = []
    for log in candles_logs:
        timestamp = log.get("timestamp")
        for detail in log.get("execution_details", []) or []:
            trade = detail.get("trade")
            if trade:
                side = "BUY" if trade.quantity > 0 else "SELL"
                qty = abs(trade.quantity)
                cost = qty * trade.price
                trades.append({
                    "timestamp": timestamp,
                    "symbol": trade.symbol,
                    "side": side,
                    "quantity": qty,
                    "price": trade.price,
                    "fee": trade.fee,
                    "cost": cost,
                    "value": cost
                })
                
    if not trades:
        return

    with open(filepath, "w", newline='') as csvfile:
        fieldnames = ["timestamp", "symbol", "side", "quantity", "price", "fee", "cost", "value"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for trade in trades:
            writer.writerow(trade)

def _write_equity_csv(filepath: str, candles_logs: List[Dict[str, Any]]) -> None:
    with open(filepath, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "equity", "cash", "unrealized_pnl", "realized_pnl", "fees"])
        
        for log in candles_logs:
            ts = log.get("timestamp")
            snap = log["snapshot_after"]
            
            unrealized = getattr(snap, 'unrealized_pnl', 0.0)
            realized = getattr(snap, 'total_realized_pnl', 0.0)
            fees = getattr(snap, 'total_fees', 0.0)
            
            writer.writerow([ts, snap.equity, snap.cash, unrealized, realized, fees])

def _write_order_intents_csv(filepath: str, candles_logs: List[Dict[str, Any]]) -> None:
    intents_data = []
    for log in candles_logs:
        timestamp = log.get("timestamp")
        
        # Map intents to their execution result if possible
        # This is tricky because execution_details is a list, and order_intents is a list.
        # Assuming 1-to-1 mapping or we just list all intents and their potential outcome if found.
        # A simpler approach is to iterate execution_details which contains the intent + result.
        
        execution_details = log.get("execution_details", [])
        for detail in execution_details:
            intent = detail.get("intent")
            if intent:
                status = detail.get("status", "UNKNOWN")
                reason = detail.get("reason", "")
                trade = detail.get("trade")
                
                executed_price = trade.price if trade else None
                executed_qty = trade.quantity if trade else None
                fee = trade.fee if trade else 0.0
                
                intents_data.append({
                    "timestamp": timestamp,
                    "symbol": intent.symbol,
                    "side": intent.side,
                    "quantity": intent.quantity,
                    "order_price": intent.limit_price, # Requested price
                    "status": status,
                    "reason": reason,
                    "executed_price": executed_price,
                    "executed_qty": executed_qty,
                    "fee": fee
                })

    if not intents_data:
        return

    with open(filepath, "w", newline='') as csvfile:
        fieldnames = ["timestamp", "symbol", "side", "quantity", "order_price", "status", "reason", "executed_price", "executed_qty", "fee"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for data in intents_data:
            writer.writerow(data)
