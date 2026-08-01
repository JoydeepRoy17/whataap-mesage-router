"""
Main Entry Point
CLI runner for the WhatsApp Message Router AI.
"""
import sys
import logging
from src.pipeline import MessageRouterPipeline

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    setup_logging()
    logger = logging.getLogger("main")
    logger.info("Initializing WhatsApp Message Router AI Execution...")

    try:
        pipeline = MessageRouterPipeline(
            data_dir="dataset",
            output_dir="outputs",
            use_ai=True
        )
        results = pipeline.run()
        logger.info(f"Successfully finished routing {len(results)} messages.")
    except Exception as e:
        logger.critical(f"Unhandled exception in main execution: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
