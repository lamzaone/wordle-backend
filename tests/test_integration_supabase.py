import os

import pytest


pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    not os.getenv("TEST_SUPABASE_DATABASE_URL") or not os.getenv("TEST_SUPABASE_ACCESS_TOKEN"),
    reason="Set TEST_SUPABASE_DATABASE_URL and TEST_SUPABASE_ACCESS_TOKEN to run Supabase integration tests.",
)
def test_supabase_integration_configuration_is_explicit():
    database_url = os.environ["TEST_SUPABASE_DATABASE_URL"].lower()
    assert "sqlite" not in database_url
    assert "localhost" not in database_url
    assert "127.0.0.1" not in database_url
