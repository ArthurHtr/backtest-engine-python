class Exporter:
    def __init__(self, db_config: dict):
        self.db_config = db_config
        # Initialize database connection here

    def export_to_db(self, data: dict):
        """
        Export data to a database.
        Handles detailed candle-by-candle logs, including rejection reasons.
        :param data: The data to export.
        """
        snapshots = data.get("snapshots", [])
        strategy = data.get("strategy", "")
        orders = data.get("orders", [])
        candle_logs = data.get("candle_logs", [])

        print("Exporting to database...")
        print(f"Strategy: {strategy}")
        print(f"Snapshots: {len(snapshots)} entries")
        print(f"Orders: {len(orders)} entries")
        print(f"Candle Logs: {len(candle_logs)} entries")

        # Add database export logic here to handle candle_logs and other details

    def export_to_file(self, data: dict, file_path: str):
        """
        Export data to a file.
        :param data: The data to export.
        :param file_path: Path to the file.
        """
        pass