import asyncio
import logging
from datetime import datetime

# Configuration de base
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("CRYPTO VIZ Web Scraper Starting...")
    logger.info("Ready to collect crypto data from APIs")
    
    # Simulation du service de scraping
    while True:
        logger.info(f"Scraping crypto data at {datetime.now()}")
        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
