import base64
import json
import logging
import os
import pathlib
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from urllib.parse import urlencode

import click
import requests
import uvicorn
from fastapi import FastAPI, Query, Request
from starlette.background import BackgroundTask
from starlette.responses import RedirectResponse

from lightning_app.core.constants import get_lightning_cloud_url, LIGHTNING_CREDENTIAL_PATH
from lightning_app.utilities.network import find_free_network_port

logger = logging.getLogger(__name__)


class Keys(Enum):
    USERNAME = "LIGHTNING_USERNAME"
    USER_ID = "LIGHTNING_USER_ID"
    API_KEY = "LIGHTNING_API_KEY"

    @property
    def suffix(self):
        return self.value.lstrip("LIGHTNING_").lower()


@dataclass
class Auth:
    username: Optional[str] = None
    user_id: Optional[str] = None
    api_key: Optional[str] = None

    secrets_file = pathlib.Path(LIGHTNING_CREDENTIAL_PATH)

    def __post_init__(self):
        for key in Keys:
            setattr(self, key.suffix, os.environ.get(key.value, None))

        self._with_env_var = bool(self.user_id and self.api_key)  # used by authenticate method
        if self.api_key and not self.user_id:
            raise ValueError(
                f"{Keys.USER_ID.value} is missing from env variables. "
                "To use env vars for authentication both "
                f"{Keys.USER_ID.value} and {Keys.API_KEY.value} should be set."
            )

    def load(self) -> bool:
        """Load credentials from disk and update properties with credentials.

        Returns
        ----------
        True if credentials are available.
        """
        if not self.secrets_file.exists():
            logger.debug("Credentials file not found.")
            return False
        with self.secrets_file.open() as creds:
            credentials = json.load(creds)
            for key in Keys:
                setattr(self, key.suffix, credentials.get(key.suffix, None))
            return True

    def save(self, token: str = "", user_id: str = "", api_key: str = "", username: str = "") -> None:
        """save credentials to disk."""
        self.secrets_file.parent.mkdir(exist_ok=True, parents=True)
        with self.secrets_file.open("w") as f:
            json.dump(
                {
                    f"{Keys.USERNAME.suffix}": username,
                    f"{Keys.USER_ID.suffix}": user_id,
                    f"{Keys.API_KEY.suffix}": api_key,
                },
                f,
            )

        self.username = username
        self.user_id = user_id
        self.api_key = api_key
        logger.debug("credentials saved successfully")

    @classmethod
    def clear(cls) -> None:
        """remove credentials from disk and env variables."""
        if cls.secrets_file.exists():
            cls.secrets_file.unlink()
        for key in Keys:
            os.environ.pop(key.value, None)
        logger.debug("credentials removed successfully")

    @property
    def auth_header(self) -> Optional[str]:
        """authentication header used by lightning-cloud client."""
        if self.api_key:
            token = f"{self.user_id}:{self.api_key}"
            return f"Basic {base64.b64encode(token.encode('ascii')).decode('ascii')}"  # E501
        raise AttributeError(
            "Authentication Failed, no authentication header available. "
            "This is most likely a bug in the LightningCloud Framework"
        )

    def _run_server(self) -> None:
        """start a server to complete authentication."""
        AuthServer().login_with_browser(self)

    def authenticate(self) -> Optional[str]:
        """Performs end to end authentication flow.

        Returns
        ----------
        authorization header to use when authentication completes.
        """
        if self._with_env_var:
            logger.debug("successfully loaded credentials from env")
            return self.auth_header

        if not self.load():
            logger.debug("failed to load credentials, opening browser to get new.")
            self._run_server()
            return self.auth_header

        elif self.user_id and self.api_key:
            return self.auth_header

        raise ValueError(
            "We couldn't find any credentials linked to your account. "
            "Please try logging in using the CLI command `lightning login`"
        )


class AuthServer:
    def get_auth_url(self, port: int) -> str:
        redirect_uri = f"http://localhost:{port}/login-complete"
        params = urlencode(dict(redirectTo=redirect_uri))
        return f"{get_lightning_cloud_url()}/sign-in?{params}"

    def login_with_browser(self, auth: Auth) -> None:
        app = FastAPI()
        port = find_free_network_port()
        url = self.get_auth_url(port)
        try:
            # check if server is reachable or catch any network errors
            requests.head(url)
        except requests.ConnectionError as e:
            raise requests.ConnectionError(
                f"No internet connection available. Please connect to a stable internet connection \n{e}"  # E501
            )
        except requests.RequestException as e:
            raise requests.RequestException(
                f"An error occurred with the request. Please report this issue to Lightning Team \n{e}"  # E501
            )

        logger.info(f"login started for lightning.ai, opening {url}")
        click.launch(url)

        @app.get("/login-complete")
        async def save_token(request: Request, token="", key="", user_id: str = Query("", alias="userID")):
            if token:
                auth.save(token=token, username=user_id, user_id=user_id, api_key=key)
                logger.info("Authentication Successful")
            else:
                logger.warning(
                    "Authentication Failed. This is most likely because you're using an older version of the CLI. \n"  # E501
                    "Please try to update the CLI or open an issue with this information \n"  # E501
                    f"expected token in {request.query_params.items()}"
                )

            # Include the credentials in the redirect so that UI will also be logged in
            params = urlencode(dict(token=token, key=key, userID=user_id))

            return RedirectResponse(
                url=f"{get_lightning_cloud_url()}/me/apps?{params}",
                # The response background task is being executed right after the server finished writing the response
                background=BackgroundTask(stop_server),
            )

        def stop_server():
            server.should_exit = True

        server = uvicorn.Server(config=uvicorn.Config(app, port=port, log_level="error"))
        server.run()
