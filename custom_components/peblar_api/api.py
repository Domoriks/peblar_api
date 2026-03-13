"""HTTP client for Peblar local REST API."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class PeblarApiClientError(Exception):
    """Base error for Peblar API client."""


class PeblarApiClientConnectionError(PeblarApiClientError):
    """Raised when the Peblar charger cannot be reached."""


class PeblarApiAuthenticationError(PeblarApiClientError):
    """Raised when authentication with Peblar API fails."""


class PeblarApiClient:
    """Simple async client for the Peblar local REST API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        api_token: str,
        request_timeout: int = 10,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._host = self._normalize_host(host)
        self._api_token = api_token.strip()
        self._request_timeout = request_timeout

    @staticmethod
    def _normalize_host(host: str) -> str:
        """Normalize host input from config flow and options."""
        normalized = host.strip().removeprefix("http://").removeprefix("https://")
        normalized = normalized.split("/", maxsplit=1)[0]
        return normalized.strip()

    @property
    def base_url(self) -> str:
        """Return API base URL."""
        return f"http://{self._host}/api/wlac/v1"

    async def get_system(self) -> dict[str, Any]:
        """Get generic system information."""
        return await self._get("system")

    async def get_evinterface(self) -> dict[str, Any]:
        """Get EV interface information."""
        return await self._get("evinterface")

    async def get_meter(self) -> dict[str, Any]:
        """Get meter information."""
        return await self._get("meter")

    async def patch_evinterface(self, data: dict[str, Any]) -> dict[str, Any]:
        """Patch EV interface fields."""
        return await self._patch("evinterface", data)

    async def _get(self, endpoint: str) -> dict[str, Any]:
        """Run a GET request against the Peblar API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        timeout = aiohttp.ClientTimeout(total=self._request_timeout)

        try:
            async with self._session.get(
                url,
                headers={"Authorization": self._api_token},
                timeout=timeout,
            ) as response:
                if response.status == HTTPStatus.UNAUTHORIZED:
                    raise PeblarApiAuthenticationError("Invalid API token")

                if response.status >= HTTPStatus.BAD_REQUEST:
                    message = f"Peblar API returned HTTP {response.status}"
                    error_payload = await _read_json_safely(response)
                    if isinstance(error_payload, dict):
                        status_msg = error_payload.get("statusmsg")
                        if isinstance(status_msg, str) and status_msg:
                            message = status_msg
                    raise PeblarApiClientError(message)

                payload = await _read_json_safely(response)
        except (
            aiohttp.ClientConnectionError,
            aiohttp.ClientConnectorError,
            aiohttp.ServerTimeoutError,
            TimeoutError,
        ) as err:
            raise PeblarApiClientConnectionError(
                "Unable to connect to Peblar charger"
            ) from err
        except aiohttp.ClientError as err:
            raise PeblarApiClientError(f"HTTP client error: {err}") from err

        if not isinstance(payload, dict):
            raise PeblarApiClientError("Unexpected response format from Peblar API")

        _LOGGER.debug("GET /%s response: %s", endpoint, payload)
        return payload


    async def _patch(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        """Run a PATCH request against the Peblar API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        timeout = aiohttp.ClientTimeout(total=self._request_timeout)

        try:
            async with self._session.patch(
                url,
                headers={"Authorization": self._api_token},
                json=data,
                timeout=timeout,
            ) as response:
                if response.status == HTTPStatus.UNAUTHORIZED:
                    raise PeblarApiAuthenticationError("Invalid API token")

                if response.status >= HTTPStatus.BAD_REQUEST:
                    message = f"Peblar API returned HTTP {response.status}"
                    error_payload = await _read_json_safely(response)
                    if isinstance(error_payload, dict):
                        status_msg = error_payload.get("statusmsg")
                        if isinstance(status_msg, str) and status_msg:
                            message = status_msg
                    raise PeblarApiClientError(message)

                payload = await _read_json_safely(response)
        except (
            aiohttp.ClientConnectionError,
            aiohttp.ClientConnectorError,
            aiohttp.ServerTimeoutError,
            TimeoutError,
        ) as err:
            raise PeblarApiClientConnectionError(
                "Unable to connect to Peblar charger"
            ) from err
        except aiohttp.ClientError as err:
            raise PeblarApiClientError(f"HTTP client error: {err}") from err

        if not isinstance(payload, dict):
            raise PeblarApiClientError("Unexpected response format from Peblar API")

        _LOGGER.debug("PATCH /%s payload: %s | response: %s", endpoint, data, payload)
        return payload


async def _read_json_safely(response: aiohttp.ClientResponse) -> Any:
    """Read JSON and gracefully handle non-JSON payloads."""
    try:
        return await response.json(content_type=None)
    except (aiohttp.ContentTypeError, ValueError):
        text = (await response.text()).strip()
        return {"statusmsg": text} if text else None
