import logging

from splatnet3_scraper import __version__
from splatnet3_scraper.auth.nso import NSO
from splatnet3_scraper.auth.tokens.environment_manager import (
    EnvironmentVariablesManager,
)
from splatnet3_scraper.auth.tokens.keychain import TokenKeychain
from splatnet3_scraper.auth.tokens.manager import TokenManager
from splatnet3_scraper.auth.tokens.regenerator import TokenRegenerator
from splatnet3_scraper.auth.tokens.token_typing import ORIGIN
from splatnet3_scraper.auth.tokens.tokens import Token
from splatnet3_scraper.constants import (
    DEFAULT_F_TOKEN_URL,
    DEFAULT_USER_AGENT,
    TOKENS,
)

logger = logging.getLogger(__name__)


class TokenManagerConstructor:
    """This class is used to construct a ``TokenManager`` object. This class
    should only contain static methods that are used to construct the
    ``TokenManager`` object.
    """

    @staticmethod
    def from_session_token(
        session_token: str,
        *,
        nso: NSO | None = None,
        f_token_url: str | list[str] | None = DEFAULT_F_TOKEN_URL,
    ) -> TokenManager:
        """Creates a ``TokenManager`` object from a session token. This method
        is the bare minimum needed to create a ``TokenManager`` object.

        Args:
            session_token (str): The session token to use.
            nso (NSO | None): An instance of the ``NSO`` class. If one is not
                provided, a new instance will be created. Defaults to None.
            f_token_url (str | list[str] | None): The URL(s) to use to generate
                tokens. If a list is provided, each URL will be tried in order
                until a token is successfully generated. If None is provided,
                the default URL provided by imink will be used. Defaults to
                None.
            env_manager (EnvironmentVariablesManager | None): An instance of the
                ``EnvironmentVariablesManager`` class. If one is not provided, a
                new instance will be created. Defaults to None.

        Returns:
            TokenManager: The ``TokenManager`` object.
        """
        if nso is None:
            nso = NSO(session=session_token)
        else:
            nso._session_token = session_token
        manager = TokenManager(
            nso=nso,
            f_token_url=f_token_url,
            origin="memory",
        )
        manager.add_token(session_token, TOKENS.SESSION_TOKEN)
        return manager

    @staticmethod
    def from_tokens(
        session_token: str,
        gtoken: str | None = None,
        bullet_token: str | None = None,
        *,
        nso: NSO | None = None,
        f_token_url: str | list[str] = DEFAULT_F_TOKEN_URL,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> TokenManager:
        """Creates a ``TokenManager`` object from a session token and other
        tokens. This method is the bare minimum needed to create a
        ``TokenManager`` object.

        Args:
            session_token (str): The session token to use.
            gtoken (str | None): The gtoken to use. If None is provided, a new
                gtoken will be generated.
            bullet_token (str | None): The bullet token to use. If None is
                provided, a new bullet token will be generated.
            nso (NSO | None): An instance of the ``NSO`` class. If one is not
                provided, a new instance will be created. Defaults to None.
            f_token_url (str | list[str] | None): The URL(s) to use to generate
                tokens. If a list is provided, each URL will be tried in order
                until a token is successfully generated. If None is provided,
                the default URL provided by imink will be used. Defaults to
                None.

        Returns:
            TokenManager: The ``TokenManager`` object.
        """
        if nso is None:
            nso = NSO(session=session_token)
        else:
            nso._session_token = session_token
        manager = TokenManager(
            nso=nso,
            f_token_url=f_token_url,
            origin="memory",
        )
        manager.add_token(session_token, TOKENS.SESSION_TOKEN)

        return manager
