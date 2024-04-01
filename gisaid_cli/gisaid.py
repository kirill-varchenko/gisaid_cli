from __future__ import annotations

import asyncio
import hashlib
import secrets
from datetime import datetime

import aiohttp

from gisaid_cli.models import AuthToken, Database, Submission


def _sha512_hexdigest(inp: bytes) -> str:
    hasher = hashlib.sha512()
    hasher.update(inp)
    return hasher.hexdigest()


def _hash_password(password: str) -> str:
    salt = secrets.token_urlsafe(64)
    hashed_password = (
        salt
        + "/"
        + _sha512_hexdigest(
            (salt + _sha512_hexdigest(password.encode("utf8"))).encode("ascii")
        )
    )
    return hashed_password


class GisaidClient:
    gps_service_url = "https://gpsapi.epicov.org/epi3/gps_api"
    sleep = 0.1

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.session = session

    async def call_api(self, data: dict, database: Database) -> dict:
        data.update(
            {
                "api": {"version": 1},
                "ctx": database.value,
            }
        )
        async with self.session.post(self.gps_service_url, json=data) as response:
            await asyncio.sleep(self.sleep)
            return await response.json()

    async def request_auth_token(
        self, database: Database, client_id: str, username: str, password: str
    ) -> AuthToken:
        hashed = _hash_password(password)

        command_data = {
            "cmd": "state/auth/get_token",
            "client_id": client_id,
            "login": username,
            "hash": hashed,
        }

        response = await self.call_api(command_data, database)
        return AuthToken(
            database=database,
            client_id=client_id,
            token=response["auth_token"],
            expiry=datetime.fromtimestamp(response["valid_until"]),
        )


class GisaidSession:
    def __init__(self, auth_token: AuthToken, client: GisaidClient) -> None:
        self.auth_token = auth_token
        self.client = client
        self.sid: str | None = None

    async def __aenter__(self) -> GisaidSession:
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def open(self) -> None:
        if self.sid is not None:
            return

        result = await self.client.call_api(
            {
                "cmd": "state/session/logon",
                "api": {"version": 1},
                "client_id": self.auth_token.client_id,
                "auth_token": self.auth_token.token,
            },
            database=self.auth_token.database,
        )
        await asyncio.sleep(0.5)  # give system time to save session
        self.sid = result.get("sid")

    async def close(self) -> None:
        if self.sid is None:
            return

        await self.client.call_api(
            {"cmd": "state/session/logoff", "sid": self.sid},
            database=self.auth_token.database,
        )
        self.sid = None

    async def submit(self, submission: Submission) -> dict:
        if self.sid is None:
            raise ValueError("Session is closed")

        data = submission.model_dump(mode="json", by_alias=True)
        result = await self.client.call_api(
            {
                "cmd": "data/hcov-19/upload",
                "sid": self.sid,
                "data": data,
                "submitter": submission.submitter,
            },
            database=self.auth_token.database,
        )
        result.pop("api", None)
        return result
