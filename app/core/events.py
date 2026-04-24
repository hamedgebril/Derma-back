"""
Application lifecycle events (startup/shutdown)
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import setup_logging
from app.infrastructure.database.session import init_db
from app.infrastructure.ml.model_loader import ModelLoader

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Manage application lifespan events
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Setup logging
    setup_logging()
    
    # Initialize database
    logger.info("Initializing database...")
    try:
        await init_db()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    # Load ML model (skip if model file doesn't exist)
    logger.info("Loading ML model...")
    try:
        model_loader = ModelLoader.get_instance()
        await model_loader.load_model()
        
        # Warmup model if enabled and loaded successfully
        if settings.MODEL_WARMUP and model_loader.is_loaded:
            logger.info("Warming up model...")
            await model_loader.warmup()
        
        logger.info("ML model ready")
    except Exception as e:
        logger.error(f"Model loading failed: {e}", exc_info=True)
        # Don't continue - model is required now
        raise
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Cleanup model resources
    try:
        model_loader = ModelLoader.get_instance()
        model_loader.cleanup()
    except:
        pass
    
    logger.info("Application shutdown complete")
