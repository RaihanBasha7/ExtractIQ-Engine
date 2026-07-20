import platform
from datetime import datetime, timezone

import app.config as cfg
from app.api.models import VersionResponse


class VersionService:
    """Reads service version, active provider/model, and runtime metadata.

    All values are sourced from :mod:`app.config` and the Python runtime.
    No secrets or filesystem paths are exposed.
    """

    def get_version(self) -> VersionResponse:
        return VersionResponse(
            service=cfg.APP_NAME,
            version=cfg.APP_VERSION,
            api_version=cfg.API_VERSION,
            provider=cfg.ACTIVE_PROVIDER,
            model=cfg.ACTIVE_MODEL,
            environment=cfg.ENVIRONMENT,
            python_version=platform.python_version(),
            timestamp=datetime.now(timezone.utc),
        )
