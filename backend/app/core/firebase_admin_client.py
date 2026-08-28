"""
firebase_admin_client.py — Server-side Firebase Admin SDK bootstrap & singleton initialization.
"""

from __future__ import annotations
import os
import json
import logging
from typing import Optional, Any
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, auth as fb_auth

try:
    from app.config import settings
except ImportError:
    from backend.app.config import settings

logger = logging.getLogger("udyam_saathi.auth.firebase")

_firebase_app: Optional[firebase_admin.App] = None


def init_firebase_admin() -> Optional[firebase_admin.App]:
    """
    Initializes the Firebase Admin SDK once using:
    1. FIREBASE_SERVICE_ACCOUNT_JSON (single-line JSON string)
    2. FIREBASE_SERVICE_ACCOUNT_PATH (local file path)
    3. Default application credentials / Mock test mode if configured
    """
    global _firebase_app
    if _firebase_app is not None or len(firebase_admin._apps) > 0:
        _firebase_app = firebase_admin.get_app()
        return _firebase_app

    json_str = settings.FIREBASE_SERVICE_ACCOUNT_JSON or os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    path_str = settings.FIREBASE_SERVICE_ACCOUNT_PATH or os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    project_id = settings.FIREBASE_PROJECT_ID or os.getenv("FIREBASE_PROJECT_ID")

    cred = None

    if json_str and json_str.strip():
        try:
            cert_dict = json.loads(json_str.strip())
            cred = credentials.Certificate(cert_dict)
            logger.info("🔐 Initializing Firebase Admin via FIREBASE_SERVICE_ACCOUNT_JSON")
        except Exception as e:
            logger.error(f"❌ Failed to parse FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
            raise ValueError(f"Invalid FIREBASE_SERVICE_ACCOUNT_JSON: {e}")

    elif path_str and path_str.strip():
        raw_path = Path(path_str.strip())
        candidates = [
            raw_path,
            Path.cwd() / raw_path,
            Path.cwd().parent / raw_path,
            Path(__file__).resolve().parent.parent.parent.parent / raw_path,
            Path(__file__).resolve().parent.parent.parent / raw_path,
            Path(__file__).resolve().parent / raw_path,
        ]
        resolved_path = None
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                resolved_path = candidate
                break

        if resolved_path is not None:
            try:
                cred = credentials.Certificate(str(resolved_path))
                logger.info(f"🔐 Initializing Firebase Admin via service account file: {resolved_path}")
            except Exception as e:
                logger.error(f"❌ Failed to load credentials from {resolved_path}: {e}")
                raise ValueError(f"Invalid FIREBASE_SERVICE_ACCOUNT_PATH: {e}")
        else:
            logger.error(f"❌ Service account file not found at any candidate path for: {path_str}")
            raise FileNotFoundError(f"Firebase service account file not found: {path_str}")

    if cred is not None:
        options = {"projectId": project_id} if project_id else {}
        _firebase_app = firebase_admin.initialize_app(cred, options=options)
        logger.info("✅ Firebase Admin SDK successfully initialized.")
        return _firebase_app
    else:
        # Check if running in development / test mode without credentials
        logger.warning(
            "⚠️ Neither FIREBASE_SERVICE_ACCOUNT_JSON nor FIREBASE_SERVICE_ACCOUNT_PATH is configured. "
            "Server token verification will operate in emulator/test validation mode."
        )
        try:
            options = {"projectId": project_id or "udyam-saathi-sih2026"}
            _firebase_app = firebase_admin.initialize_app(options=options)
            return _firebase_app
        except Exception as e:
            logger.warning(f"Could not initialize default Firebase app ({e}); dev token bypass mode active.")
            return None


# Initialize on module load
try:
    init_firebase_admin()
except Exception as exc:
    logger.warning(f"Firebase Admin initialization deferred: {exc}")

# Expose firebase_auth singleton
firebase_auth = fb_auth
