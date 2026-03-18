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
        assert "Artist 1 (D1) | artist ID: id1" in res
        assert "Artist 2 | artist ID: id2" in res


def test_get_release_group_cover_art_success():
    mock_result = {
        "images": [
            {
                "types": ["Front"],
                "image": "http://example.com/front.jpg",
                "thumbnails": {"500": "http://example.com/front-500.jpg"},
            }
        ]
    }

    class MockCache(dict):
        def set(self, key, value, expire=None):
            self[key] = value

    with (
        mock.patch("musicbrainzngs.get_release_group_image_list", return_value=mock_result),
        mock.patch("mcp_musicbrainz.server.cache", MockCache()),
    ):
        from mcp_musicbrainz.server import get_release_group_cover_art

        res = get_release_group_cover_art("test-rg-id")
        assert "Cover art for release group test-rg-id (1 images):" in res
        assert "[Front] http://example.com/front.jpg" in res
        assert "Thumbnail: http://example.com/front-500.jpg" in res


def test_get_release_group_cover_art_404():
    class MockCause:
        code = 404

    class MockCache(dict):
        def set(self, key, value, expire=None):
            self[key] = value

    # Simulate a 404 ResponseError from the Cover Art Archive
    mock_error = musicbrainzngs.ResponseError(cause=MockCause())

    with (
        mock.patch(
            "musicbrainzngs.get_release_group_image_list",
            side_effect=mock_error,
        ),
        mock.patch("mcp_musicbrainz.server.cache", MockCache()),
    ):
        from mcp_musicbrainz.server import get_release_group_cover_art

        res = get_release_group_cover_art("test-rg-id")
        expected_msg = "No cover art available for release group test-rg-id in the archive."
        assert expected_msg in res


def test_missing_entity_details():
    class MockCache(dict):
        def set(self, key, value, expire=None):
            self[key] = value

    mock_event = {"event": {"name": "Test Event", "type": "Festival", "id": "e1"}}
    mock_instrument = {"instrument": {"name": "Test Instrument", "type": "String", "id": "i1"}}
    mock_place = {"place": {"name": "Test Place", "type": "Venue", "id": "p1"}}
    mock_series = {"series": {"name": "Test Series", "type": "Tour", "id": "s1"}}

    with (
        mock.patch("musicbrainzngs.get_event_by_id", return_value=mock_event),
        mock.patch("musicbrainzngs.get_instrument_by_id", return_value=mock_instrument),
        mock.patch("musicbrainzngs.get_place_by_id", return_value=mock_place),
        mock.patch("musicbrainzngs.get_series_by_id", return_value=mock_series),
        mock.patch("mcp_musicbrainz.server.cache", MockCache()),
    ):
        from mcp_musicbrainz.server import (
            get_event_details,
            get_instrument_details,
            get_place_details,
            get_series_details,
        )

        assert "Name: Test Event" in get_event_details("e1")
        assert "Type: String" in get_instrument_details("i1")
        assert "Name: Test Place" in get_place_details("p1")
        assert "Name: Test Series" in get_series_details("s1")
