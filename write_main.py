content = r'''# src/api/main.py
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from src.agent.graph import build_graph
from src.agent.state import AgentState
from src.alerts.alert_manager import AlertManager, FileAlertChannel
from src.api.schemas import AnalyseRequest, HealthResponse
from src.audit.audit_logger import AuditLogger

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DASH_USER  = os.getenv("DASH_USER", "admin")
DASH_PASS  = os.getenv("DASH_PASS", "clinic2026")
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production-please")


def require_login(request: Request) -> bool:
    return request.session.get("logged_in") is True
'''

with open("src/api/main.py", "w", encoding="utf-8") as f:
    f.write(content)
print("done")
