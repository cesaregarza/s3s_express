import pathlib
import time
from typing import Literal
from unittest.mock import MagicMock, mock_open, patch

import freezegun
import pytest
import pytest_mock
import requests

from splatnet3_scraper.auth.tokens.manager import ManagerOrigin, TokenManager
from splatnet3_scraper.constants import IMINK_URL, TOKENS

ftoken_urls = [
    "ftoken_url_1",
    "ftoken_url_2",
    "ftoken_url_3",
    "ftoken_url_4",
]

base_token_manager_path = "splatnet3_scraper.auth.tokens.manager"
token_manager_path = base_token_manager_path + ".TokenManager"


class TestTokenManager:
    @pytest.fixture
    def mock_token_manager(self) -> TokenManager:
        with (
            patch(base_token_manager_path + ".NSO"),
            patch(base_token_manager_path + ".EnvironmentVariablesManager"),
            patch(base_token_manager_path + ".TokenKeychain"),
            patch(base_token_manager_path + ".ManagerOrigin"),
        ):
            return TokenManager()

    @pytest.mark.parametrize(
        "with_nso",
        [True, False],
        ids=["with_nso", "without_nso"],
    )
    @pytest.mark.parametrize(
        "f_token_url",
        [
            ftoken_urls[0],
            ftoken_urls,
            None,
        ],
        ids=["single_url", "multiple_urls", "default_url"],
    )
    @pytest.mark.parametrize(
        "with_env_manager",
        [True, False],
        ids=["with_env_manager", "without_env_manager"],
    )
    @pytest.mark.parametrize(
        "with_origin",
        [True, False],
        ids=["with_origin", "without_origin"],
    )
    @pytest.mark.parametrize(
        "with_origin_data",
        [True, False],
        ids=["with_origin_data", "without_origin_data"],
    )
    def test_init(
        self,
        with_nso: bool,
        f_token_url: str | list[str] | None,
        with_env_manager: bool,
        with_origin: bool,
        with_origin_data: bool,
    ) -> None:
        nso = MagicMock()
        env_manager = MagicMock()

        with (
            patch(base_token_manager_path + ".NSO") as mock_nso,
            patch(
                base_token_manager_path + ".EnvironmentVariablesManager"
            ) as mock_env_manager,
            patch(base_token_manager_path + ".TokenKeychain") as mock_keychain,
            patch(base_token_manager_path + ".ManagerOrigin") as mock_origin,
        ):
            mock_nso.new_instance.return_value = nso
            mock_env_manager.return_value = env_manager

            instance = TokenManager(
                nso=nso if with_nso else None,
                f_token_url=f_token_url,
                env_manager=env_manager if with_env_manager else None,
                origin="origin" if with_origin else "memory",
                origin_data="test_data" if with_origin_data else None,
            )

            if with_nso:
                mock_nso.new_instance.assert_not_called()
            else:
                mock_nso.new_instance.assert_called_once()

            if with_env_manager:
                mock_env_manager.assert_not_called()
            else:
                mock_env_manager.assert_called_once()

            if isinstance(f_token_url, str):
                expected_f_token_url = [f_token_url]
            elif f_token_url is None:
                expected_f_token_url = [IMINK_URL]
            else:
                expected_f_token_url = f_token_url

            assert instance.nso == nso
            assert instance.f_token_url == expected_f_token_url
            assert instance.env_manager == env_manager
            assert instance.keychain == mock_keychain.return_value
            assert instance.origin == mock_origin.return_value

            mock_origin.assert_called_once_with(
                "origin" if with_origin else "memory",
                "test_data" if with_origin_data else None,
            )

    def test_flag_origin(self, mock_token_manager: TokenManager) -> None:
        mock_token_manager.flag_origin("test_origin", "test_data")
        assert isinstance(mock_token_manager.origin, ManagerOrigin)
        assert mock_token_manager.origin.origin == "test_origin"
        assert mock_token_manager.origin.data == "test_data"

    @pytest.mark.parametrize(
        "token_name",
        [
            TOKENS.SESSION_TOKEN,
            TOKENS.GTOKEN,
            TOKENS.BULLET_TOKEN,
        ],
        ids=["session_token", "gtoken", "bullet_token"],
    )
    @pytest.mark.parametrize(
        "raise_exception",
        [True, False],
        ids=["raise_exception", "no_exception"],
    )
    def test_add_token(
        self,
        mock_token_manager: TokenManager,
        token_name: str,
        raise_exception: bool,
    ) -> None:
        token = MagicMock()
        token.name = token_name
        nso = mock_token_manager.nso

        def simulate_add_token(*args, **kwargs):
            if raise_exception:
                raise ValueError("test")
            return token

        mock_token_manager.keychain.add_token.side_effect = simulate_add_token

        if raise_exception:
            with pytest.raises(ValueError):
                mock_token_manager.add_token(token)
            return

        mock_token_manager.add_token(token)
        mock_token_manager.keychain.add_token.assert_called_once_with(
            token, None, None
        )
        if token_name == TOKENS.GTOKEN:
            assert nso._gtoken == token.value
        else:
            assert nso._gtoken != token.value

        if token_name == TOKENS.SESSION_TOKEN:
            assert nso._session_token == token.value
        else:
            assert nso._session_token != token.value

    @pytest.mark.parametrize(
        "raise_exception",
        [True, False],
        ids=["raise_exception", "no_exception"],
    )
    def test_get_token(
        self, mock_token_manager: TokenManager, raise_exception: bool
    ) -> None:
        mock_token = MagicMock()

        def simulate_get(*args, **kwargs):
            if raise_exception:
                raise ValueError("test")
            return mock_token

        mock_token_manager.keychain.get.side_effect = simulate_get

        if raise_exception:
            with pytest.raises(ValueError):
                mock_token_manager.get_token("test")
            return

        token = mock_token_manager.get_token("test")
        mock_token_manager.keychain.get.assert_called_once_with(
            "test", full_token=True
        )
        assert token == mock_token
