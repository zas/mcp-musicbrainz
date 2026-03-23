"""Tests for all MCP tools using mocked musicbrainzngs responses.

Mock data is sourced from real MusicBrainz API responses for Reverend Bizarre.
See conftest.py for fixtures and response constants.
"""

import unittest.mock as mock

import musicbrainzngs

from mcp_musicbrainz.server import (
    _search_entities,
    browse_entities,
    get_album_recording_rels,
    get_album_tracks,
    get_area_details,
    get_artist_details,
    get_cover_art_urls,
    get_entity_relationships,
    get_event_details,
    get_instrument_details,
    get_label_details,
    get_place_details,
    get_recording_details,
    get_release_details,
    get_release_group_cover_art,
    get_release_group_details,
    get_series_details,
    get_work_details,
    search_areas,
    search_artists,
    search_entities_fuzzy,
    search_events,
    search_labels,
    search_places,
    search_recordings,
    search_release_groups,
    search_releases,
)
from tests.conftest import (
    BROWSE_RELEASE_GROUPS_RESPONSE,
    BROWSE_RELEASES_FOR_RG_RESPONSE,
    BROWSE_RELEASES_RESPONSE,
    BROWSE_RELEASES_WITH_LABELS_RESPONSE,
    BURN_RECORDING_ID,
    BURN_WORK_ID,
    COVER_ART_RESPONSE,
    FINLAND_AREA_ID,
    GET_AREA_RESPONSE,
    GET_ARTIST_RELS_RESPONSE,
    GET_ARTIST_RESPONSE,
    GET_EVENT_RESPONSE,
    GET_INSTRUMENT_RESPONSE,
    GET_LABEL_RESPONSE,
    GET_PLACE_RESPONSE,
    GET_RECORDING_RESPONSE,
    GET_RELEASE_GROUP_RESPONSE,
    GET_RELEASE_RESPONSE,
    GET_RELEASE_WITH_RECORDING_ARTIST_RELS,
    GET_RELEASE_WITH_RECORDING_PLACE_RELS,
    GET_SERIES_RESPONSE,
    GET_WORK_RESPONSE,
    RB_ARTIST_ID,
    RECTORY_RELEASE_ID,
    RECTORY_RG_ID,
    RG_COVER_ART_RESPONSE,
    SEARCH_ARTISTS_RESPONSE,
    SEARCH_RECORDINGS_RESPONSE,
    SEARCH_RELEASE_GROUPS_RESPONSE,
    SEARCH_RELEASES_RESPONSE,
    SINISTER_LABEL_ID,
)

# ── search_entities ──────────────────────────────────────────────────────────


class TestSearchEntities:
    def test_artist_search(self):
        with mock.patch.dict(
            "mcp_musicbrainz.server.SEARCH_FUNCS", {"artist": mock.Mock(return_value=SEARCH_ARTISTS_RESPONSE)}
        ):
            res = _search_entities("artist", "Reverend Bizarre", limit=2)
        assert "Found 2 results" in res
        assert "Reverend Bizarre (Finnish doom metal band)" in res
        assert f"artist ID: {RB_ARTIST_ID}" in res

    def test_invalid_entity_type(self):
        res = _search_entities("bogus", "test")
        assert "Invalid entity type" in res

    def test_empty_results(self):
        with mock.patch.dict(
            "mcp_musicbrainz.server.SEARCH_FUNCS", {"artist": mock.Mock(return_value={"artist-list": []})}
        ):
            res = _search_entities("artist", "nonexistent")
        assert "Found 0 results" in res


# ── search_entities_fuzzy ────────────────────────────────────────────────────


class TestSearchEntitiesFuzzy:
    def test_exact_match_found(self):
        with mock.patch.dict(
            "mcp_musicbrainz.server.SEARCH_FUNCS", {"artist": mock.Mock(return_value=SEARCH_ARTISTS_RESPONSE)}
        ):
            res = search_entities_fuzzy("artist", "Reverend Bizarre")
        assert "Found 2 results" in res

    def test_fallback_to_fuzzy(self):
        empty = {"artist-list": []}
        m = mock.Mock(side_effect=[empty, SEARCH_ARTISTS_RESPONSE])
        with mock.patch.dict("mcp_musicbrainz.server.SEARCH_FUNCS", {"artist": m}):
            res = search_entities_fuzzy("artist", "Reverand Bizzare")
        assert "Found 2 results" in res
        assert m.call_count == 2


# ── browse_entities ──────────────────────────────────────────────────────────


class TestBrowseEntities:
    def test_browse_releases(self):
        with mock.patch("musicbrainzngs.browse_releases", return_value=BROWSE_RELEASES_RESPONSE):
            res = browse_entities("releases", "artist", RB_ARTIST_ID, limit=2)
        assert "Showing 2 of 48 releases" in res
        assert "Practice Sessions" in res
        assert "Slice of Doom" in res

    def test_browse_release_groups(self):
        with mock.patch("musicbrainzngs.browse_release_groups", return_value=BROWSE_RELEASE_GROUPS_RESPONSE):
            res = browse_entities("release-groups", "artist", RB_ARTIST_ID, limit=3)
        assert "Showing 3 of 28" in res
        assert "In the Rectory" in res

    def test_invalid_entity_type(self):
        res = browse_entities("bogus", "artist", "some-id")
        assert "Invalid entity type" in res

    def test_invalid_linked_type(self):
        res = browse_entities("releases", "bogus", "some-id")
        assert "Invalid linked type" in res

    def test_hyphen_normalization(self):
        """release-group should be accepted as linked_type."""
        with mock.patch("musicbrainzngs.browse_releases", return_value=BROWSE_RELEASES_RESPONSE):
            res = browse_entities("releases", "release-group", RECTORY_RG_ID)
        assert "Showing" in res

    def test_includes_labels(self):
        """includes=['labels'] should pass through and show label info in output."""
        mock_fn = mock.Mock(return_value=BROWSE_RELEASES_WITH_LABELS_RESPONSE)
        with mock.patch.dict("mcp_musicbrainz.server.BROWSE_FUNCS", {"releases": mock_fn}):
            res = browse_entities("releases", "artist", RB_ARTIST_ID, includes=["labels"])
        assert mock_fn.call_args[1]["includes"] == ["labels"]
        assert "Sinister Figure (SFGCD10)" in res
        assert "[no label]" in res


# ── search_artists ───────────────────────────────────────────────────────────


class TestSearchArtists:
    def test_basic_search(self):
        with mock.patch("musicbrainzngs.search_artists", return_value=SEARCH_ARTISTS_RESPONSE):
            res = search_artists("Reverend Bizarre")
        assert "Found 2 artists" in res
        assert "Reverend Bizarre (Finnish doom metal band)" in res
        assert "Bizarre (US rapper)" in res

    def test_with_country_filter(self):
        with mock.patch("musicbrainzngs.search_artists", return_value=SEARCH_ARTISTS_RESPONSE) as m:
            search_artists("Reverend Bizarre", country="FI")
        assert m.call_args[1]["country"] == "FI"

    def test_with_type_filter(self):
        with mock.patch("musicbrainzngs.search_artists", return_value=SEARCH_ARTISTS_RESPONSE) as m:
            search_artists("Reverend Bizarre", artist_type="group")
        assert m.call_args[1]["type"] == "group"

    def test_with_offset(self):
        with mock.patch("musicbrainzngs.search_artists", return_value=SEARCH_ARTISTS_RESPONSE) as m:
            search_artists("Reverend Bizarre", offset=5)
        assert m.call_args[1]["offset"] == 5

    def test_strict(self):
        with mock.patch("musicbrainzngs.search_artists", return_value=SEARCH_ARTISTS_RESPONSE) as m:
            search_artists("Reverend Bizarre", country="FI", strict=True)
        assert m.call_args[1]["strict"] is True

    def test_with_begin_date(self):
        with mock.patch("musicbrainzngs.search_artists", return_value=SEARCH_ARTISTS_RESPONSE) as m:
            search_artists("Reverend Bizarre", begin_date="1999")
        assert m.call_args[1]["begin"] == "1999"

    def test_with_end_date(self):
        with mock.patch("musicbrainzngs.search_artists", return_value=SEARCH_ARTISTS_RESPONSE) as m:
            search_artists("Reverend Bizarre", end_date="2007")
        assert m.call_args[1]["end"] == "2007"


# ── search_labels / search_areas / search_events / search_places (begin/end) ─


EMPTY_AREA_RESPONSE = {"area-list": []}
EMPTY_LABEL_RESPONSE = {"label-list": []}
EMPTY_EVENT_RESPONSE = {"event-list": []}
EMPTY_PLACE_RESPONSE = {"place-list": []}


class TestSearchLabelsBeginEnd:
    def test_with_begin_date(self):
        m = mock.Mock(return_value=EMPTY_LABEL_RESPONSE)
        with mock.patch.dict("mcp_musicbrainz.server.SEARCH_FUNCS", {"label": m}):
            search_labels("test", begin_date="2020")
        assert "begin:2020" in m.call_args[1]["query"]

    def test_with_end_date(self):
        m = mock.Mock(return_value=EMPTY_LABEL_RESPONSE)
        with mock.patch.dict("mcp_musicbrainz.server.SEARCH_FUNCS", {"label": m}):
            search_labels("test", end_date="2023")
        assert "end:2023" in m.call_args[1]["query"]


class TestSearchAreasBeginEnd:
    def test_with_begin_date(self):
        m = mock.Mock(return_value=EMPTY_AREA_RESPONSE)
        with mock.patch.dict("mcp_musicbrainz.server.SEARCH_FUNCS", {"area": m}):
            search_areas("test", begin_date="1990")
        assert "begin:1990" in m.call_args[1]["query"]

    def test_with_end_date(self):
        m = mock.Mock(return_value=EMPTY_AREA_RESPONSE)
        with mock.patch.dict("mcp_musicbrainz.server.SEARCH_FUNCS", {"area": m}):
            search_areas("test", end_date="2000")
        assert "end:2000" in m.call_args[1]["query"]


class TestSearchEventsBeginEnd:
    def test_with_begin_date(self):
        m = mock.Mock(return_value=EMPTY_EVENT_RESPONSE)
        with mock.patch.dict("mcp_musicbrainz.server.SEARCH_FUNCS", {"event": m}):
            search_events("test", begin_date="2024-06-15")
        assert "begin:2024-06-15" in m.call_args[1]["query"]

    def test_with_end_date(self):
        m = mock.Mock(return_value=EMPTY_EVENT_RESPONSE)
        with mock.patch.dict("mcp_musicbrainz.server.SEARCH_FUNCS", {"event": m}):
            search_events("test", end_date="2024-06-17")
        assert "end:2024-06-17" in m.call_args[1]["query"]


class TestSearchPlacesBeginEnd:
    def test_with_begin_date(self):
        m = mock.Mock(return_value=EMPTY_PLACE_RESPONSE)
        with mock.patch.dict("mcp_musicbrainz.server.SEARCH_FUNCS", {"place": m}):
            search_places("test", begin_date="1971")
        assert "begin:1971" in m.call_args[1]["query"]

    def test_with_end_date(self):
        m = mock.Mock(return_value=EMPTY_PLACE_RESPONSE)
        with mock.patch.dict("mcp_musicbrainz.server.SEARCH_FUNCS", {"place": m}):
            search_places("test", end_date="1999-10")
        assert "end:1999-10" in m.call_args[1]["query"]


# ── search_releases ──────────────────────────────────────────────────────────


class TestSearchReleases:
    def test_basic_search(self):
        with mock.patch("musicbrainzngs.search_releases", return_value=SEARCH_RELEASES_RESPONSE):
            res = search_releases(title="In the Rectory")
        assert "Found 1 releases" in res
        assert "Reverend Bizarre" in res
        assert f"release ID: {RECTORY_RELEASE_ID}" in res
        assert "Sinister Figure" in res
        assert "SY-002" in res
        assert '12" Vinyl' in res

    def test_no_params(self):
        res = search_releases()
        assert "Please provide at least one search parameter" in res

    def test_with_offset(self):
        with mock.patch("musicbrainzngs.search_releases", return_value=SEARCH_RELEASES_RESPONSE) as m:
            search_releases(title="In the Rectory", offset=10)
        assert m.call_args[1]["offset"] == 10

    def test_strict(self):
        with mock.patch("musicbrainzngs.search_releases", return_value=SEARCH_RELEASES_RESPONSE) as m:
            search_releases(title="In the Rectory", artist="Reverend Bizarre", strict=True)
        assert m.call_args[1]["strict"] is True

    def test_with_catno_filter(self):
        with mock.patch("musicbrainzngs.search_releases", return_value=SEARCH_RELEASES_RESPONSE) as m:
            search_releases(catno="SY-002")
        assert m.call_args[1]["catno"] == "SY-002"

    def test_with_format_filter(self):
        with mock.patch("musicbrainzngs.search_releases", return_value=SEARCH_RELEASES_RESPONSE) as m:
            search_releases(format='12" Vinyl')
        assert m.call_args[1]["format"] == '12" Vinyl'

    def test_with_barcode_filter(self):
        with mock.patch("musicbrainzngs.search_releases", return_value=SEARCH_RELEASES_RESPONSE) as m:
            search_releases(barcode="6420074201020")
        assert m.call_args[1]["barcode"] == "6420074201020"

    def test_with_label_filter(self):
        with mock.patch("musicbrainzngs.search_releases", return_value=SEARCH_RELEASES_RESPONSE) as m:
            search_releases(label="Sinister Figure")
        assert m.call_args[1]["label"] == "Sinister Figure"


# ── search_recordings ────────────────────────────────────────────────────────


class TestSearchRecordings:
    def test_basic_search(self):
        with mock.patch("musicbrainzngs.search_recordings", return_value=SEARCH_RECORDINGS_RESPONSE):
            res = search_recordings(title="Burn in Hell!")
        assert "Found 1 recordings" in res
        assert "Reverend Bizarre" in res
        assert f"recording ID: {BURN_RECORDING_ID}" in res

    def test_with_artist_filter(self):
        with mock.patch("musicbrainzngs.search_recordings", return_value=SEARCH_RECORDINGS_RESPONSE) as m:
            search_recordings(title="Burn in Hell!", artist="Reverend Bizarre")
        assert m.call_args[1]["artist"] == "Reverend Bizarre"

    def test_no_params(self):
        res = search_recordings()
        assert "Please provide at least one search parameter" in res

    def test_with_offset(self):
        with mock.patch("musicbrainzngs.search_recordings", return_value=SEARCH_RECORDINGS_RESPONSE) as m:
            search_recordings(title="Burn in Hell!", offset=10)
        assert m.call_args[1]["offset"] == 10

    def test_strict(self):
        with mock.patch("musicbrainzngs.search_recordings", return_value=SEARCH_RECORDINGS_RESPONSE) as m:
            search_recordings(title="Burn in Hell!", artist="Reverend Bizarre", strict=True)
        assert m.call_args[1]["strict"] is True


# ── search_release_groups ────────────────────────────────────────────────────


class TestSearchReleaseGroups:
    def test_basic_search(self):
        with mock.patch("musicbrainzngs.search_release_groups", return_value=SEARCH_RELEASE_GROUPS_RESPONSE):
            res = search_release_groups(title="In the Rectory")
        assert "Found 1 release groups" in res
        assert f"release-group ID: {RECTORY_RG_ID}" in res

    def test_with_artist_filter(self):
        with mock.patch("musicbrainzngs.search_release_groups", return_value=SEARCH_RELEASE_GROUPS_RESPONSE) as m:
            search_release_groups(title="In the Rectory", artist="Reverend Bizarre")
        assert m.call_args[1]["artist"] == "Reverend Bizarre"

    def test_with_type_filter(self):
        with mock.patch("musicbrainzngs.search_release_groups", return_value=SEARCH_RELEASE_GROUPS_RESPONSE) as m:
            search_release_groups(artist="Reverend Bizarre", release_group_type="album")
        assert m.call_args[1]["type"] == "album"

    def test_no_params(self):
        res = search_release_groups()
        assert "Please provide at least one search parameter" in res

    def test_with_offset(self):
        with mock.patch("musicbrainzngs.search_release_groups", return_value=SEARCH_RELEASE_GROUPS_RESPONSE) as m:
            search_release_groups(title="In the Rectory", offset=15)
        assert m.call_args[1]["offset"] == 15

    def test_strict(self):
        with mock.patch("musicbrainzngs.search_release_groups", return_value=SEARCH_RELEASE_GROUPS_RESPONSE) as m:
            search_release_groups(title="In the Rectory", artist="Reverend Bizarre", strict=True)
        assert m.call_args[1]["strict"] is True


# ── get_artist_details ───────────────────────────────────────────────────────


class TestGetArtistDetails:
    def _mock_both(self):
        return (
            mock.patch("musicbrainzngs.get_artist_by_id", return_value=GET_ARTIST_RESPONSE),
            mock.patch("musicbrainzngs.browse_release_groups", return_value=BROWSE_RELEASE_GROUPS_RESPONSE),
        )

    def test_full_output(self):
        with self._mock_both()[0], self._mock_both()[1]:
            res = get_artist_details(RB_ARTIST_ID)
        assert "Name: Reverend Bizarre" in res
        assert "Type: Group" in res
        assert "Country: FI" in res
        assert "Life-span: 1995 to 2007" in res
        assert "doom metal (4)" in res
        assert "5/5 (3 votes)" in res
        assert "Reverand Bizarre" in res
        assert "bandcamp" in res
        assert "In the Rectory" in res
        assert f"MBID: {RB_ARTIST_ID}" in res
        assert "Disambiguation: Finnish doom metal band" in res
        assert "Annotation:\nFormed in Loimaa, Finland." in res

    def test_alias_limit(self):
        with self._mock_both()[0], self._mock_both()[1]:
            res = get_artist_details(RB_ARTIST_ID, alias_limit=2)
        # Only 2 of 4 aliases should appear
        assert "Reverand Bizarre" in res
        assert "Reverend Bizare" in res
        assert "Reverend Bizzarre" not in res

    def test_discography_limit(self):
        with (
            mock.patch("musicbrainzngs.get_artist_by_id", return_value=GET_ARTIST_RESPONSE),
            mock.patch("musicbrainzngs.browse_release_groups", return_value=BROWSE_RELEASE_GROUPS_RESPONSE) as m,
        ):
            get_artist_details(RB_ARTIST_ID, discography_limit=1)
        assert m.call_args[1]["limit"] == 1


# ── get_release_details ──────────────────────────────────────────────────────


class TestGetReleaseDetails:
    def test_full_output(self):
        with mock.patch("musicbrainzngs.get_release_by_id", return_value=GET_RELEASE_RESPONSE):
            res = get_release_details(RECTORY_RELEASE_ID)
        assert "Title: In the Rectory of the Bizarre Reverend" in res
        assert "Artist: Reverend Bizarre" in res
        assert "Date: 2002-03-28" in res
        assert "Country: FI" in res
        assert "Barcode: 6420074201020" in res
        assert "Sinister Figure (SFGCD10)" in res
        assert "Tags: doom metal (2)" in res
        assert f"release-group ID: {RECTORY_RG_ID}" in res
        assert "1. Burn in Hell! (8:52)" in res
        assert "6. Cirith Ungol (21:09)" in res
        assert f"recording ID: {BURN_RECORDING_ID}" in res
        assert "Disambiguation: first press" in res
        assert "Annotation:\nRecorded at Tico-Tico Studio." in res

    def test_error_hint(self):
        """Error message should suggest get_release_group_details."""
        err = musicbrainzngs.ResponseError(cause=type("Cause", (), {"code": 400, "reason": "Bad Request"})())
        with mock.patch("musicbrainzngs.get_release_by_id", side_effect=err):
            res = get_release_details("wrong-id")
        assert "get_release_group_details" in res


# ── get_recording_details ────────────────────────────────────────────────────


class TestGetRecordingDetails:
    def test_full_output(self):
        with mock.patch("musicbrainzngs.get_recording_by_id", return_value=GET_RECORDING_RESPONSE):
            res = get_recording_details(BURN_RECORDING_ID)
        assert "Title: Burn in Hell!" in res
        assert "Artist: Reverend Bizarre" in res
        assert "Duration: 8:52" in res
        assert "FISFS0404002" in res
        assert "doom metal (2)" in res
        assert "Rating: 4.25/5 (2 votes)" in res
        assert "Performers (3):" in res
        assert "Instrument (bass guitar): Kimi Kärki" in res
        assert "Instrument (drums (drum set)): Earl of Void" in res
        assert "Vocal (lead vocals): Albert Witchfinder" in res
        assert "Works (1):" in res
        assert "Burn in Hell" in res
        assert "Composer: Dee Snider" in res
        assert f"work ID: {BURN_WORK_ID}" in res
        assert "Appears on (3 releases)" in res
        # No disambiguation or annotation in mock data — should be absent
        assert "Disambiguation:" not in res
        assert "Annotation:" not in res

    def test_releases_limit(self):
        with mock.patch("musicbrainzngs.get_recording_by_id", return_value=GET_RECORDING_RESPONSE):
            res = get_recording_details(BURN_RECORDING_ID, releases_limit=1)
        assert "Appears on (3 releases)" in res
        assert "... and 2 more" in res
        assert "browse_entities" in res

    def test_no_truncation_hint_when_all_shown(self):
        with mock.patch("musicbrainzngs.get_recording_by_id", return_value=GET_RECORDING_RESPONSE):
            res = get_recording_details(BURN_RECORDING_ID, releases_limit=25)
        assert "... and" not in res


# ── get_album_tracks ─────────────────────────────────────────────────────────


class TestGetAlbumTracks:
    def test_tracklist(self):
        with (
            mock.patch("musicbrainzngs.get_release_group_by_id", return_value=GET_RELEASE_GROUP_RESPONSE),
            mock.patch("musicbrainzngs.get_release_by_id", return_value=GET_RELEASE_RESPONSE),
        ):
            res = get_album_tracks(RECTORY_RG_ID)
        assert "Burn in Hell!" in res
        assert "Cirith Ungol" in res
        assert f"release ID: {RECTORY_RELEASE_ID}" in res
        assert f"recording ID: {BURN_RECORDING_ID}" in res
        assert "Instrument (bass guitar): Kimi Kärki" in res
        assert "Vocal (lead vocals): Albert Witchfinder" in res

    def test_multi_release_hint(self):
        with (
            mock.patch("musicbrainzngs.get_release_group_by_id", return_value=GET_RELEASE_GROUP_RESPONSE),
            mock.patch("musicbrainzngs.get_release_by_id", return_value=GET_RELEASE_RESPONSE),
        ):
            res = get_album_tracks(RECTORY_RG_ID)
        assert "2 releases available" in res
        assert "get_release_group_details" in res

    def test_single_release_no_hint(self):
        single_rg = {
            "release-group": {
                "release-list": [{"id": RECTORY_RELEASE_ID, "title": "Test"}],
            }
        }
        with (
            mock.patch("musicbrainzngs.get_release_group_by_id", return_value=single_rg),
            mock.patch("musicbrainzngs.get_release_by_id", return_value=GET_RELEASE_RESPONSE),
        ):
            res = get_album_tracks(RECTORY_RG_ID)
        assert "releases available" not in res

    def test_no_releases(self):
        empty_rg = {"release-group": {"release-list": []}}
        with mock.patch("musicbrainzngs.get_release_group_by_id", return_value=empty_rg):
            res = get_album_tracks(RECTORY_RG_ID)
        assert "No releases found" in res

    def test_no_performer_credits_hint(self):
        """When no recordings have artist-relation-list, show a guidance hint."""
        no_credits_release = {
            "release": {
                "id": RECTORY_RELEASE_ID,
                "title": "Test Album",
                "date": "2022",
                "medium-list": [
                    {
                        "position": "1",
                        "track-list": [
                            {"number": "1", "recording": {"id": "rec-1", "title": "Track 1", "length": "180000"}},
                        ],
                    }
                ],
            }
        }
        single_rg = {"release-group": {"release-list": [{"id": RECTORY_RELEASE_ID}]}}
        with (
            mock.patch("musicbrainzngs.get_release_group_by_id", return_value=single_rg),
            mock.patch("musicbrainzngs.get_release_by_id", return_value=no_credits_release),
        ):
            res = get_album_tracks(RECTORY_RG_ID)
        assert "No per-track performer credits found" in res
        assert "get_recording_details" in res
        assert "get_entity_relationships" in res

    def test_has_performers_no_hint(self):
        """When recordings have performer credits, no hint is shown."""
        with (
            mock.patch("musicbrainzngs.get_release_group_by_id", return_value=GET_RELEASE_GROUP_RESPONSE),
            mock.patch("musicbrainzngs.get_release_by_id", return_value=GET_RELEASE_RESPONSE),
        ):
            res = get_album_tracks(RECTORY_RG_ID)
        assert "No per-track performer credits found" not in res


# ── get_album_recording_rels ─────────────────────────────────────────────────


class TestGetAlbumRecordingRels:
    def test_place_rels(self):
        with (
            mock.patch("musicbrainzngs.get_release_group_by_id", return_value=GET_RELEASE_GROUP_RESPONSE),
            mock.patch("musicbrainzngs.get_release_by_id", return_value=GET_RELEASE_WITH_RECORDING_PLACE_RELS),
        ):
            res = get_album_recording_rels(RECTORY_RG_ID, "place")
        assert "Tico-Tico Studio" in res
        assert "Finnvox Studios" in res
        assert "Recorded at" in res
        assert "Mixed at" in res
        assert "place ID: place-studio-1" in res
        assert "2001-10" in res
        assert f"release ID: {RECTORY_RELEASE_ID}" in res

    def test_artist_rels(self):
        with (
            mock.patch("musicbrainzngs.get_release_group_by_id", return_value=GET_RELEASE_GROUP_RESPONSE),
            mock.patch("musicbrainzngs.get_release_by_id", return_value=GET_RELEASE_WITH_RECORDING_ARTIST_RELS),
        ):
            res = get_album_recording_rels(RECTORY_RG_ID, "artist")
        assert "Anssi Kippo" in res
        assert "Engineer" in res
        assert "artist ID: artist-eng-1" in res

    def test_deduplication(self):
        with (
            mock.patch("musicbrainzngs.get_release_group_by_id", return_value=GET_RELEASE_GROUP_RESPONSE),
            mock.patch("musicbrainzngs.get_release_by_id", return_value=GET_RELEASE_WITH_RECORDING_PLACE_RELS),
        ):
            res = get_album_recording_rels(RECTORY_RG_ID, "place")
        assert res.count("Tico-Tico Studio") == 1

    def test_no_rels(self):
        no_rels_release = {
            "release": {
                "id": RECTORY_RELEASE_ID,
                "title": "Test",
                "date": "2022",
                "medium-list": [
                    {
                        "position": "1",
                        "track-list": [
                            {"number": "1", "recording": {"id": "rec-1", "title": "Track 1", "length": "180000"}},
                        ],
                    }
                ],
            }
        }
        single_rg = {"release-group": {"release-list": [{"id": RECTORY_RELEASE_ID}]}}
        with (
            mock.patch("musicbrainzngs.get_release_group_by_id", return_value=single_rg),
            mock.patch("musicbrainzngs.get_release_by_id", return_value=no_rels_release),
        ):
            res = get_album_recording_rels(RECTORY_RG_ID, "place")
        assert "No place relationships found" in res
        assert "get_entity_relationships" in res

    def test_no_releases(self):
        empty_rg = {"release-group": {"release-list": []}}
        with mock.patch("musicbrainzngs.get_release_group_by_id", return_value=empty_rg):
            res = get_album_recording_rels(RECTORY_RG_ID, "place")
        assert "No releases found" in res

    def test_invalid_rel_type(self):
        res = get_album_recording_rels(RECTORY_RG_ID, "invalid")
        assert "Invalid rel_type" in res


# ── get_release_group_details ────────────────────────────────────────────────


class TestGetReleaseGroupDetails:
    def test_full_output(self):
        with (
            mock.patch("musicbrainzngs.get_release_group_by_id", return_value=GET_RELEASE_GROUP_RESPONSE),
            mock.patch("musicbrainzngs.browse_releases", return_value=BROWSE_RELEASES_FOR_RG_RESPONSE),
        ):
            res = get_release_group_details(RECTORY_RG_ID)
        assert "Title: In the Rectory of the Bizarre Reverend" in res
        assert "Artist: Reverend Bizarre" in res
        assert "Type: Album" in res
        assert "doom metal (2)" in res
        assert "Rating: 4.25/5 (2 votes)" in res
        assert "Releases in this group (5)" in res
        # Label and format info from browse_releases
        assert "Sinister Figure (SFGCD10)" in res
        assert "CD" in res
        assert "FI" in res

    def test_releases_limit(self):
        release_list: list[dict[str, object]] = BROWSE_RELEASES_FOR_RG_RESPONSE["release-list"]  # type: ignore[assignment]
        limited_browse = {
            "release-list": release_list[:1],
            "release-count": 5,
        }
        with (
            mock.patch("musicbrainzngs.get_release_group_by_id", return_value=GET_RELEASE_GROUP_RESPONSE),
            mock.patch("musicbrainzngs.browse_releases", return_value=limited_browse),
        ):
            res = get_release_group_details(RECTORY_RG_ID, releases_limit=1)
        assert "... and 4 more" in res
        assert "browse_entities" in res


# ── get_work_details ─────────────────────────────────────────────────────────


class TestGetWorkDetails:
    def test_full_output(self):
        with mock.patch("musicbrainzngs.get_work_by_id", return_value=GET_WORK_RESPONSE):
            res = get_work_details(BURN_WORK_ID)
        assert "Title: Burn in Hell" in res
        assert "Type: Song" in res
        assert "Composer: Dee Snider" in res
        assert "Lyricist: Dee Snider" in res
        assert "heavy metal (1)" in res
        assert "Rating: 4.5/5 (1 votes)" in res

    def test_publishers(self):
        with mock.patch("musicbrainzngs.get_work_by_id", return_value=GET_WORK_RESPONSE):
            res = get_work_details(BURN_WORK_ID)
        assert "Publishing: Universal Tunes" in res

    def test_no_creators(self):
        empty_work = {"work": {"id": "w1", "title": "Test", "type": "Song"}}
        with mock.patch("musicbrainzngs.get_work_by_id", return_value=empty_work):
            res = get_work_details("w1")
        assert "No creators listed" in res


# ── get_area_details ─────────────────────────────────────────────────────────


class TestGetAreaDetails:
    def test_full_output(self):
        with mock.patch("musicbrainzngs.get_area_by_id", return_value=GET_AREA_RESPONSE):
            res = get_area_details(FINLAND_AREA_ID)
        assert "Name: Finland" in res
        assert "Type: Country" in res
        assert "Suomi" in res

    def test_alias_limit(self):
        with mock.patch("musicbrainzngs.get_area_by_id", return_value=GET_AREA_RESPONSE):
            res = get_area_details(FINLAND_AREA_ID, alias_limit=1)
        assert "Finland" in res
        assert "Suomi" not in res


# ── get_event_details ────────────────────────────────────────────────────────


class TestGetEventDetails:
    def test_full_output(self):
        with mock.patch("musicbrainzngs.get_event_by_id", return_value=GET_EVENT_RESPONSE):
            res = get_event_details("event-1")
        assert "Name: Reverend Bizarre Farewell Show" in res
        assert "Type: Concert" in res
        assert "Date: 2007-10-26 to 2007-10-26" in res
        assert "Time: 20:00" in res
        assert "RB Last Gig" in res
        assert "doom metal (1)" in res


# ── get_instrument_details ───────────────────────────────────────────────────


class TestGetInstrumentDetails:
    def test_full_output(self):
        with mock.patch("musicbrainzngs.get_instrument_by_id", return_value=GET_INSTRUMENT_RESPONSE):
            res = get_instrument_details("instrument-1")
        assert "Name: bass guitar" in res
        assert "Type: String instrument" in res
        assert "four-stringed" in res
        assert "bass" in res


# ── get_place_details ────────────────────────────────────────────────────────


class TestGetPlaceDetails:
    def test_full_output(self):
        with mock.patch("musicbrainzngs.get_place_by_id", return_value=GET_PLACE_RESPONSE):
            res = get_place_details("place-1")
        assert "Name: Nosturi" in res
        assert "Type: Venue" in res
        assert "Telakkakatu 8" in res
        assert "60.16172" in res
        assert "Nosturi Club" in res


# ── get_series_details ───────────────────────────────────────────────────────


class TestGetSeriesDetails:
    def test_full_output(self):
        with mock.patch("musicbrainzngs.get_series_by_id", return_value=GET_SERIES_RESPONSE):
            res = get_series_details("series-1")
        assert "Name: Days of the Ceremony" in res
        assert "Type: Tour" in res
        assert "DotC" in res


# ── get_label_details ────────────────────────────────────────────────────────


class TestGetLabelDetails:
    def test_full_output(self):
        with mock.patch("musicbrainzngs.get_label_by_id", return_value=GET_LABEL_RESPONSE):
            res = get_label_details(SINISTER_LABEL_ID)
        assert "Name: Sinister Figure" in res
        assert "Type: Original Production" in res
        assert "Country: FI" in res
        assert "Rating: 3.8/5 (5 votes)" in res
        assert "discogs" in res


# ── get_entity_relationships ─────────────────────────────────────────────────


class TestGetEntityRelationships:
    def test_artist_relationships(self):
        with mock.patch("musicbrainzngs.get_artist_by_id", return_value=GET_ARTIST_RELS_RESPONSE):
            res = get_entity_relationships("artist", RB_ARTIST_ID)
        assert "Member of band" in res
        assert "Albert Witchfinder" in res
        assert "bass guitar" in res
        assert "Peter Vicar" in res
        assert "bandcamp" in res

    def test_full_output(self):
        with mock.patch("musicbrainzngs.get_artist_by_id", return_value=GET_ARTIST_RELS_RESPONSE):
            res = get_entity_relationships("artist", RB_ARTIST_ID)
        # Target MBIDs are included
        assert "artist ID: 6b3ed1ba-ce18-422f-823e-bf39137f8d56" in res
        assert "artist ID: 9b3f663b-2cba-4e7c-be94-f33bc56cf0c4" in res
        # Date range shown when present
        assert "[1999–2007]" in res
        # No date range for Peter Vicar (no begin/end in mock data)
        peter_line = [line for line in res.splitlines() if "Peter Vicar" in line][0]
        assert "[" not in peter_line or "artist ID" in peter_line.split("[")[-1]
        # URL rels use target as fallback (no entity dict)
        assert "bandcamp" in res.lower()

    def test_custom_include_rels(self):
        with mock.patch("musicbrainzngs.get_artist_by_id", return_value=GET_ARTIST_RELS_RESPONSE) as m:
            get_entity_relationships("artist", RB_ARTIST_ID, include_rels=["label-rels", "place-rels"])
        assert m.call_args[1]["includes"] == ["label-rels", "place-rels"]

    def test_invalid_include_rels(self):
        res = get_entity_relationships("artist", RB_ARTIST_ID, include_rels=["bogus-rels"])
        assert "Invalid relationship types" in res

    def test_invalid_entity_type(self):
        res = get_entity_relationships("bogus", "some-id")
        assert "Invalid entity type" in res

    def test_no_relationships(self):
        empty = {"artist": {"id": RB_ARTIST_ID, "name": "Test"}}
        with mock.patch("musicbrainzngs.get_artist_by_id", return_value=empty):
            res = get_entity_relationships("artist", RB_ARTIST_ID)
        assert "No relationships found" in res


# ── get_cover_art_urls ───────────────────────────────────────────────────────


class TestGetCoverArtUrls:
    def test_with_images(self):
        with mock.patch("musicbrainzngs.get_image_list", return_value=COVER_ART_RESPONSE):
            res = get_cover_art_urls(RECTORY_RELEASE_ID)
        assert "2 images" in res
        assert "[Front]" in res
        assert "[Back]" in res
        assert "front-500.jpg" in res

    def test_no_images(self):
        with mock.patch("musicbrainzngs.get_image_list", return_value={"images": []}):
            res = get_cover_art_urls(RECTORY_RELEASE_ID)
        assert "No cover art" in res


# ── get_release_group_cover_art ──────────────────────────────────────────────


class TestGetReleaseGroupCoverArt:
    def test_success(self):
        with mock.patch("musicbrainzngs.get_release_group_image_list", return_value=RG_COVER_ART_RESPONSE):
            res = get_release_group_cover_art(RECTORY_RG_ID)
        assert "1 images" in res
        assert "[Front]" in res

    def test_404(self):
        err = musicbrainzngs.ResponseError(cause=type("C", (), {"code": 404})())
        with mock.patch("musicbrainzngs.get_release_group_image_list", side_effect=err):
            res = get_release_group_cover_art(RECTORY_RG_ID)
        assert "No cover art available" in res

    def test_other_error_propagates(self):
        err = musicbrainzngs.ResponseError(cause=type("C", (), {"code": 503, "reason": "Unavailable"})())
        with mock.patch("musicbrainzngs.get_release_group_image_list", side_effect=err):
            res = get_release_group_cover_art(RECTORY_RG_ID)
        assert "MusicBrainz API error" in res


# ── ID mismatch hints ────────────────────────────────────────────────────────


class TestIDMismatchHints:
    def _make_error(self):
        return musicbrainzngs.ResponseError(cause=type("C", (), {"code": 400, "reason": "Bad Request"})())

    def test_release_details_hint(self):
        with mock.patch("musicbrainzngs.get_release_by_id", side_effect=self._make_error()):
            res = get_release_details("wrong-id")
        assert "get_release_group_details" in res

    def test_release_group_details_hint(self):
        with mock.patch("musicbrainzngs.get_release_group_by_id", side_effect=self._make_error()):
            res = get_release_group_details("wrong-id")
        assert "get_release_details" in res

    def test_album_tracks_hint(self):
        with mock.patch("musicbrainzngs.get_release_group_by_id", side_effect=self._make_error()):
            res = get_album_tracks("wrong-id")
        assert "get_release_details" in res


# ── Industry Standard Translation Tools (ISRC/ISWC) ──────────────────────────


class TestIndustryTranslationTools:
    def test_lookup_recording_by_isrc(self):
        mock_res = {
            "isrc": {
                "recording-list": [
                    {"title": "Smells Like Teen Spirit", "artist-credit-phrase": "Nirvana", "id": "rec-123"}
                ]
            }
        }
        with mock.patch("musicbrainzngs.get_recordings_by_isrc", return_value=mock_res):
            from mcp_musicbrainz.server import lookup_recording_by_isrc

            res = lookup_recording_by_isrc("USDC3234234")
            assert "Smells Like Teen Spirit" in res
            assert "Nirvana" in res
            assert "rec-123" in res

    def test_lookup_recording_by_isrc_not_found(self):
        with mock.patch("musicbrainzngs.get_recordings_by_isrc", return_value={"isrc": {"recording-list": []}}):
            from mcp_musicbrainz.server import lookup_recording_by_isrc

            res = lookup_recording_by_isrc("BOGUS-ISRC")
            assert "No recording found" in res

    def test_lookup_work_by_iswc(self):
        mock_res = {"work-list": [{"title": "Yesterday", "id": "work-456"}]}
        with mock.patch("musicbrainzngs.get_works_by_iswc", return_value=mock_res):
            from mcp_musicbrainz.server import lookup_work_by_iswc

            res = lookup_work_by_iswc("T-123.456.789-C")
            assert "Yesterday" in res
            assert "work-456" in res

    def test_lookup_work_by_iswc_not_found(self):
        with mock.patch("musicbrainzngs.get_works_by_iswc", return_value={"work-list": []}):
            from mcp_musicbrainz.server import lookup_work_by_iswc

            res = lookup_work_by_iswc("BOGUS-ISWC")
            assert "No works found" in res
