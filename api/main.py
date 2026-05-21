"""
PSN API - Main FastAPI Application

Serves three API products:
1. Metabolic Simulation (/v1/simulate)
2. GL-Number Registry (/v1/registry)
3. Goebl Regulatory Analysis (/v1/regulatory)
"""
import time
import logging
from logging.handlers import TimedRotatingFileHandler
from contextlib import asynccontextmanager
from datetime import datetime

import cobra
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.config import (
    MODEL_PATH, LOG_PATH, API_VERSION, MODEL_VERSION
)
from api.auth import init_api_keys_db
from api.models.common import Meta, HealthResponse
from api.services.simulation_service import SimulationService
from api.services.registry_service import RegistryService
from api.services.regulatory_service import RegulatoryService
from api.routers import simulate_router, registry_router, regulatory_router
from api.routers.simulate import set_simulation_service
from api.routers.registry import set_registry_service
from api.routers.regulatory import set_regulatory_service


# Configure logging
def setup_logging():
    """Set up logging with daily rotation"""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # File handler with daily rotation
    file_handler = TimedRotatingFileHandler(
        LOG_PATH,
        when='midnight',
        interval=1,
        backupCount=30
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Reduce noise from other libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


# Global state
app_state = {
    "model": None,
    "model_loaded": False,
    "start_time": None,
    "load_time_seconds": 0
}

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    setup_logging()
    logger.info("=" * 60)
    logger.info("PSN API Starting...")
    logger.info(f"API Version: {API_VERSION}")
    logger.info(f"Model Version: {MODEL_VERSION}")

    app_state["start_time"] = time.time()

    # Initialize API keys database
    logger.info("Initializing API keys database...")
    init_api_keys_db()

    # Load COBRA model
    logger.info(f"Loading COBRA model from {MODEL_PATH}...")
    load_start = time.time()

    try:
        model = cobra.io.read_sbml_model(str(MODEL_PATH))
        model.solver.configuration.processes = 20
        app_state["model"] = model
        app_state["model_loaded"] = True
        app_state["load_time_seconds"] = time.time() - load_start

        logger.info(f"Model loaded successfully in {app_state['load_time_seconds']:.2f}s")
        logger.info(f"  - Reactions: {len(model.reactions)}")
        logger.info(f"  - Metabolites: {len(model.metabolites)}")
        logger.info(f"  - Genes: {len(model.genes)}")

    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        app_state["model_loaded"] = False

    # Initialize services
    logger.info("Initializing services...")

    if app_state["model_loaded"]:
        simulation_service = SimulationService(app_state["model"])
        set_simulation_service(simulation_service)
        logger.info("  - Simulation service: OK")
    else:
        logger.warning("  - Simulation service: UNAVAILABLE (model not loaded)")

    registry_service = RegistryService()
    set_registry_service(registry_service)
    logger.info("  - Registry service: OK")

    regulatory_service = RegulatoryService()
    set_regulatory_service(regulatory_service)
    logger.info("  - Regulatory service: OK")

    logger.info("PSN API Ready!")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("PSN API Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="PSN API - Pharma Saccharomyces-Nexus",
    description="""
## Digital Twin of Yeast Metabolism

The PSN API provides programmatic access to a comprehensive yeast metabolic model
built on COBRApy and Yeast-GEM v9.0.2.

### API Products

1. **Metabolic Simulation** (`/v1/simulate`) - Run Flux Balance Analysis with optional
   Goebl regulatory layer
2. **GL-Number Registry** (`/v1/registry`) - Query genes, reactions, metabolites,
   and pathway information
3. **Goebl Regulatory Analysis** (`/v1/regulatory`) - Premium access to proprietary
   SCF-GRR1 proteolytic regulation modeling

### Authentication

All endpoints require an API key via the `X-API-Key` header.

### Rate Limits

- Free: 50 calls/month
- Pro: 1,000 calls/month
- Enterprise: 10,000 calls/month
    """,
    version=API_VERSION,
    docs_url="/v1/docs",
    redoc_url="/v1/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all API requests"""
    start_time = time.time()

    # Get API key suffix for logging (privacy)
    api_key = request.headers.get("X-API-Key", "")
    key_suffix = f"...{api_key[-8:]}" if len(api_key) > 8 else "none"

    response = await call_next(request)

    # Calculate processing time
    process_time = int((time.time() - start_time) * 1000)

    # Log request
    logger.info(
        f"{request.method} {request.url.path} - "
        f"key={key_suffix} - "
        f"status={response.status_code} - "
        f"time={process_time}ms"
    )

    return response


# Include routers
app.include_router(simulate_router)
app.include_router(registry_router)
app.include_router(regulatory_router)


# Health endpoint (no auth required)
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health Check",
    description="Returns API status, model loading state, and uptime."
)
async def health_check():
    """Health check endpoint for monitoring."""
    uptime = time.time() - app_state["start_time"] if app_state["start_time"] else 0

    # Check database connectivity
    try:
        from api.config import DATABASE_PATH
        database_connected = DATABASE_PATH.exists()
    except Exception:
        database_connected = False

    return HealthResponse(
        status="healthy" if app_state["model_loaded"] else "degraded",
        model_loaded=app_state["model_loaded"],
        database_connected=database_connected,
        uptime_seconds=round(uptime, 2),
        meta=Meta(api_version=API_VERSION, model_version=MODEL_VERSION)
    )


# Root redirect to docs
@app.get("/", include_in_schema=False)
async def root():
    """Redirect to API documentation"""
    return JSONResponse(
        content={
            "message": "PSN API - Pharma Saccharomyces-Nexus",
            "version": API_VERSION,
            "docs": "/v1/docs",
            "health": "/health"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8502)
