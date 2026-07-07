"""Pytest configuration for fpx tests."""

#try:
#    import fpx
#except ImportError:
#    for p in site.getsitepackages() + [site.getusersitepackages()]:
#        if p and (Path(p) / 'fpx').exists():
#            sys.path.insert(0, str(p))
#            break

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_client():
    """Returns a mock fpx client for testing model methods."""
    client = MagicMock()
    client._account.chat.send_message = AsyncMock(return_value=True)
    client._account.review.review_answer = AsyncMock(return_value=True)
    return client
