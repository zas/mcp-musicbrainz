"""Tests for all MCP tools using mocked musicbrainzngs responses.

Mock data is sourced from real MusicBrainz API responses for Reverend Bizarre.
See conftest.py for fixtures and response constants.
"""

import unittest.mock as mock

import musicbrainzngs

from mcp_musicbrainz.server import (
    browse_entities,
    get_album_tracks,
    get_area_details,
    get_artist_details,
    get_artist_discography,
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
    lookup_by_barcode,
    search_artists,
    search_entities,
    search_entities_fuzzy,
    search_release_groups,
    search_releases,
)
from tests.conftest import (
    BARCODE_LOOKUP_RESPONSE,
    BROWSE_RELEASE_GROUPS_RESPONSE,
    BROWSE_RELEASES_RESPONSE,
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
    GET_SERIES_RESPONSE,
    GET_WORK_RESPONSE,
    RB_ARTIST_ID,
    RECTORY_BARCODE,
    RECTORY_RELEASE_ID,
    RECTORY_RG_ID,
    RG_COVER_ART_RESPONSE,
    SEARCH_ARTISTS_RESPONSE,
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
            res = search_entities("artist", "Reverend Bizarre", limit=2)
        assert "Found 2 results" in res
        assert "Reverend Bizarre (Finnish doom metal band)" in res
        assert f"artist ID: {RB_ARTIST_ID}" in res

    def test_invalid_entity_type(self):
        res = search_entities("bogus", "test")
        assert "Invalid entity type" in res

    def test_empty_results(self):
        with mock.patch.dict(
            "mcp_musicbrainz.server.SEARCH_FUNCS", {"artist": mock.Mock(return_value={"artist-list": []})}
        ):
            res = search_entities("artist", "nonexistent")
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


# ── search_releases ──────────────────────────────────────────────────────────


class TestSearchReleases:
    def test_basic_search(self):
        with mock.patch("musicbrainzngs.search_releases", return_value=SEARCH_RELEASES_RESPONSE):
            res = search_releases(title="In the Rectory")
        assert "Found 1 releases" in res
        assert "Reverend Bizarre" in res
        assert f"release ID: {RECTORY_RELEASE_ID}" in res

    def test_no_params(self):
        res = search_releases()
        assert "Please provide at least one search parameter" in res


# ── search_recordings ─────────────────────────────────────────


class TestSearchRecordings:
    def test_basic_search(self):
        mock_res = {
            "recording-list": [{"title": "Stairway to Heaven", "artist-credit-phrase": "Led Zeppelin", "id": "rec-1"}]
        }
        with mock.patch("musicbrainzngs.search_recordings", return_value=mock_res):
            from mcp_musicbrainz.server import search_recordings

            res = search_recordings(query="Stairway to Heaven")
        assert "Stairway to Heaven" in res
        assert "Led Zeppelin" in res
        assert "rec-1" in res

    def test_with_offset(self):
        with mock.patch("musicbrainzngs.search_recordings", return_value={"recording-list": []}) as m:
            from mcp_musicbrainz.server import search_recordings

            search_recordings(query="Test", offset=5)
        assert m.call_args[1]["offset"] == 5


# ── search_works ─────────────────────────────────────────


class TestSearchWorks:
    def test_basic_search(self):
        mock_res = {"work-list": [{"title": "Symphony No. 5", "type": "Symphony", "id": "work-1"}]}
        with mock.patch("musicbrainzngs.search_works", return_value=mock_res):
            from mcp_musicbrainz.server import search_works

            res = search_works(query="Symphony No. 5")
        assert "Symphony No. 5" in res
        assert "Symphony" in res
        assert "work-1" in res

    def test_with_offset(self):
        with mock.patch("musicbrainzngs.search_works", return_value={"work-list": []}) as m:
            from mcp_musicbrainz.server import search_works

            search_works(query="Test", offset=10)
        assert m.call_args[1]["offset"] == 10


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


# ── get_artist_details ───────────────────────────────────────────────────────


class TestGetArtistDetails:
    def test_full_output(self):
        with mock.patch("musicbrainzngs.get_artist_by_id", return_value=GET_ARTIST_RESPONSE):
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

    def test_alias_limit(self):
        with mock.patch("musicbrainzngs.get_artist_by_id", return_value=GET_ARTIST_RESPONSE):
            res = get_artist_details(RB_ARTIST_ID, alias_limit=2)
        # Only 2 of 4 aliases should appear
        assert "Reverand Bizarre" in res
        assert "Reverend Bizare" in res
        assert "Reverend Bizzarre" not in res

    def test_discography_limit(self):
        with mock.patch("musicbrainzngs.get_artist_by_id", return_value=GET_ARTIST_RESPONSE):
            res = get_artist_details(RB_ARTIST_ID, discography_limit=1)
        assert "In the Rectory" in res
        assert "II: Crush the Insects" not in res


# ── get_artist_discography ───────────────────────────────────────────────────


class TestGetArtistDiscography:
    def test_paged_output(self):
        with mock.patch("musicbrainzngs.browse_release_groups", return_value=BROWSE_RELEASE_GROUPS_RESPONSE):
            res = get_artist_discography(RB_ARTIST_ID, limit=3)
        assert "Showing 3 of 28" in res
        assert "In the Rectory" in res
        assert "II: Crush the Insects" in res
        assert "[Album]" in res


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
        assert "1. Burn in Hell! (8:52)" in res
        assert "6. Cirith Ungol (21:09)" in res

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
        assert "Appears on (3 releases)" in res

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


# ── get_release_group_details ────────────────────────────────────────────────


class TestGetReleaseGroupDetails:
    def test_full_output(self):
        with mock.patch("musicbrainzngs.get_release_group_by_id", return_value=GET_RELEASE_GROUP_RESPONSE):
            res = get_release_group_details(RECTORY_RG_ID)
        assert "Title: In the Rectory of the Bizarre Reverend" in res
        assert "Artist: Reverend Bizarre" in res
        assert "Type: Album" in res
        assert "doom metal (2)" in res
        assert "Rating: 4.25/5 (2 votes)" in res
        assert "Releases in this group (2)" in res

    def test_releases_limit(self):
        with mock.patch("musicbrainzngs.get_release_group_by_id", return_value=GET_RELEASE_GROUP_RESPONSE):
            res = get_release_group_details(RECTORY_RG_ID, releases_limit=1)
        assert "... and 1 more" in res
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


# ── lookup_by_barcode ────────────────────────────────────────────────────────


class TestLookupByBarcode:
    def test_found(self):
        with mock.patch("musicbrainzngs.search_releases", return_value=BARCODE_LOOKUP_RESPONSE):
            res = lookup_by_barcode(RECTORY_BARCODE)
        assert "In the Rectory" in res
        assert "Reverend Bizarre" in res

    def test_not_found(self):
        with mock.patch("musicbrainzngs.search_releases", return_value={"release-list": []}):
            res = lookup_by_barcode("0000000000000")
        assert "No releases found" in res


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
