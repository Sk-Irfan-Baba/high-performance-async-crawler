import asyncio
from utils.exporter import URLBatchExporter
from config import DB_PATH


async def main():
    exporter = URLBatchExporter(
        db_path=DB_PATH,
        batch_size=1000,
    )

    while True:
        has_data = await exporter.export_next_batch()
        if not has_data:
            print("[EXPORT] No new URLs. Done.")
            break


if __name__ == "__main__":
    asyncio.run(main())
