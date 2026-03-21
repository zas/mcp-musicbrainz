"""Shared fixtures and mock data from real MusicBrainz API responses.

All data is based on Reverend Bizarre (Finnish doom metal band, 1995-2007)
and their album "In the Rectory of the Bizarre Reverend" (2002).
Responses have been trimmed to essential fields for readability.
"""

import unittest.mock as mock

import pytest

# -- IDs --
RB_ARTIST_ID = "97992045-1d3f-469d-91ce-27afd0bd216b"
RECTORY_RG_ID = "b44c32ad-bb4e-36b5-beef-431423a62232"
RECTORY_RELEASE_ID = "c3e0a211-0a98-4bb0-b9bb-29245a4cfc93"
BURN_RECORDING_ID = "c83dc49b-5567-4f5c-8645-ecf4158e76b9"
BURN_WORK_ID = "6ee7ac65-aa61-4f5d-98fa-46875ddfb713"
FINLAND_AREA_ID = "6a264f94-6ff1-30b1-9a81-41f7bfabd616"
SINISTER_LABEL_ID = "d7d0a16e-a051-49aa-b6f5-20aba76b1143"
RECTORY_BARCODE = "6420074201020"

# -- search_artists response --
SEARCH_ARTISTS_RESPONSE = {
    "artist-list": [
        {
            "id": RB_ARTIST_ID,
            "type": "Group",
            "name": "Reverend Bizarre",
            "sort-name": "Reverend Bizarre",
            "country": "FI",
            "disambiguation": "Finnish doom metal band",
            "life-span": {"begin": "1995", "end": "2007", "ended": "true"},
        },
        {
            "id": "2ddb0e05-e6b2-4c6b-b2d4-08a20c1a0d1d",
            "type": "Person",
            "name": "Bizarre",
            "sort-name": "Bizarre",
            "disambiguation": "US rapper",
        },
    ],
    "artist-count": 389,
}

# -- get_artist_by_id response (with includes) --
GET_ARTIST_RESPONSE = {
    "artist": {
        "id": RB_ARTIST_ID,
        "type": "Group",
        "name": "Reverend Bizarre",
        "sort-name": "Reverend Bizarre",
        "country": "FI",
        "disambiguation": "Finnish doom metal band",
        "life-span": {"begin": "1995", "end": "2007", "ended": "true"},
        "alias-list": [
            {"sort-name": "Reverand Bizarre", "type": "Search hint", "alias": "Reverand Bizarre"},
            {"sort-name": "Reverend Bizare", "type": "Search hint", "alias": "Reverend Bizare"},
            {"sort-name": "Reverend Bizzare", "type": "Search hint", "alias": "Reverend Bizzare"},
            {"sort-name": "Reverend Bizzarre", "type": "Search hint", "alias": "Reverend Bizzarre"},
        ],
        "alias-count": 4,
        "release-group-list": [
            {
                "id": RECTORY_RG_ID,
                "type": "Album",
                "title": "In the Rectory of the Bizarre Reverend",
                "first-release-date": "2002-03-28",
                "primary-type": "Album",
            },
            {
                "id": "01354609-9761-32fd-82ad-df4b10ac0ed9",
                "type": "Album",
                "title": "II: Crush the Insects",
                "first-release-date": "2005-06-15",
                "primary-type": "Album",
            },
            {
                "id": "da76aeb6-7eec-3676-ba4c-15311ad3488c",
                "type": "Album",
                "title": "III: So Long Suckers",
                "first-release-date": "2007-08-08",
                "primary-type": "Album",
            },
        ],
        "release-group-count": 28,
        "url-relation-list": [
            {"type": "bandcamp", "target": "https://reverendbizarre.bandcamp.com/", "direction": "forward"},
            {"type": "discogs", "target": "https://www.discogs.com/artist/306450", "direction": "forward"},
        ],
        "tag-list": [
            {"count": "4", "name": "doom metal"},
            {"count": "1", "name": "heavy metal"},
            {"count": "1", "name": "traditional doom metal"},
        ],
        "rating": {"votes-count": "3", "rating": "5"},
    }
}

# -- browse_release_groups response --
BROWSE_RELEASE_GROUPS_RESPONSE = {
    "release-group-list": [
        {
            "id": RECTORY_RG_ID,
            "type": "Album",
            "title": "In the Rectory of the Bizarre Reverend",
            "first-release-date": "2002-03-28",
            "primary-type": "Album",
        },
        {
            "id": "01354609-9761-32fd-82ad-df4b10ac0ed9",
            "type": "Album",
            "title": "II: Crush the Insects",
            "first-release-date": "2005-06-15",
            "primary-type": "Album",
        },
        {
            "id": "da76aeb6-7eec-3676-ba4c-15311ad3488c",
            "type": "Album",
            "title": "III: So Long Suckers",
            "first-release-date": "2007-08-08",
            "primary-type": "Album",
        },
    ],
    "release-group-count": 28,
}

# -- get_release_group_by_id response --
GET_RELEASE_GROUP_RESPONSE = {
    "release-group": {
        "id": RECTORY_RG_ID,
        "type": "Album",
        "title": "In the Rectory of the Bizarre Reverend",
        "first-release-date": "2002-03-28",
        "primary-type": "Album",
        "artist-credit-phrase": "Reverend Bizarre",
        "release-list": [
            {
                "id": RECTORY_RELEASE_ID,
                "title": "In the Rectory of the Bizarre Reverend",
                "status": "Official",
                "date": "2002-03-28",
                "country": "FI",
                "artist-credit-phrase": "Reverend Bizarre",
            },
            {
                "id": "036abc08-d4c4-4e32-ab61-5358d7a67f40",
                "title": "In the Rectory of the Bizarre Reverend",
                "status": "Official",
                "date": "2002",
                "country": "RU",
                "artist-credit-phrase": "Reverend Bizarre",
            },
        ],
        "release-count": 5,
        "tag-list": [{"count": "2", "name": "doom metal"}],
        "rating": {"votes-count": "2", "rating": "4.25"},
    }
}

# -- get_release_by_id response --
GET_RELEASE_RESPONSE = {
    "release": {
        "id": RECTORY_RELEASE_ID,
        "title": "In the Rectory of the Bizarre Reverend",
        "status": "Official",
        "date": "2002-03-28",
        "country": "FI",
        "barcode": RECTORY_BARCODE,
        "artist-credit-phrase": "Reverend Bizarre",
        "release-group": {
            "id": RECTORY_RG_ID,
            "type": "Album",
            "title": "In the Rectory of the Bizarre Reverend",
            "tag-list": [{"count": "2", "name": "doom metal"}],
        },
        "label-info-list": [
            {
                "catalog-number": "SFGCD10",
                "label": {"id": SINISTER_LABEL_ID, "name": "Sinister Figure"},
            }
        ],
        "medium-list": [
            {
                "position": "1",
                "format": "CD",
                "track-list": [
                    {
                        "id": "04eed1ec-1058-3b36-8e77-3affc1ded85f",
                        "position": "1",
                        "number": "1",
                        "length": "532413",
                        "recording": {"id": BURN_RECORDING_ID, "title": "Burn in Hell!", "length": "532413"},
                    },
                    {
                        "id": "1d929982-20d3-3085-b8c2-a67e8ec01c53",
                        "position": "2",
                        "number": "2",
                        "length": "790426",
                        "recording": {
                            "id": "e3a8767f-6fe6-4af4-9898-2f9f60fd1429",
                            "title": "In the Rectory",
                            "length": "790426",
                        },
                    },
                    {
                        "id": "8a5f29cd-eaed-38eb-8a32-96bad53e1bc8",
                        "position": "3",
                        "number": "3",
                        "length": "708813",
                        "recording": {
                            "id": "1f8366f3-f01a-4ae7-adce-88ea1636d739",
                            "title": "The Hour of Death",
                            "length": "708813",
                        },
                    },
                    {
                        "id": "fccb4abb-1c99-3f1e-8982-5b7f210322bd",
                        "position": "4",
                        "number": "4",
                        "length": "809386",
                        "recording": {
                            "id": "3c676146-bf23-44ea-83d1-90149f2c3fc9",
                            "title": "Sodoma Sunrise",
                            "length": "809386",
                        },
                    },
                    {
                        "id": "6bc1d28a-9668-3039-9ff0-ae78e3cf88eb",
                        "position": "5",
                        "number": "5",
                        "length": "337160",
                        "recording": {
                            "id": "c43b4a9a-c71e-44fc-bb2a-ce25cc6986cb",
                            "title": "Doomsower",
                            "length": "337160",
                        },
                    },
                    {
                        "id": "cb2418ab-8aea-306d-a2cc-ac85fa948e8f",
                        "position": "6",
                        "number": "6",
                        "length": "1269800",
                        "recording": {
                            "id": "9450a8df-a16b-4bc3-9ac2-e50e0fb2a722",
                            "title": "Cirith Ungol",
                            "length": "1269800",
                        },
                    },
                ],
                "track-count": 6,
            }
        ],
    }
}

# -- get_recording_by_id response --
GET_RECORDING_RESPONSE = {
    "recording": {
        "id": BURN_RECORDING_ID,
        "title": "Burn in Hell!",
        "length": "532413",
        "artist-credit-phrase": "Reverend Bizarre",
        "release-list": [
            {"id": RECTORY_RELEASE_ID, "title": "In the Rectory of the Bizarre Reverend", "date": "2002-03-28"},
            {
                "id": "036abc08-d4c4-4e32-ab61-5358d7a67f40",
                "title": "In the Rectory of the Bizarre Reverend",
                "date": "2002",
            },
            {
                "id": "5752d1f0-94fd-3ac3-92cd-f289293e1efe",
                "title": "In the Rectory of the Bizarre Reverend",
                "date": "2003-01-31",
            },
        ],
        "release-count": 8,
        "isrc-list": ["FISFS0404002"],
        "tag-list": [
            {"count": "2", "name": "doom metal"},
            {"count": "1", "name": "finnish metal"},
        ],
        "rating": {"votes-count": "2", "rating": "4.25"},
        "work-relation-list": [
            {
                "type": "performance",
                "work": {
                    "id": BURN_WORK_ID,
                    "title": "Burn in Hell",
                    "artist-relation-list": [
                        {
                            "type": "composer",
                            "artist": {"id": "80c4f609-e9e6-440d-aa8d-252224ef4d92", "name": "Dee Snider"},
                        },
                        {
                            "type": "lyricist",
                            "artist": {"id": "80c4f609-e9e6-440d-aa8d-252224ef4d92", "name": "Dee Snider"},
                        },
                    ],
                },
            },
        ],
    }
}

# -- get_work_by_id response (Twisted Sister's "Burn in Hell") --
GET_WORK_RESPONSE = {
    "work": {
        "id": BURN_WORK_ID,
        "type": "Song",
        "title": "Burn in Hell",
        "language": "eng",
        "artist-relation-list": [
            {
                "type": "composer",
                "direction": "backward",
                "artist": {"id": "80c4f609-e9e6-440d-aa8d-252224ef4d92", "name": "Dee Snider"},
            },
            {
                "type": "lyricist",
                "direction": "backward",
                "artist": {"id": "80c4f609-e9e6-440d-aa8d-252224ef4d92", "name": "Dee Snider"},
            },
        ],
        "label-relation-list": [
            {
                "type": "publishing",
                "direction": "backward",
                "label": {"id": "fe54e161-95ba-49da-83ee-1ab0f0f163dd", "name": "Universal Tunes"},
            },
        ],
        "tag-list": [
            {"count": "1", "name": "heavy metal"},
            {"count": "1", "name": "rock"},
        ],
        "rating": {"votes-count": "1", "rating": "4.5"},
    }
}

# -- get_area_by_id response --
GET_AREA_RESPONSE = {
    "area": {
        "id": FINLAND_AREA_ID,
        "type": "Country",
        "name": "Finland",
        "sort-name": "Finland",
        "life-span": {"ended": "false"},
        "alias-list": [
            {"locale": "en", "sort-name": "Finland", "alias": "Finland"},
            {"locale": "fi", "sort-name": "Suomi", "alias": "Suomi"},
            {"locale": "fr", "sort-name": "Finlande", "alias": "Finlande"},
        ],
    }
}

# -- get_label_by_id response --
GET_LABEL_RESPONSE = {
    "label": {
        "id": SINISTER_LABEL_ID,
        "type": "Original Production",
        "name": "Sinister Figure",
        "sort-name": "Sinister Figure",
        "country": "FI",
        "life-span": {},
        "url-relation-list": [
            {"type": "discogs", "target": "https://www.discogs.com/label/60339", "direction": "forward"},
        ],
        "rating": {"votes-count": "5", "rating": "3.8"},
    }
}

# -- browse_releases response --
BROWSE_RELEASES_RESPONSE = {
    "release-list": [
        {
            "id": "77e0f608-e340-4c02-88a1-c11b33efc85d",
            "title": "Practice Sessions",
            "date": "1996",
        },
        {
            "id": "d18a00af-6779-4005-8be8-5f11dededb3a",
            "title": "Slice of Doom",
            "date": "1999-09-09",
        },
    ],
    "release-count": 48,
}

# -- search_releases response --
SEARCH_RELEASES_RESPONSE = {
    "release-list": [
        {
            "id": RECTORY_RELEASE_ID,
            "title": "In the Rectory of the Bizarre Reverend",
            "date": "2002-03-28",
            "artist-credit-phrase": "Reverend Bizarre",
        },
    ],
    "release-count": 1,
}

# -- search_recordings response --
SEARCH_RECORDINGS_RESPONSE = {
    "recording-list": [
        {
            "id": BURN_RECORDING_ID,
            "title": "Burn in Hell!",
            "length": "532413",
            "artist-credit-phrase": "Reverend Bizarre",
        },
    ],
    "recording-count": 1,
}

# -- search_release_groups response --
SEARCH_RELEASE_GROUPS_RESPONSE = {
    "release-group-list": [
        {
            "id": RECTORY_RG_ID,
            "type": "Album",
            "title": "In the Rectory of the Bizarre Reverend",
            "first-release-date": "2002-03-28",
            "artist-credit-phrase": "Reverend Bizarre",
        },
    ],
    "release-group-count": 1,
}

# -- get_artist_by_id for relationships --
GET_ARTIST_RELS_RESPONSE = {
    "artist": {
        "id": RB_ARTIST_ID,
        "name": "Reverend Bizarre",
        "artist-relation-list": [
            {
                "type": "member of band",
                "direction": "backward",
                "attribute-list": ["bass guitar", "lead vocals", "original"],
                "artist": {"id": "6b3ed1ba-ce18-422f-823e-bf39137f8d56", "name": "Albert Witchfinder"},
            },
            {
                "type": "member of band",
                "direction": "backward",
                "attribute-list": ["guitar", "original"],
                "artist": {"id": "9b3f663b-2cba-4e7c-be94-f33bc56cf0c4", "name": "Peter Vicar"},
            },
        ],
        "url-relation-list": [
            {"type": "bandcamp", "target": "https://reverendbizarre.bandcamp.com/", "direction": "forward"},
        ],
    }
}

# -- cover art responses --
COVER_ART_RESPONSE = {
    "images": [
        {
            "types": ["Front"],
            "image": "http://coverartarchive.org/release/c3e0a211/front.jpg",
            "thumbnails": {"500": "http://coverartarchive.org/release/c3e0a211/front-500.jpg"},
        },
        {
            "types": ["Back"],
            "image": "http://coverartarchive.org/release/c3e0a211/back.jpg",
            "thumbnails": {"large": "http://coverartarchive.org/release/c3e0a211/back-large.jpg"},
        },
    ]
}

RG_COVER_ART_RESPONSE = {
    "images": [
        {
            "types": ["Front"],
            "image": "http://coverartarchive.org/release-group/b44c32ad/front.jpg",
            "thumbnails": {"500": "http://coverartarchive.org/release-group/b44c32ad/front-500.jpg"},
        },
    ]
}

# -- barcode lookup response --
BARCODE_LOOKUP_RESPONSE = {
    "release-list": [
        {
            "id": RECTORY_RELEASE_ID,
            "title": "In the Rectory of the Bizarre Reverend",
            "date": "2002-03-28",
            "artist-credit-phrase": "Reverend Bizarre",
        },
    ],
}

# -- event/instrument/place/series responses --
GET_EVENT_RESPONSE = {
    "event": {
        "id": "event-1",
        "name": "Reverend Bizarre Farewell Show",
        "type": "Concert",
        "life-span": {"begin": "2007-10-26", "end": "2007-10-26"},
        "time": "20:00",
        "alias-list": [{"alias": "RB Last Gig", "sort-name": "RB Last Gig"}],
        "tag-list": [{"count": "1", "name": "doom metal"}],
    }
}

GET_INSTRUMENT_RESPONSE = {
    "instrument": {
        "id": "instrument-1",
        "name": "bass guitar",
        "type": "String instrument",
        "description": "A four-stringed instrument.",
        "alias-list": [{"alias": "bass", "sort-name": "bass"}],
        "tag-list": [{"count": "1", "name": "guitar family"}],
    }
}

GET_PLACE_RESPONSE = {
    "place": {
        "id": "place-1",
        "name": "Nosturi",
        "type": "Venue",
        "address": "Telakkakatu 8, 00150 Helsinki",
        "coordinates": {"latitude": "60.16172", "longitude": "24.92572"},
        "alias-list": [{"alias": "Nosturi Club", "sort-name": "Nosturi Club"}],
        "tag-list": [{"count": "1", "name": "live venue"}],
    }
}

GET_SERIES_RESPONSE = {
    "series": {
        "id": "series-1",
        "name": "Days of the Ceremony",
        "type": "Tour",
        "alias-list": [{"alias": "DotC", "sort-name": "DotC"}],
        "tag-list": [{"count": "1", "name": "doom metal"}],
    }
}


class MockCache(dict):
    """In-memory cache replacement for tests."""

    def set(self, key, value, expire=None):
        self[key] = value


@pytest.fixture(autouse=True)
def _mock_cache():
    """Replace disk cache with in-memory dict for all tests."""
    with mock.patch("mcp_musicbrainz.server.cache", MockCache()):
        yield
