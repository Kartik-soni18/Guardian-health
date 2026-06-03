"""
GuardianHealth v2 - MongoDB / Beanie Database Layer

Handles Motor async connection lifecycle, Beanie ODM initialization,
and index creation on startup.
"""

from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.config import get_settings
from app.logging_config import get_logger
from app.models.user import User
from app.models.chat import Chat

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Module-level Motor client
# ---------------------------------------------------------------------------

_motor_client: AsyncIOMotorClient | None = None


def get_motor_client() -> AsyncIOMotorClient:
    """
    Return the singleton Motor client.

    Raises:
        RuntimeError: If init_db() has not been called yet.
    """
    if _motor_client is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _motor_client


def get_database():
    """Return the configured MongoDB database handle."""
    settings = get_settings()
    return get_motor_client()[settings.mongodb_db]


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


async def init_db() -> None:
    """
    Initialize the MongoDB connection and Beanie ODM.

    This function:
        1. Creates the Motor async client.
        2. Pings the server to confirm connectivity.
        3. Registers all Beanie Document models.
        4. Creates required indexes.

    Must be called once during application startup.
    """
    global _motor_client  # noqa: PLW0603

    settings = get_settings()
    logger.info("Connecting to MongoDB at %s", settings.mongodb_uri)

    _motor_client = AsyncIOMotorClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=30000,
        maxPoolSize=50,
        minPoolSize=5,
    )

    # Health check before Beanie init
    await _motor_client.admin.command("ping")
    logger.info("MongoDB connection established")

    # Initialize Beanie with all Document models
    await init_beanie(
        database=_motor_client[settings.mongodb_db],
        document_models=[
            User,
            Chat,
        ],
    )
    logger.info("Beanie ODM initialized with models: User, Chat")

    # Ensure indexes exist
    await _create_indexes()


async def close_db() -> None:
    """
    Gracefully close the Motor client connection.

    Should be called during application shutdown.
    """
    global _motor_client  # noqa: PLW0603

    if _motor_client is not None:
        _motor_client.close()
        _motor_client = None
        logger.info("MongoDB connection closed")


# ---------------------------------------------------------------------------
# Indexes
# ---------------------------------------------------------------------------


async def _create_indexes() -> None:
    """
    Create MongoDB indexes required by the application.

    Indexes created:
        - users.username: unique, sparse
        - users.email: unique, sparse
        - chats.chat_id: unique, sparse
        - chats.user_id: standard (for user-scoped queries)
        - chats.created_at: descending (for recent-first listing)
    """
    db = get_database()

    # User indexes
    await db["users"].create_index("username", unique=True, sparse=True)
    await db["users"].create_index("email", unique=True, sparse=True)
    logger.debug("User indexes created: username (unique), email (unique)")

    # Chat indexes
    await db["chats"].create_index("chat_id", unique=True, sparse=True)
    await db["chats"].create_index("user_id")
    await db["chats"].create_index("created_at")
    logger.debug(
        "Chat indexes created: chat_id (unique), user_id, created_at"
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


async def health_check() -> dict[str, str | bool]:
    """
    Perform a database health check.

    Returns:
        A dict with keys: status (str), ping_ok (bool).
    """
    try:
        client = get_motor_client()
        await client.admin.command("ping")
        return {"status": "connected", "ping_ok": True}
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        return {"status": "disconnected", "ping_ok": False, "error": str(exc)}
