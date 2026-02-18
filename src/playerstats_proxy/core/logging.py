import logging


def setup_logging() -> None:
    # Logging simple, compatible avec Uvicorn
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
