"""Async DynamoDB client and table management for GuardianHealth.

Uses aioboto3 for fully async I/O.  Tables are created with on-demand billing
(pay-per-request) to stay within the AWS Free Tier.

Table design:
    users        : PK username  (GSI: by_email → email)
    chats        : PK chat_id   , SK user_id  (GSI: by_user → user_id, created_at)
    interactions : PK interaction_id, SK chat_id
"""


import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional

import aioboto3
from botocore.exceptions import ClientError

from app.config import Settings, get_settings
from app.logging_config import get_logger

logger = get_logger("app.dynamodb")

# ------------------------------------------------------------------------------
# Client / resource helpers
# ------------------------------------------------------------------------------

_session: Optional[aioboto3.Session] = None
_lock = asyncio.Lock()


async def _get_session() -> aioboto3.Session:
    """Return a cached aioboto3 session (thread-safe)."""
    global _session
    if _session is None:
        async with _lock:
            if _session is None:
                _session = aioboto3.Session()
    return _session


@asynccontextmanager
async def get_ddb_client() -> AsyncGenerator[Any, None]:
    """Async context manager yielding a DynamoDB *client*.

    Usage:
        async with get_ddb_client() as client:
            await client.put_item(TableName="...", Item={...})
    """
    settings = get_settings()
    session = await _get_session()
    kwargs: Dict[str, Any] = {"region_name": settings.aws_region}
    if settings.dynamodb_endpoint_url:
        kwargs["endpoint_url"] = settings.dynamodb_endpoint_url

    async with session.client("dynamodb", **kwargs) as client:
        yield client


@asynccontextmanager
async def get_ddb_resource() -> AsyncGenerator[Any, None]:
    """Async context manager yielding a DynamoDB *resource*.

    Usage:
        async with get_ddb_resource() as dynamo:
            table = await dynamo.Table("my-table")
            await table.put_item(Item={...})
    """
    settings = get_settings()
    session = await _get_session()
    kwargs: Dict[str, Any] = {"region_name": settings.aws_region}
    if settings.dynamodb_endpoint_url:
        kwargs["endpoint_url"] = settings.dynamodb_endpoint_url

    async with session.resource("dynamodb", **kwargs) as dynamo:
        yield dynamo


async def get_ddb_table(table_name: str):
    """Return a Table resource object for the given table name.

    The caller must already be inside an async with get_ddb_resource() block,
    OR use this helper standalone (it manages its own resource context internally
    but requires the caller to await table methods).

    For simplicity in route handlers, prefer the dependency-injected table
    from app.core.dependencies.
    """
    settings = get_settings()
    session = await _get_session()
    kwargs: Dict[str, Any] = {"region_name": settings.aws_region}
    if settings.dynamodb_endpoint_url:
        kwargs["endpoint_url"] = settings.dynamodb_endpoint_url

    dynamo = session.resource("dynamodb", **kwargs)
    return await dynamo.Table(table_name)


# ------------------------------------------------------------------------------
# Table creation
# ------------------------------------------------------------------------------


async def create_tables(settings: Optional[Settings] = None) -> None:
    """Idempotently create all GuardianHealth DynamoDB tables.

    Uses on-demand (PAY_PER_REQUEST) billing for free-tier safety.
    Existing tables are silently skipped.
    """
    if settings is None:
        settings = get_settings()

    async with get_ddb_client() as client:
        existing = await _list_existing_tables(client)

        await _ensure_users_table(client, settings, existing)
        await _ensure_chats_table(client, settings, existing)
        await _ensure_interactions_table(client, settings, existing)

    logger.info("DynamoDB table initialization complete")


async def _list_existing_tables(client) -> set:
    """Return a set of table names currently in the account."""
    paginator = client.get_paginator("list_tables")
    names: set = set()
    async for page in paginator.paginate():
        names.update(page.get("TableNames", []))
    return names


async def _ensure_users_table(client, settings: Settings, existing: set) -> None:
    table_name = settings.table_users
    if table_name in existing:
        logger.debug("Table %s already exists", table_name)
        return

    logger.info("Creating table: %s", table_name)
    await client.create_table(
        TableName=table_name,
        AttributeDefinitions=[
            {"AttributeName": "username", "AttributeType": "S"},
            {"AttributeName": "email", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "username", "KeyType": "HASH"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "by_email",
                "KeySchema": [
                    {"AttributeName": "email", "KeyType": "HASH"},
                ],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    logger.info("Table %s created successfully", table_name)


async def _ensure_chats_table(client, settings: Settings, existing: set) -> None:
    table_name = settings.table_chats
    if table_name in existing:
        logger.debug("Table %s already exists", table_name)
        return

    logger.info("Creating table: %s", table_name)
    await client.create_table(
        TableName=table_name,
        AttributeDefinitions=[
            {"AttributeName": "chat_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "chat_id", "KeyType": "HASH"},
            {"AttributeName": "user_id", "KeyType": "RANGE"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "by_user",
                "KeySchema": [
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                    {"AttributeName": "created_at", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    logger.info("Table %s created successfully", table_name)


async def _ensure_interactions_table(client, settings: Settings, existing: set) -> None:
    table_name = settings.table_interactions
    if table_name in existing:
        logger.debug("Table %s already exists", table_name)
        return

    logger.info("Creating table: %s", table_name)
    await client.create_table(
        TableName=table_name,
        AttributeDefinitions=[
            {"AttributeName": "interaction_id", "AttributeType": "S"},
            {"AttributeName": "chat_id", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "interaction_id", "KeyType": "HASH"},
            {"AttributeName": "chat_id", "KeyType": "RANGE"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    logger.info("Table %s created successfully", table_name)


# ------------------------------------------------------------------------------
# Health check
# ------------------------------------------------------------------------------


async def can_ping_dynamodb() -> bool:
    """Return True if DynamoDB is reachable and responsive.

    Performs a lightweight ListTables operation.
    """
    try:
        async with get_ddb_client() as client:
            await client.list_tables(Limit=1)
        return True
    except Exception as exc:
        logger.warning("DynamoDB health check failed: %s", exc)
        return False


# ------------------------------------------------------------------------------
# Low-level helpers
# ------------------------------------------------------------------------------


async def ddb_put_item(table_name: str, item: Dict[str, Any]) -> None:
    """Put a single item into the named table.

    Raises:
        app.core.exceptions.DatabaseError: On DynamoDB client errors.
    """
    from app.core.exceptions import DatabaseError

    try:
        async with get_ddb_client() as client:
            await client.put_item(TableName=table_name, Item=_serialize_item(item))
    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        raise DatabaseError(
            f"Failed to write to {table_name}: {error_code}",
            extra={"table": table_name, "dynamo_error": error_code},
        ) from exc


async def ddb_get_item(
    table_name: str, key: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Get a single item by its primary key.

    Returns:
        The deserialized item dict, or None if not found.
    """
    from app.core.exceptions import DatabaseError

    try:
        async with get_ddb_client() as client:
            resp = await client.get_item(
                TableName=table_name, Key=_serialize_keys(key)
            )
        raw = resp.get("Item")
        return _deserialize_item(raw) if raw else None
    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        raise DatabaseError(
            f"Failed to read from {table_name}: {error_code}",
            extra={"table": table_name, "dynamo_error": error_code},
        ) from exc


async def ddb_query(
    table_name: str,
    *,
    key_condition: str,
    expression_values: Dict[str, Any],
    index_name: Optional[str] = None,
    scan_index_forward: bool = False,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Run a Query operation against a table or GSI.

    Returns:
        List of deserialized item dicts (may be empty).
    """
    from app.core.exceptions import DatabaseError

    params: Dict[str, Any] = {
        "TableName": table_name,
        "KeyConditionExpression": key_condition,
        "ExpressionAttributeValues": _serialize_keys(expression_values),
        "ScanIndexForward": scan_index_forward,
        "Limit": limit,
    }
    if index_name:
        params["IndexName"] = index_name

    try:
        async with get_ddb_client() as client:
            resp = await client.query(**params)
        items = resp.get("Items", [])
        return [_deserialize_item(i) for i in items]
    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        raise DatabaseError(
            f"Failed to query {table_name}: {error_code}",
            extra={"table": table_name, "dynamo_error": error_code},
        ) from exc


async def ddb_delete_item(table_name: str, key: Dict[str, Any]) -> None:
    """Delete a single item by primary key."""
    from app.core.exceptions import DatabaseError

    try:
        async with get_ddb_client() as client:
            await client.delete_item(TableName=table_name, Key=_serialize_keys(key))
    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        raise DatabaseError(
            f"Failed to delete from {table_name}: {error_code}",
            extra={"table": table_name, "dynamo_error": error_code},
        ) from exc


# ------------------------------------------------------------------------------
# (De)serialization — DynamoDB type wrapper helpers
# ------------------------------------------------------------------------------

def _serialize_keys(key: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """Convert a simple dict {'username': 'alice'} into DynamoDB typed format."""
    return {k: {"S": str(v)} for k, v in key.items()}


def _serialize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Best-effort serialize a Python dict into DynamoDB AttributeValue format.

    Handles strings, numbers (as Decimal), booleans, lists, and nested dicts.
    """
    from decimal import Decimal

    result: Dict[str, Any] = {}
    for k, v in item.items():
        if v is None:
            continue  # Skip nulls — DynamoDB doesn't have a native null in all contexts
        elif isinstance(v, bool):
            result[k] = {"BOOL": v}
        elif isinstance(v, (int, float)):
            result[k] = {"N": str(v)}
        elif isinstance(v, str):
            result[k] = {"S": v}
        elif isinstance(v, list):
            result[k] = {"L": [_serialize_value(i) for i in v]}
        elif isinstance(v, dict):
            result[k] = {"M": _serialize_item(v)}
        else:
            result[k] = {"S": str(v)}
    return result


def _serialize_value(v: Any) -> Dict[str, Any]:
    """Serialize a single value into DynamoDB AttributeValue format."""
    if v is None:
        return {"NULL": True}
    elif isinstance(v, bool):
        return {"BOOL": v}
    elif isinstance(v, (int, float)):
        return {"N": str(v)}
    elif isinstance(v, str):
        return {"S": v}
    elif isinstance(v, list):
        return {"L": [_serialize_value(i) for i in v]}
    elif isinstance(v, dict):
        return {"M": _serialize_item(v)}
    return {"S": str(v)}


def _deserialize_item(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a DynamoDB typed item into a plain Python dict."""
    from decimal import Decimal

    result: Dict[str, Any] = {}
    for k, v in raw.items():
        result[k] = _deserialize_value(v)
    return result


def _deserialize_value(v: Dict[str, Any]) -> Any:
    """Deserialize a single DynamoDB AttributeValue."""
    if "S" in v:
        return v["S"]
    if "N" in v:
        s = v["N"]
        return int(s) if "." not in s and "e" not in s.lower() else float(s)
    if "BOOL" in v:
        return v["BOOL"]
    if "NULL" in v and v["NULL"]:
        return None
    if "L" in v:
        return [_deserialize_value(i) for i in v["L"]]
    if "M" in v:
        return _deserialize_item(v["M"])
    if "SS" in v:
        return set(v["SS"])
    if "NS" in v:
        return {int(n) if "." not in n else float(n) for n in v["NS"]}
    return v