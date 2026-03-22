import musicbrainzngs

from mcp_musicbrainz.server import (
    BROWSE_FUNCS,
    SEARCH_FUNCS,
    VALID_LINKED_TYPES,
    _fmt_duration,
    _fmt_rating,
    _fmt_tags,
    _format_performers,
    _format_tracks,
    _mb_error_message,
    browse_entities,
    search_entities,
)


class TestFmtDuration:
    def test_none(self):
        assert _fmt_duration(None) == "??:??"

    def test_zero(self):
        assert _fmt_duration(0) == "0:00"

    def test_empty_string(self):
        assert _fmt_duration("") == "??:??"

    def test_milliseconds(self):
        assert _fmt_duration(125000) == "2:05"

    def test_string_input(self):
        assert _fmt_duration("300000") == "5:00"

    def test_under_one_minute(self):
        assert _fmt_duration(45000) == "0:45"


class TestFmtRating:
    def test_with_rating(self):
        assert _fmt_rating({"rating": {"rating": "4.5", "votes-count": "3"}}) == "4.5/5 (3 votes)"

    def test_no_rating(self):
        assert _fmt_rating({}) == "N/A"

    def test_empty_rating(self):
        assert _fmt_rating({"rating": {}}) == "N/A"


class TestFmtTags:
    def test_sorted_by_count(self):
        entity = {"tag-list": [{"count": "1", "name": "rock"}, {"count": "3", "name": "metal"}]}
        assert _fmt_tags(entity) == "metal (3), rock (1)"

    def test_empty(self):
        assert _fmt_tags({}) == ""


class TestFormatTracks:
    def test_empty(self):
        assert _format_tracks([]) == []

    def test_single_medium(self):
        media = [
            {
                "format": "CD",
                "track-list": [
                    {
                        "number": "1",
                        "recording": {"id": "abc-123", "title": "Song", "length": "180000"},
                    }
                ],
            }
        ]
        result = _format_tracks(media)
        assert len(result) == 1
        assert "1. Song (3:00)" in result[0]
        assert "recording ID: abc-123" in result[0]
        assert "[CD]" not in result[0]

    def test_multi_medium_has_prefix(self):
        medium = {
            "format": "CD",
            "track-list": [
                {
                    "number": "1",
                    "recording": {"id": "abc-123", "title": "Track", "length": "60000"},
                }
            ],
        }
        result = _format_tracks([medium, medium])
        assert "[CD]" in result[0]

    def test_missing_length(self):
        media = [
            {
                "track-list": [
                    {"number": "1", "recording": {"title": "X"}},
                ]
            }
        ]
        result = _format_tracks(media)
        assert "??:??" in result[0]

    def test_missing_recording_id(self):
        media = [
            {
                "track-list": [
                    {"number": "1", "recording": {"title": "X", "length": "60000"}},
                ]
            }
        ]
        result = _format_tracks(media)
        assert "recording ID" not in result[0]

    def test_include_performers(self):
        media = [
            {
                "track-list": [
                    {
                        "number": "1",
                        "recording": {
                            "id": "abc-123",
                            "title": "Song",
                            "length": "180000",
                            "artist-relation-list": [
                                {
                                    "type": "instrument",
                                    "attribute-list": ["guitar"],
                                    "artist": {"name": "Alice"},
                                },
                            ],
                        },
                    }
                ],
            }
        ]
        result = _format_tracks(media, include_performers=True)
        assert len(result) == 2
        assert "Instrument (guitar): Alice" in result[1]

    def test_no_performers_by_default(self):
        media = [
            {
                "track-list": [
                    {
                        "number": "1",
                        "recording": {
                            "id": "abc-123",
                            "title": "Song",
                            "length": "180000",
                            "artist-relation-list": [
                                {
                                    "type": "instrument",
                                    "attribute-list": ["guitar"],
                                    "artist": {"name": "Alice"},
                                },
                            ],
                        },
                    }
                ],
            }
        ]
        result = _format_tracks(media)
        assert len(result) == 1


class TestFormatPerformers:
    def test_empty(self):
        assert _format_performers([]) == []

    def test_with_attributes(self):
        rels = [{"type": "instrument", "attribute-list": ["trombone"], "artist": {"name": "Bob"}}]
        result = _format_performers(rels)
        assert result == ["  - Instrument (trombone): Bob"]

    def test_without_attributes(self):
        rels = [{"type": "performer", "artist": {"name": "Carol"}}]
        result = _format_performers(rels)
        assert result == ["  - Performer: Carol"]


class TestFuncMaps:
    def test_search_funcs_not_empty(self):
        assert len(SEARCH_FUNCS) > 0

    def test_browse_funcs_not_empty(self):
        assert len(BROWSE_FUNCS) > 0

    def test_all_search_funcs_callable(self):
        for name, func in SEARCH_FUNCS.items():
            assert callable(func), f"{name} is not callable"

    def test_all_browse_funcs_callable(self):
        for name, func in BROWSE_FUNCS.items():
            assert callable(func), f"{name} is not callable"


class TestInputValidation:
    def test_search_invalid_entity_type(self):
        result = search_entities("bogus", "test")
        assert "Invalid entity type" in result
        assert "bogus" in result

    def test_browse_invalid_entity_type(self):
        result = browse_entities("bogus", "artist", "some-id")
        assert "Invalid entity type" in result

    def test_browse_invalid_linked_type(self):
        result = browse_entities("releases", "bogus", "some-id")
        assert "Invalid linked type" in result

    def test_browse_normalizes_hyphen(self):
        # "release-group" should be accepted and normalized to "release_group"
        assert "release_group" in VALID_LINKED_TYPES


class TestErrorMessage:
    def test_generic_error(self):
        err = musicbrainzngs.MusicBrainzError("something broke")
        msg = _mb_error_message(err)
        assert "something broke" in msg
