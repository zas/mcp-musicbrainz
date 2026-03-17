from __future__ import annotations

from typing import Any

import diskcache
import musicbrainzngs
from fastmcp import FastMCP

from mcp_musicbrainz import __version__

mcp = FastMCP("MusicBrainz")
cache = diskcache.Cache(".musicbrainz_cache")

musicbrainzngs.set_useragent(
    "mcp-musicbrainz",
    __version__,
    "https://github.com/zas/mcp-musicbrainz",
)

SEARCH_FUNCS: dict[str, Any] = {
    "artist": musicbrainzngs.search_artists,
    "release": musicbrainzngs.search_releases,
    "release-group": musicbrainzngs.search_release_groups,
    "recording": musicbrainzngs.search_recordings,
    "label": musicbrainzngs.search_labels,
    "work": musicbrainzngs.search_works,
    "area": musicbrainzngs.search_areas,
    "event": musicbrainzngs.search_events,
    "instrument": musicbrainzngs.search_instruments,
    "place": musicbrainzngs.search_places,
    "series": musicbrainzngs.search_series,
}

BROWSE_FUNCS: dict[str, Any] = {
    "releases": musicbrainzngs.browse_releases,
    "recordings": musicbrainzngs.browse_recordings,
    "release-groups": musicbrainzngs.browse_release_groups,
    "artists": musicbrainzngs.browse_artists,
    "labels": musicbrainzngs.browse_labels,
    "works": musicbrainzngs.browse_works,
    "events": musicbrainzngs.browse_events,
    "places": musicbrainzngs.browse_places,
}

VALID_LINKED_TYPES = {
    "artist",
    "label",
    "recording",
    "release",
    "release_group",
    "work",
    "area",
    "collection",
}


def _fmt_duration(ms: str | int | None) -> str:
    if not ms:
        return "??:??"
    total_seconds = int(ms) // 1000
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"


def _cached(key: str, func: Any, expire: int = 86400) -> Any:
    if key in cache:
        return cache[key]
    data = func()
    cache.set(key, data, expire=expire)
    return data


def _mb_error_message(err: musicbrainzngs.MusicBrainzError) -> str:
    """Extract a readable message from a MusicBrainz error."""
    if isinstance(err, musicbrainzngs.ResponseError):
        cause = err.cause
        if cause:
            return f"MusicBrainz API error: {cause.code} {cause.reason}"
        return str(err)
    return f"MusicBrainz error: {err}"


def _format_tracks(medium_list: list[dict[str, Any]]) -> list[str]:
    tracks = []
    for medium in medium_list:
        fmt = medium.get("format", "")
        prefix = f"[{fmt}] " if fmt and len(medium_list) > 1 else ""
        for t in medium.get("track-list", []):
            rec = t.get("recording", {})
            dur = _fmt_duration(rec.get("length"))
            tracks.append(f"  {prefix}{t['number']}. {rec.get('title', '?')} ({dur})")
    return tracks


@mcp.tool()
def search_entities(entity_type: str, query: str, limit: int = 5) -> str:
    """
    Search for any MusicBrainz entity (artist, release, recording, label, work,
    release-group, area, event, instrument, place, series).
    Supports Lucene syntax. Example queries:
    - 'artist:Nirvana AND country:US'
    - 'release:Nevermind'
    - 'recording:"Smells Like Teen Spirit"'
    """
    if entity_type not in SEARCH_FUNCS:
        return (
            f"Invalid entity type '{entity_type}'. "
            f"Choose from: {', '.join(SEARCH_FUNCS)}"
        )
    cache_key = f"search:{entity_type}:{query}:{limit}"

    def fetch() -> str:
        result = SEARCH_FUNCS[entity_type](query=query, limit=limit)
        list_key = f"{entity_type.replace('-', '_')}-list"
        items = result.get(list_key, [])
        lines = [f"Found {len(items)} results for {entity_type}:"]
        for i in items:
            name = i.get("name") or i.get("title")
            disambig = i.get("disambiguation", "")
            extra = f" ({disambig})" if disambig else ""
            lines.append(f"- {name}{extra} | ID: {i['id']}")
        return "\n".join(lines)

    try:
        return _cached(cache_key, fetch)
    except musicbrainzngs.MusicBrainzError as e:
        return _mb_error_message(e)


@mcp.tool()
def browse_entities(
    entity_type: str,
    linked_type: str,
    linked_id: str,
    limit: int = 25,
    offset: int = 0,
) -> str:
    """
    Browse MusicBrainz entities linked to another entity, with paging.
    Useful for getting complete discographies, all releases on a label, etc.

    Args:
        entity_type: What to list (releases, recordings, release-groups,
                     artists, labels, works, events, places)
        linked_type: The entity you're browsing by (artist, label,
                     recording, release, release_group, work, area, collection)
        linked_id: MBID of the linked entity
        limit: Results per page (max 100)
        offset: Paging offset
    """
    if entity_type not in BROWSE_FUNCS:
        return (
            f"Invalid entity type '{entity_type}'. "
            f"Choose from: {', '.join(BROWSE_FUNCS)}"
        )
    # Normalize hyphenated linked_type to underscore for musicbrainzngs kwargs
    normalized = linked_type.replace("-", "_")
    if normalized not in VALID_LINKED_TYPES:
        return (
            f"Invalid linked type '{linked_type}'. "
            f"Choose from: {', '.join(sorted(VALID_LINKED_TYPES))}"
        )
    cache_key = f"browse:{entity_type}:{normalized}:{linked_id}:{limit}:{offset}"

    def fetch() -> str:
        result = BROWSE_FUNCS[entity_type](
            **{normalized: linked_id, "limit": min(limit, 100), "offset": offset}
        )
        singular = entity_type.rstrip("s")
        list_key = f"{singular}-list"
        count_key = f"{singular}-count"
        items = result.get(list_key, [])
        count = result.get(count_key, len(items))
        lines = [f"Showing {len(items)} of {count} {entity_type} (offset {offset}):"]
        for i in items:
            name = i.get("title") or i.get("name", "?")
            date = i.get("first-release-date") or i.get("date", "")
            rtype = i.get("type") or i.get("primary-type", "")
            extra = " | ".join(filter(None, [date, rtype]))
            extra_str = f" ({extra})" if extra else ""
            lines.append(f"- {name}{extra_str} | ID: {i['id']}")
        return "\n".join(lines)

    try:
        return _cached(cache_key, fetch)
    except musicbrainzngs.MusicBrainzError as e:
        return _mb_error_message(e)


@mcp.tool()
def get_artist_details(artist_id: str) -> str:
    """
    Get comprehensive info about an artist including aliases, tags, genres,
    and their discography (Release Groups) with MBIDs.
    """
    cache_key = f"artist_v3:{artist_id}"

    def fetch() -> str:
        res = musicbrainzngs.get_artist_by_id(
            artist_id,
            includes=[
                "aliases",
                "tags",
                "ratings",
                "release-groups",
                "url-rels",
            ],
        )
        a = res["artist"]
        tags = [t["name"] for t in a.get("tag-list", [])]
        genres = ", ".join(tags) if tags else ""
        aliases = ", ".join(al["alias"] for al in a.get("alias-list", [])[:10])
        urls = "\n".join(
            f"  - {r['type']}: {r['target']}" for r in a.get("url-relation-list", [])
        )

        rg_list = sorted(
            a.get("release-group-list", []),
            key=lambda rg: rg.get("first-release-date", "9999"),
        )
        albums = []
        for rg in rg_list:
            rtype = rg.get("type", "Unknown")
            date = rg.get("first-release-date", "????")
            albums.append(f"  - {rg['title']} ({date}) [{rtype}] | ID: {rg['id']}")

        lifespan = a.get("life-span", {})
        begin = lifespan.get("begin", "?")
        end = lifespan.get("end", "present")
        rating = a.get("rating", {})
        rating_str = (
            f"{rating['rating']}/5 ({rating.get('votes-count', 0)} votes)"
            if rating.get("rating")
            else "N/A"
        )

        parts = [
            f"Name: {a['name']}",
            f"Type: {a.get('type', 'N/A')}",
            f"Country: {a.get('country', 'N/A')}",
            f"Life-span: {begin} to {end}",
            f"Genres: {genres or 'None listed'}",
            f"Rating: {rating_str}",
            f"Aliases: {aliases or 'None'}",
            f"MBID: {a['id']}",
        ]
        if urls:
            parts.append(f"URLs:\n{urls}")
        parts.append(
            f"\nDISCOGRAPHY ({len(rg_list)} release groups, "
            f"showing first 25):\n" + "\n".join(albums[:25])
        )
        return "\n".join(parts)

    try:
        return _cached(cache_key, fetch)
    except musicbrainzngs.MusicBrainzError as e:
        return _mb_error_message(e)


@mcp.tool()
def get_release_details(release_id: str) -> str:
    """
    Get tracklist with durations, barcode, and label for a specific release.
    """
    cache_key = f"release_v4:{release_id}"

    def fetch() -> str:
        res = musicbrainzngs.get_release_by_id(
            release_id,
            includes=[
                "recordings",
                "labels",
                "artist-credits",
                "media",
                "release-groups",
            ],
        )
        r = res["release"]
        tracks = _format_tracks(r.get("medium-list", []))

        labels = ", ".join(
            f"{li.get('label', {}).get('name', '?')}"
            f" ({li.get('catalog-number', 'N/A')})"
            for li in r.get("label-info-list", [])
        )
        barcode = r.get("barcode", "N/A")
        status = r.get("status", "N/A")
        country = r.get("country", "N/A")
        rg = r.get("release-group", {})
        rg_type = rg.get("type", "N/A")

        parts = [
            f"Title: {r['title']}",
            f"Artist: {r.get('artist-credit-phrase', 'N/A')}",
            f"Date: {r.get('date', 'Unknown')}",
            f"Country: {country}",
            f"Status: {status}",
            f"Type: {rg_type}",
            f"Barcode: {barcode}",
            f"Label: {labels or 'N/A'}",
            f"MBID: {release_id}",
            "\nTracklist:\n" + "\n".join(tracks),
        ]
        return "\n".join(parts)

    try:
        return _cached(cache_key, fetch)
    except musicbrainzngs.MusicBrainzError as e:
        return _mb_error_message(e)


@mcp.tool()
def get_recording_details(recording_id: str) -> str:
    """
    Find which albums a specific recording (song) appears on,
    including artist credits, ISRCs, and genres.
    """
    cache_key = f"recording_v2:{recording_id}"

    def fetch() -> str:
        res = musicbrainzngs.get_recording_by_id(
            recording_id,
            includes=[
                "releases",
                "artist-credits",
                "isrcs",
                "tags",
                "ratings",
            ],
        )
        rec = res["recording"]
        releases = [
            f"  - {rel['title']} ({rel.get('date', '?')}) | ID: {rel['id']}"
            for rel in rec.get("release-list", [])
        ]
        isrcs = ", ".join(rec.get("isrc-list", [])) or "None"
        tags = [t["name"] for t in rec.get("tag-list", [])]
        genres = ", ".join(tags) if tags else ""
        artist = rec.get("artist-credit-phrase", "N/A")
        dur = _fmt_duration(rec.get("length"))

        parts = [
            f"Title: {rec['title']}",
            f"Artist: {artist}",
            f"Duration: {dur}",
            f"ISRCs: {isrcs}",
            f"Genres: {genres or 'None listed'}",
            f"MBID: {recording_id}",
            f"\nAppears on ({len(releases)} releases):",
            *releases[:25],
        ]
        return "\n".join(parts)

    try:
        return _cached(cache_key, fetch)
    except musicbrainzngs.MusicBrainzError as e:
        return _mb_error_message(e)


@mcp.tool()
def get_album_tracks(release_group_id: str) -> str:
    """Fetches the tracklist with durations for a specific album ID. (Cached)"""
    cache_key = f"tracks_v4:{release_group_id}"

    def fetch() -> str:
        rg_result = musicbrainzngs.get_release_group_by_id(
            release_group_id, includes=["releases"]
        )
        releases = rg_result["release-group"].get("release-list", [])
        if not releases:
            return "No releases found for this release group."

        release_id = releases[0]["id"]
        release_details = musicbrainzngs.get_release_by_id(
            release_id, includes=["recordings"]
        )
        tracks = _format_tracks(release_details["release"].get("medium-list", []))
        return "\n".join(tracks) if tracks else "No tracks found."

    try:
        return _cached(cache_key, fetch)
    except musicbrainzngs.MusicBrainzError as e:
        return _mb_error_message(e)


@mcp.tool()
def get_label_details(label_id: str) -> str:
    """
    Get details about a record label including type, area, and associated releases.
    """
    cache_key = f"label_v1:{label_id}"

    def fetch() -> str:
        res = musicbrainzngs.get_label_by_id(
            label_id,
            includes=["aliases", "tags", "ratings", "url-rels"],
        )
        lb = res["label"]
        tags = [t["name"] for t in lb.get("tag-list", [])]
        genres = ", ".join(tags) if tags else ""
        aliases = ", ".join(al["alias"] for al in lb.get("alias-list", [])[:10])
        urls = "\n".join(
            f"  - {r['type']}: {r['target']}" for r in lb.get("url-relation-list", [])
        )
        lifespan = lb.get("life-span", {})
        begin = lifespan.get("begin", "?")
        end = lifespan.get("end", "present")

        parts = [
            f"Name: {lb['name']}",
            f"Type: {lb.get('type', 'N/A')}",
            f"Country: {lb.get('country', 'N/A')}",
            f"Founded: {begin} to {end}",
            f"Label code: {lb.get('label-code', 'N/A')}",
            f"Genres: {genres or 'None listed'}",
            f"Aliases: {aliases or 'None'}",
            f"MBID: {lb['id']}",
        ]
        if urls:
            parts.append(f"URLs:\n{urls}")
        return "\n".join(parts)

    try:
        return _cached(cache_key, fetch)
    except musicbrainzngs.MusicBrainzError as e:
        return _mb_error_message(e)


@mcp.tool()
def lookup_by_barcode(barcode: str) -> str:
    """Finds a release by its UPC/EAN barcode."""
    cache_key = f"barcode:{barcode}"

    def fetch() -> str:
        result = musicbrainzngs.search_releases(barcode=barcode, limit=5)
        releases = result.get("release-list", [])
        if not releases:
            return f"No releases found for barcode {barcode}."
        lines = [f"Releases for barcode {barcode}:"]
        for r in releases:
            artist = r.get("artist-credit-phrase", "Unknown")
            date = r.get("date", "?")
            lines.append(f"- {r['title']} by {artist} ({date}) | ID: {r['id']}")
        return "\n".join(lines)

    try:
        return _cached(cache_key, fetch)
    except musicbrainzngs.MusicBrainzError as e:
        return _mb_error_message(e)


@mcp.tool()
def get_cover_art_urls(release_id: str) -> str:
    """
    Get cover art image URLs for a release from the Cover Art Archive.
    Returns URLs for front/back covers and thumbnails.
    """
    cache_key = f"coverart_v1:{release_id}"

    def fetch() -> str:
        images = musicbrainzngs.get_image_list(release_id)
        img_list = images.get("images", [])
        if not img_list:
            return "No cover art images available."
        lines = [f"Cover art for release {release_id} ({len(img_list)} images):"]
        for img in img_list:
            types = ", ".join(img.get("types", ["Unknown"]))
            lines.append(f"- [{types}] {img.get('image', 'N/A')}")
            thumbs = img.get("thumbnails", {})
            if thumbs:
                thumb_url = thumbs.get("500") or thumbs.get("large", "")
                if thumb_url:
                    lines.append(f"  Thumbnail: {thumb_url}")
        return "\n".join(lines)

    try:
        return _cached(cache_key, fetch)
    except musicbrainzngs.MusicBrainzError as e:
        return _mb_error_message(e)
