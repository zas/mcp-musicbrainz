import unittest.mock as mock

import musicbrainzngs

from mcp_musicbrainz.server import cached_tool, search_artists


def test_cached_tool_decorator():
    # Mock the cache and the function
    class MockCache(dict):
        def set(self, key, value, expire=None):
            self[key] = value

    mock_cache = MockCache()

    with mock.patch("mcp_musicbrainz.server.cache", mock_cache):
        call_count = 0

        @cached_tool()
        def test_func(a, b=None):
            nonlocal call_count
            call_count += 1
            return f"result-{a}-{b}"

        # First call
        res1 = test_func(1, b=2)
        assert res1 == "result-1-2"
        assert call_count == 1

        # Second call (should be cached)
        res2 = test_func(1, b=2)
        assert res2 == "result-1-2"
        assert call_count == 1

        # Call with different args
        res3 = test_func(2, b=2)
        assert res3 == "result-2-2"
        assert call_count == 2


def test_cached_tool_error_handling():
    class MockCache(dict):
        def set(self, key, value, expire=None):
            self[key] = value

    with mock.patch("mcp_musicbrainz.server.cache", MockCache()):

        @cached_tool()
        def error_func():
            raise musicbrainzngs.MusicBrainzError("MB Error")

        res = error_func()
        assert "MusicBrainz error: MB Error" in res


def test_search_artists_mock():
    mock_result = {
        "artist-list": [
            {"name": "Artist 1", "id": "id1", "disambiguation": "D1"},
            {"name": "Artist 2", "id": "id2"},
        ]
    }

    class MockCache(dict):
        def set(self, key, value, expire=None):
            self[key] = value

    # Mock the cache to avoid actual disk writes in tests
    with (
        mock.patch("musicbrainzngs.search_artists", return_value=mock_result),
        mock.patch("mcp_musicbrainz.server.cache", MockCache()),
    ):
        res = search_artists("Test Artist")
        assert "Found 2 artists" in res
        assert "Artist 1 (D1) | ID: id1" in res
        assert "Artist 2 | ID: id2" in res
