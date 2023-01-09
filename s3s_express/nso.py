import base64
import hashlib
import os

import requests
from bs4 import BeautifulSoup

from s3s_express.constants import DEFAULT_USER_AGENT, IOS_APP_URL


class NSO:
    def __init__(self, session: requests.Session) -> None:
        self.session = session
        self._state: bytes | None = None
        self._verifier: bytes | None = None
        self._version: str | None = None

    @staticmethod
    def new_instance() -> "NSO":
        session = requests.Session()
        return NSO(session=session)

    @property
    def version(self) -> str:
        if self._version is None:
            self._version = self.get_version()
        return self._version

    def get_version(self) -> str:
        """Gets the current version of the NSO app. Necessary to access the API.

        Returns:
            str: The current version of the NSO app.
        """
        response = self.session.get(IOS_APP_URL)
        soup = BeautifulSoup(response.text, "html.parser")
        version = (
            soup.find("p", class_="whats-new__latest__version")
            .get_text()[7:]
            .strip()
        )
        return version

    @property
    def state(self) -> bytes:
        """Returns a base64url encoded random 36 byte string for the auth state.

        Returns:
            bytes: The auth state.
        """
        if self._state is None:
            self._state = self.generate_new_state()
        return self._state

    def generate_new_state(self) -> bytes:
        """Generates a new state.

        Returns:
            bytes: The auth state.
        """
        return base64.urlsafe_b64encode(os.urandom(36))

    @property
    def verifier(self) -> bytes:
        """Returns a base64url encoded random 32 byte string for the code
        verifier. This is used to generate the S256 code challenge. To align
        with node.js's crypto module, padding is removed.

        Returns:
            bytes: The code verifier, without padding.
        """
        if self._verifier is None:
            self._verifier = self.generate_new_verifier()
        return self._verifier

    def generate_new_verifier(self) -> bytes:
        """Generates a new verifier without padding.

        Returns:
            bytes: The code verifier, without padding.
        """
        verifier_ = base64.urlsafe_b64encode(os.urandom(32))
        return verifier_.replace(b"=", b"")

    def header(self, user_agent: str) -> dict[str, str]:
        """Returns the headers for the session.

        Args:
            user_agent (str): The user agent to use.

        Returns:
            dict[str, str]: The headers.
        """
        return {
            "Host": "accounts.nintendo.com",
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": user_agent,
            "Accept": (
                "text/html,"
                + "application/xhtml+xml,"
                + "application/xml;q=0.9,"
                + "image/webp,"
                + "image/apng,"
                + "*/*;q=0.8n"
            ),
            "DNT": "1",
            "Accept-Encoding": "gzip,deflate,br",
        }

    def generate_login_url(self, user_agent: str | None = None) -> str:
        """Log in to a Nintendo account and returns a session token.

        Args:
            user_agent (str): The user agent to use. Defaults to the default
                user agent found in constants.py.

        Returns:
            str: The session token.
        """
        # https://dev.to/mathewthe2/intro-to-nintendo-switch-rest-api-2cm7
        hash_ = hashlib.sha256()
        hash_.update(self.verifier)
        challenge = base64.urlsafe_b64encode(hash_.digest()).replace(b"=", b"")

        header = self.header(
            user_agent=user_agent
            if user_agent is not None
            else DEFAULT_USER_AGENT
        )
        params = {
            "state": self.state,
            "redirect_uri": "npf71b963c1b7b6d119://auth",
            "client_id": "71b963c1b7b6d119",
            "scope": ("openid user user.birthday user.mii user.screenName"),
            "response_type": "session_token_code",
            "session_token_code_challenge": challenge,
            "session_token_code_challenge_method": "S256",
            "theme": "login_form",
        }
        login_url = "https://accounts.nintendo.com/connect/1.0.0/authorize"
        response = self.session.get(login_url, headers=header, params=params)
        return response.url

    def parse_npf_uri(self, uri: str) -> str:
        """Parses the uri returned by the Nintendo login page and extracts the
        session token code. This is used to pass the challenge and verify that
        the user is who they say they are.

        Args:
            uri (str): The uri returned by the Nintendo login page.

        Returns:
            str: The session token code.
        """
        return uri.split("&")[1][len("session_token_code=") :]

    def get_session_token(self, session_token_code: str) -> str:
        """Gets the session token from the session token code.

        Args:
            session_token_code (str): The session token code.

        Returns:
            str: The session token.
        """
        header = {
            "User-Agent": f"OnlineLounge/{self.version} NASDKAPI Android",
            "Accept-Language": "en-US",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": "540",
            "Host": "accounts.nintendo.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
        }
        params = {
            "client_id": "71b963c1b7b6d119",
            "session_token_code": session_token_code,
            "session_token_code_verifier": self.verifier,
        }
        uri = "https://accounts.nintendo.com/connect/1.0.0/api/session_token"
        response = self.session.post(uri, headers=header, data=params)
        return response.json()["session_token"]
