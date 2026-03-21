"""Tests for the cached_tool decorator."""

import musicbrainzngs

from mcp_musicbrainz.server import cached_tool


def test_cached_tool_caching():
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


def test_cached_tool_musicbrainz_error():
    @cached_tool()
    def error_func():
        raise musicbrainzngs.MusicBrainzError("MB Error")

    res = error_func()
    assert "MusicBrainz error: MB Error" in res


def test_cached_tool_unexpected_error():
    @cached_tool()
    def error_func():
        raise ValueError("unexpected")

    res = error_func()
    assert "An unexpected error occurred" in res
