from typing import Any, Dict, List, Optional
from trade_tp.data.backtest_data_analysis.utils.write_line import write_line
from trade_tp.data.backtest_data_analysis.utils.write_header import _write_header
from trade_tp.data.backtest_data_analysis.utils.write_summary_header import _write_summary_header
from trade_tp.data.backtest_data_analysis.utils.write_global_portfolio_section import _write_global_portfolio_section
from trade_tp.data.backtest_data_analysis.utils.write_per_symbol_table import _write_per_symbol_table

def logs_visualisation(candles_logs, filepath: str = "backtest_analysis.txt", summary: Optional[Dict[str, Any]] = None) -> None:
    """Export a human-readable backtest analysis to `filepath`."""

    with open(filepath, "w") as file:
        _write_header(file, "Backtest Analysis")
        write_line(file)

        if summary is not None:
            _write_summary_header(file, summary)
            _write_global_portfolio_section(file, summary)
            _write_per_symbol_table(file, summary)
            write_line(file)
            write_line(file)

        _write_header(file, "Backtest Details")

        for step_idx, log in enumerate(candles_logs, start=1):
            candles = log.get("candles")
            snapshot_before = log["snapshot_before"]
            snapshot_after = log["snapshot_after"]
            order_intents = log["order_intents"]
            execution_details = log["execution_details"]
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
                # Affichage du Net PnL (Realized - Fees) pour plus de clarté
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

            write_line(file)

            write_line(file, "Order Intents:")
            if order_intents:
                for intent in order_intents:
                    write_line(
                        file,
                        (
                            "  - "
                            f"OrderID={intent.order_id}, "
                            f"Symbol={intent.symbol}, "
                            f"Side={intent.side}, "
                            f"Qty={intent.quantity}, "
                            f"Type={intent.order_type}, "
                            f"Limit={intent.limit_price}"
                        ),
                    )
            else:
                write_line(file, "  (none)")

            write_line(file)

            write_line(file, "Execution Details:")
            if execution_details:
                for detail in execution_details:
                    status = detail["status"]
                    reason = detail.get("reason", "N/A")
                    trade = detail.get("trade")
                    intent = detail.get("intent")

                    if intent is not None:
                        order_id = intent.order_id
                        write_line(
                            file,
                            (
                                f"  - OrderID={order_id}, "
                                f"Status={status}, "
                                f"Reason={reason}"
                            ),
                        )
                    else:
                        write_line(file, f"  - Event: {status}, Reason={reason}")

                    if trade:
                        write_line(
                            file,
                            (
                                f"    TradeID={getattr(trade, 'trade_id', 'N/A')}, "
                                f"Qty={trade.quantity}, "
                                f"Price={trade.price:.4f}, "
                                f"Fee={trade.fee:.4f}, "
                                f"Time={trade.timestamp}"
                            ),
                        )
            else:
                write_line(file, "  (none)")

            write_line(file)

            write_line(file, "Portfolio After:")
            write_line(file, f"  Cash:   {snapshot_after.cash:,.2f}")
            write_line(file, f"  Equity: {snapshot_after.equity:,.2f}")
            if hasattr(snapshot_after, 'unrealized_pnl'):
                write_line(file, f"  Unrealized PnL: {snapshot_after.unrealized_pnl:,.2f}")
            if hasattr(snapshot_after, 'total_realized_pnl'):
                # Affichage du Net PnL (Realized - Fees) pour plus de clarté
                net_realized = snapshot_after.total_realized_pnl - snapshot_after.total_fees
                write_line(file, f"  Total Realized PnL (Gross): {snapshot_after.total_realized_pnl:,.2f}")
                write_line(file, f"  Total Fees:                 {snapshot_after.total_fees:,.2f}")
                write_line(file, f"  Net Realized PnL:           {net_realized:,.2f}")

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
            write_line(file)
