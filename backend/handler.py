"""AWS Lambda entry point — Mangum ASGI adapter."""

from mangum import Mangum

from app.main import app

handler = Mangum(app, lifespan="off")
