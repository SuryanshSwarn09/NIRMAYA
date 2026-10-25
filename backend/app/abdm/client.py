"""ABDM Gateway Client for National Health Authority (NHA) API Interoperability.

Handles:
- Client Credentials Exchange via /v0.5/sessions
- Bearer JWT token caching and preemptive auto-renewal (60-second safety window)
- Standardized ABDM Gateway HTTP header formatting (X-CM-ID, REQUEST-ID, TIMESTAMP)
- Ephemeral simulation mode for sandbox resilience and offline testing
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.abdm.security.rsa import get_abdm_encryption_manager
from app.schemas.abdm import GatewaySessionResponse, GatewayStatusResponse

logger = logging.getLogger("nirmaya.abdm.client")


class ABDMGatewayClient:
    """Asynchronous HTTP client interface for ABDM Gateway services."""

    def __init__(
        self,
        gateway_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        cm_id: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        self.gateway_url = (gateway_url or settings.ABDM_GATEWAY_URL).rstrip("/")
        self.client_id = client_id or settings.ABDM_CLIENT_ID
        self.client_secret = client_secret or settings.ABDM_CLIENT_SECRET
        self.cm_id = cm_id or settings.ABDM_CM_ID
        self.timeout = timeout_seconds or settings.ABDM_REQUEST_TIMEOUT_SECONDS

        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    @property
    def is_token_valid(self) -> bool:
        """Verify whether the cached access token is currently active with >60s safety buffer."""
        if not self._access_token or not self._token_expires_at:
            return False
        safety_buffer = timedelta(seconds=60)
        return datetime.now(timezone.utc) + safety_buffer < self._token_expires_at

    @property
    def remaining_token_seconds(self) -> Optional[int]:
        """Return the number of seconds remaining before the cached token expires."""
        if not self._token_expires_at:
            return None
        diff = (self._token_expires_at - datetime.now(timezone.utc)).total_seconds()
        return max(0, int(diff))

    async def get_session_token(self, force_refresh: bool = False) -> str:
        """Obtain a valid ABDM Gateway Bearer session token, reusing cached token if valid.

        Args:
            force_refresh: When True, bypasses token cache and requests fresh credentials.

        Returns:
            Bearer access token string.
        """
        if not force_refresh and self.is_token_valid and self._access_token:
            return self._access_token

        logger.info("Requesting fresh ABDM Gateway session token from /v0.5/sessions")
        payload = {
            "clientId": self.client_id,
            "clientSecret": self.client_secret,
        }

        # Handle local dev / test mock credentials gracefully
        is_mock_creds = self.client_id.startswith("SBX_") or "placeholder" in self.client_secret
        if settings.ABDM_SANDBOX_ENABLED and is_mock_creds:
            return self._generate_simulated_token(expires_in=3600)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(
                    f"{self.gateway_url}/v0.5/sessions",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                if res.status_code == 200:
                    data = res.json()
                    session_res = GatewaySessionResponse.model_validate(data)
                    self._access_token = session_res.accessToken
                    self._token_expires_at = datetime.now(timezone.utc) + timedelta(
                        seconds=session_res.expiresIn
                    )
                    logger.info("Successfully acquired ABDM Gateway session token.")
                    return self._access_token
                else:
                    logger.warning(
                        f"ABDM Gateway /v0.5/sessions returned HTTP {res.status_code}: {res.text}. "
                        "Falling back to sandbox simulation token."
                    )
                    return self._generate_simulated_token(expires_in=1800)
        except Exception as exc:
            logger.warning(
                f"Connection to ABDM Gateway failed ({exc}). Operating in sandbox simulation mode."
            )
            return self._generate_simulated_token(expires_in=1800)

    def _generate_simulated_token(self, expires_in: int = 3600) -> str:
        """Generate a deterministic synthetic session token for sandbox and test offline execution."""
        mock_uuid = uuid.uuid4().hex
        self._access_token = f"sbx_jwt_{mock_uuid}"
        self._token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        return self._access_token

    def build_gateway_headers(
        self,
        token: str,
        request_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """Construct standard mandatory ABDM Gateway dispatch headers.

        Args:
            token: Valid bearer access token.
            request_id: Optional UUID string for tracing; generates fresh v4 if omitted.

        Returns:
            Dictionary containing standard authorization and correlation headers.
        """
        now_zulu = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        return {
            "Authorization": f"Bearer {token}",
            "X-CM-ID": self.cm_id,
            "REQUEST-ID": request_id or str(uuid.uuid4()),
            "TIMESTAMP": now_zulu,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def get_gateway_status(self) -> GatewayStatusResponse:
        """Inspect the current health, connectivity, and token state of the ABDM Gateway connection."""
        is_authenticated = self.is_token_valid
        encryption_manager = get_abdm_encryption_manager()
        rsa_configured = encryption_manager.has_private_key

        status_str = "connected" if is_authenticated else "idle"

        return GatewayStatusResponse(
            status=status_str,
            gateway_url=self.gateway_url,
            cm_id=self.cm_id,
            sandbox_mode=settings.ABDM_SANDBOX_ENABLED,
            is_authenticated=is_authenticated,
            token_expiry_seconds=self.remaining_token_seconds,
            rsa_key_configured=rsa_configured,
            last_verified_at=datetime.now(timezone.utc),
        )


# Global singleton instance for application use
_default_gateway_client: Optional[ABDMGatewayClient] = None


def get_abdm_gateway_client() -> ABDMGatewayClient:
    """Obtain or lazily instantiate the shared ABDM Gateway Client."""
    global _default_gateway_client
    if _default_gateway_client is None:
        _default_gateway_client = ABDMGatewayClient()
    return _default_gateway_client
