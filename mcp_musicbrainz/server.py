from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from typing import Any, NewType

import diskcache
import musicbrainzngs
from fastmcp import FastMCP

from mcp_musicbrainz import __version__

#: MusicBrainz Identifier — a UUID that uniquely identifies an entity (artist, release, recording, etc.)
MBID = NewType("MBID", str)

logger = logging.getLogger(__name__)

mcp = FastMCP("MusicBrainz")
cache = diskcache.Cache(".musicbrainz_cache")

# Bump this when changing how API responses are fetched or formatted,
# so stale cached results are automatically bypassed.
CACHE_VERSION = 6

musicbrainzngs.set_useragent(
    "mcp-musicbrainz",
    __version__,
    "https://github.com/zas/mcp-musicbrainz",
)


TOOL_ANNOTATIONS = {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": True}

ID_HINT: dict[str, str] = {
    "get_release_details": "If you have a release-group ID, use get_release_group_details or get_album_tracks instead.",
    "get_release_group_details": "If you have a release ID, use get_release_details instead.",
    "get_album_tracks": "If you have a release ID, use get_release_details instead.",
}


def cached_tool(expire: int = 86400) -> Callable:
    """Decorator to cache tool results and handle MusicBrainz errors."""

    def decorator(func: Callable[..., str]) -> Callable[..., str]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> str:
            # Create a cache key from function name and arguments
            arg_str = ":".join(map(str, args))
            kwarg_str = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = f"v{CACHE_VERSION}:{func.__name__}:{arg_str}:{kwarg_str}"  # type: ignore[union-attr]

            if cache_key in cache:
                return cache[cache_key]

            try:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, expire=expire)
                return result
            except musicbrainzngs.MusicBrainzError as e:
                msg = _mb_error_message(e)
                hint = ID_HINT.get(func.__name__, "")  # type: ignore[union-attr]
                return f"{msg} {hint}".strip() if hint else msg
            except Exception:
                logger.exception("Unexpected error in %s", func.__name__)  # type: ignore[union-attr]
                return "An unexpected error occurred. Check server logs for details."

        return wrapper

    return decorator


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
    "place",
    "track_artist",
}

# Valid (entity_type, linked_type) browse combinations per musicbrainzngs function signatures.
# Note: "areas" browse is not supported by musicbrainzngs.
VALID_BROWSE_COMBINATIONS: dict[str, set[str]] = {
    "artists": {"recording", "release", "release_group", "work"},
    "events": {"area", "artist", "place"},
    "labels": {"release"},
    "places": {"area"},
    "recordings": {"artist", "release"},
    "releases": {"artist", "track_artist", "label", "recording", "release_group"},
    "release-groups": {"artist", "release"},
    "works": {"artist"},
}


def _fmt_duration(ms: str | int | None) -> str:
    if ms is None or ms == "":
        return "??:??"
    total_seconds = int(ms) // 1000
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"


def _fmt_rating(entity: dict[str, Any]) -> str:
    rating = entity.get("rating", {})
    return f"{rating['rating']}/5 ({rating.get('votes-count', 0)} votes)" if rating.get("rating") else "N/A"


def _fmt_tags(entity: dict[str, Any]) -> str:
    tags = sorted(entity.get("tag-list", []), key=lambda t: int(t.get("count", 0)), reverse=True)
    return ", ".join(f"{t['name']} ({t['count']})" for t in tags) if tags else ""


def _mb_error_message(err: musicbrainzngs.MusicBrainzError) -> str:
    """Extract a readable message from a MusicBrainz error."""
    if isinstance(err, musicbrainzngs.ResponseError):
        cause = err.cause
        if cause:
            return f"MusicBrainz API error: {cause.code} {cause.reason}"
        return str(err)
    return f"MusicBrainz error: {err}"


def _format_performers(artist_relation_list: list[dict[str, Any]]) -> list[str]:
    performers = []
    for rel in artist_relation_list:
        rtype = rel.get("type", "Unknown")
        attrs = rel.get("attribute-list", [])
        name = rel.get("artist", {}).get("name", "Unknown")
        attrs_str = f" ({', '.join(attrs)})" if attrs else ""
        performers.append(f"  - {rtype.capitalize()}{attrs_str}: {name}")
    return performers


def _format_tracks(medium_list: list[dict[str, Any]], include_performers: bool = False) -> list[str]:
    tracks = []
    for medium in medium_list:
        fmt = medium.get("format", "")
        prefix = f"[{fmt}] " if fmt and len(medium_list) > 1 else ""
        for t in medium.get("track-list", []):
            rec = t.get("recording", {})
            dur = _fmt_duration(rec.get("length"))
            rec_id = rec.get("id", "")
            rec_suffix = f" | recording ID: {rec_id}" if rec_id else ""
            tracks.append(f"  {prefix}{t['number']}. {rec.get('title', '?')} ({dur}){rec_suffix}")
            if include_performers:
                tracks.extend(_format_performers(rec.get("artist-relation-list", [])))
    return tracks


def _search_result_detail(entity_type: str, item: dict[str, Any]) -> str:
    """Extract key details from a search result to reduce follow-up queries."""
    parts: list[str] = []
    if entity_type == "artist":
        if t := item.get("type"):
            parts.append(t)
        if c := item.get("country"):
            parts.append(c)
        ls = item.get("life-span", {})
        if begin := ls.get("begin"):
            end = ls.get("end", "present")
            parts.append(f"{begin}–{end}")
    elif entity_type == "release":
        if a := item.get("artist-credit-phrase"):
            parts.append(f"by {a}")
        if d := item.get("date"):
            parts.append(d)
        if c := item.get("country"):
            parts.append(c)
        for li in item.get("label-info-list", []):
            if lbl := li.get("label", {}).get("name"):
                parts.append(lbl)
    elif entity_type == "recording":
        if a := item.get("artist-credit-phrase"):
            parts.append(f"by {a}")
        if length := item.get("length"):
            parts.append(_fmt_duration(length))
    elif entity_type == "release-group":
        if a := item.get("artist-credit-phrase"):
            parts.append(f"by {a}")
        if d := item.get("first-release-date"):
            parts.append(d)
        if t := item.get("type") or item.get("primary-type"):
            parts.append(t)
    elif entity_type == "label":
        if t := item.get("type"):
            parts.append(t)
        if c := item.get("country"):
            parts.append(c)
    return ", ".join(parts)


def _search_entities(entity_type: str, query: str, limit: int = 5, offset: int = 0) -> str:
    """Internal helper: search any MusicBrainz entity type by Lucene query."""
    if entity_type not in SEARCH_FUNCS:
        return f"Invalid entity type '{entity_type}'. Choose from: {', '.join(SEARCH_FUNCS)}"
    result = SEARCH_FUNCS[entity_type](query=query, limit=limit, offset=offset)
    list_key = f"{entity_type.replace('-', '_')}-list"
    items = result.get(list_key, [])
    lines = [f"Found {len(items)} results for {entity_type}:"]
    for i in items:
        name = i.get("name") or i.get("title")
        disambig = i.get("disambiguation", "")
        extra = f" ({disambig})" if disambig else ""
        detail = _search_result_detail(entity_type, i)
        detail_str = f" [{detail}]" if detail else ""
        lines.append(f"- {name}{extra}{detail_str} | {entity_type} ID: {i['id']}")
    return "\n".join(lines)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def browse_entities(
    entity_type: str,
    linked_type: str,
    linked_id: MBID,
    limit: int = 25,
    offset: int = 0,
    includes: list[str] | None = None,
) -> str:
    """
    Browse MusicBrainz entities linked to another entity, with paging.
    Useful for getting complete discographies, all releases on a label, etc.

    Common combinations:
    - release-groups by artist: full discography
    - releases by release_group: all editions of an album
    - releases by label: label's catalog
    - recordings by artist: all recorded tracks

    Args:
        entity_type: What to list (releases, recordings, release-groups,
                     artists, labels, works, events, places)
        linked_type: The entity you're browsing by (artist, label,
                     recording, release, release_group, work, area, collection)
        linked_id: MBID of the linked entity
        limit: Results per page (max 100)
        offset: Paging offset
        includes: Extra data to fetch per entity. Useful examples:
            - 'labels' on releases: get label + catalog number per release
            - 'artist-credits' on releases/recordings: get artist names
            - 'tags' on most entity types: get genre tags
            - 'isrcs' on recordings: get ISRCs
    """
    if entity_type not in BROWSE_FUNCS:
        return f"Invalid entity type '{entity_type}'. Choose from: {', '.join(BROWSE_FUNCS)}"
    # Normalize hyphenated linked_type to underscore for musicbrainzngs kwargs
    normalized = linked_type.replace("-", "_")
    valid_for_entity = VALID_BROWSE_COMBINATIONS.get(entity_type, set())
    if normalized not in valid_for_entity:
        return (
            f"Invalid linked type '{linked_type}' for {entity_type}. "
            f"Valid linked types: {', '.join(sorted(valid_for_entity))}"
        )

    kwargs: dict[str, Any] = {normalized: linked_id, "limit": min(limit, 100), "offset": offset}
    if includes:
        kwargs["includes"] = includes
    result = BROWSE_FUNCS[entity_type](**kwargs)
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
        parts = [p for p in [date, rtype] if p]
        # Append label info when available (from includes=['labels'])
        for li in i.get("label-info-list", []):
            lbl = li.get("label", {}).get("name")
            cat = li.get("catalog-number")
            if lbl:
                parts.append(f"{lbl} ({cat})" if cat else lbl)
        extra_str = f" ({' | '.join(parts)})" if parts else ""
        lines.append(f"- {name}{extra_str} | {singular} ID: {i['id']}")
    return "\n".join(lines)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def search_artists(
    name: str,
    country: str | None = None,
    artist_type: str | None = None,
    gender: str | None = None,
    limit: int = 5,
    offset: int = 0,
    strict: bool = False,
) -> str:
    """
    Search for artists with specific filters.
    Args:
        name: Artist name
        country: ISO 3166-1 alpha-2 country code
        artist_type: 'person', 'group', 'orchestra', 'choir', 'character', 'other'
        gender: 'male', 'female', 'other', 'not applicable'
        limit: Max results (default 5)
        offset: Number of results to skip for pagination (default 0)
        strict: If True, all filters must match (default False for fuzzy ranking)
    """
    kwargs: dict[str, Any] = {"artist": name, "limit": limit, "offset": offset, "strict": strict}
    if country:
        kwargs["country"] = country
    if artist_type:
        kwargs["type"] = artist_type
    if gender:
        kwargs["gender"] = gender

    result = musicbrainzngs.search_artists(**kwargs)
    items = result.get("artist-list", [])
    lines = [f"Found {len(items)} artists:"]
    for i in items:
        aname = i.get("name")
        disambig = i.get("disambiguation", "")
        extra = f" ({disambig})" if disambig else ""
        lines.append(f"- {aname}{extra} | artist ID: {i['id']}")
    return "\n".join(lines)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def search_releases(
    title: str | None = None,
    artist: str | None = None,
    label: str | None = None,
    barcode: str | None = None,
    catno: str | None = None,
    format: str | None = None,
    limit: int = 5,
    offset: int = 0,
    strict: bool = False,
) -> str:
    """
    Search for releases with specific filters.
    Also use this to find a release by its barcode.
    Args:
        title: Release title
        artist: Artist name
        label: Label name
        barcode: UPC/EAN barcode
        catno: Catalog number (insensitive to case, spaces, and separators)
        format: Medium format (e.g. '12" Vinyl', 'CD', 'Digital Media')
        limit: Max results (default 5)
        offset: Number of results to skip for pagination (default 0)
        strict: If True, all filters must match (default False for fuzzy ranking)
    """
    kwargs: dict[str, Any] = {"limit": limit, "offset": offset, "strict": strict}
    if title:
        kwargs["release"] = title
    if artist:
        kwargs["artist"] = artist
    if label:
        kwargs["label"] = label
    if barcode:
        kwargs["barcode"] = "".join(c for c in barcode if c.isdigit())
    if catno:
        kwargs["catno"] = catno
    if format:
        kwargs["format"] = format

    if not any((title, artist, label, barcode, catno, format)):
        return "Please provide at least one search parameter."

    result = musicbrainzngs.search_releases(**kwargs)
    items = result.get("release-list", [])
    lines = [f"Found {len(items)} releases:"]
    for i in items:
        rtitle = i.get("title")
        rartist = i.get("artist-credit-phrase", "Unknown")
        date = i.get("date", "?")
        country = i.get("country", "")
        labels = ", ".join(
            li.get("label", {}).get("name", "")
            for li in i.get("label-info-list", [])
            if li.get("label", {}).get("name")
        )
        catnos = ", ".join(
            li.get("catalog-number", "") for li in i.get("label-info-list", []) if li.get("catalog-number")
        )
        formats = ", ".join(m.get("format", "") for m in i.get("medium-list", []) if m.get("format"))
        rg = i.get("release-group", {})
        rg_info = f" | release-group ID: {rg['id']}" if rg.get("id") else ""
        extras = " | ".join(filter(None, [date, country, formats, labels, catnos]))
        lines.append(f"- {rtitle} by {rartist} ({extras}) | release ID: {i['id']}{rg_info}")
    return "\n".join(lines)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def search_recordings(
    title: str | None = None,
    artist: str | None = None,
    release: str | None = None,
    isrc: str | None = None,
    limit: int = 5,
    offset: int = 0,
    strict: bool = False,
) -> str:
    """
    Search for recordings with specific filters.
    Args:
        title: Recording title
        artist: Artist name
        release: Release title the recording appears on
        isrc: International Standard Recording Code
        limit: Max results (default 5)
        offset: Number of results to skip for pagination (default 0)
        strict: If True, all filters must match (default False for fuzzy ranking)
    """
    kwargs: dict[str, Any] = {"limit": limit, "offset": offset, "strict": strict}
    if title:
        kwargs["recording"] = title
    if artist:
        kwargs["artist"] = artist
    if release:
        kwargs["release"] = release
    if isrc:
        kwargs["isrc"] = isrc

    if not any((title, artist, release, isrc)):
        return "Please provide at least one search parameter."

    result = musicbrainzngs.search_recordings(**kwargs)
    items = result.get("recording-list", [])
    lines = [f"Found {len(items)} recordings:"]
    for i in items:
        rtitle = i.get("title")
        rartist = i.get("artist-credit-phrase", "Unknown")
        dur = _fmt_duration(i.get("length"))
        lines.append(f"- {rtitle} by {rartist} ({dur}) | recording ID: {i['id']}")
    return "\n".join(lines)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def search_release_groups(
    title: str | None = None,
    artist: str | None = None,
    release_group_type: str | None = None,
    limit: int = 5,
    offset: int = 0,
    strict: bool = False,
) -> str:
    """
    Search for release groups (albums/EPs/singles) with specific filters.
    Args:
        title: Release group title
        artist: Artist name
        release_group_type: 'album', 'ep', 'single', 'broadcast', 'other'
        limit: Max results (default 5)
        offset: Number of results to skip for pagination (default 0)
        strict: If True, all filters must match (default False for fuzzy ranking)
    """
    kwargs: dict[str, Any] = {"limit": limit, "offset": offset, "strict": strict}
    if title:
        kwargs["releasegroup"] = title
    if artist:
        kwargs["artist"] = artist
    if release_group_type:
        kwargs["type"] = release_group_type

    if not any((title, artist, release_group_type)):
        return "Please provide at least one search parameter."

    result = musicbrainzngs.search_release_groups(**kwargs)
    items = result.get("release-group-list", [])
    lines = [f"Found {len(items)} release groups:"]
    for i in items:
        rgtitle = i.get("title")
        rgartist = i.get("artist-credit-phrase", "Unknown")
        rgtype = i.get("type", "?")
        date = i.get("first-release-date", "?")
        lines.append(f"- {rgtitle} by {rgartist} ({date}) [{rgtype}] | release-group ID: {i['id']}")
    return "\n".join(lines)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def search_labels(
    name: str, label_type: str | None = None, country: str | None = None, limit: int = 5, offset: int = 0
) -> str:
    """
    Search for record labels.
    Args:
        name: Label name
        label_type: e.g. 'Original Production', 'Distributor', 'Holding', 'Reissue Production'
        country: ISO 3166-1 alpha-2 country code
        limit: Max results (default 5)
        offset: Number of results to skip for pagination (default 0)
    """
    parts = [f"label:{name}"]
    if label_type:
        parts.append(f'type:"{label_type}"')
    if country:
        parts.append(f"country:{country}")
    return _search_entities("label", " AND ".join(parts), limit=limit, offset=offset)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def search_works(
    name: str, artist: str | None = None, work_type: str | None = None, limit: int = 5, offset: int = 0
) -> str:
    """
    Search for musical works (compositions).
    Args:
        name: Work name
        artist: Composer or lyricist name
        work_type: e.g. 'Song', 'Opera', 'Symphony', 'Concerto'
        limit: Max results (default 5)
        offset: Number of results to skip for pagination (default 0)
    """
    parts = [f"work:{name}"]
    if artist:
        parts.append(f"artist:{artist}")
    if work_type:
        parts.append(f"type:{work_type}")
    return _search_entities("work", " AND ".join(parts), limit=limit, offset=offset)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def search_areas(name: str, area_type: str | None = None, limit: int = 5, offset: int = 0) -> str:
    """
    Search for geographic areas (countries, cities, etc.).
    Args:
        name: Area name
        area_type: e.g. 'Country', 'City', 'Subdivision', 'Municipality'
        limit: Max results (default 5)
        offset: Number of results to skip for pagination (default 0)
    """
    parts = [f"area:{name}"]
    if area_type:
        parts.append(f"type:{area_type}")
    return _search_entities("area", " AND ".join(parts), limit=limit, offset=offset)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def search_events(
    name: str, artist: str | None = None, event_type: str | None = None, limit: int = 5, offset: int = 0
) -> str:
    """
    Search for music events (concerts, festivals, etc.).
    Args:
        name: Event name
        artist: Artist related to the event
        event_type: e.g. 'Concert', 'Festival', 'Convention/Expo'
        limit: Max results (default 5)
        offset: Number of results to skip for pagination (default 0)
    """
    parts = [f"event:{name}"]
    if artist:
        parts.append(f"artist:{artist}")
    if event_type:
        parts.append(f"type:{event_type}")
    return _search_entities("event", " AND ".join(parts), limit=limit, offset=offset)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def search_instruments(name: str, instrument_type: str | None = None, limit: int = 5, offset: int = 0) -> str:
    """
    Search for musical instruments.
    Args:
        name: Instrument name
        instrument_type: e.g. 'Wind instrument', 'String instrument', 'Percussion instrument', 'Electronic instrument'
        limit: Max results (default 5)
        offset: Number of results to skip for pagination (default 0)
    """
    parts = [f"instrument:{name}"]
    if instrument_type:
        parts.append(f"type:{instrument_type}")
    return _search_entities("instrument", " AND ".join(parts), limit=limit, offset=offset)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def search_places(
    name: str, place_type: str | None = None, area: str | None = None, limit: int = 5, offset: int = 0
) -> str:
    """
    Search for places (venues, studios, etc.).
    Args:
        name: Place name
        place_type: e.g. 'Studio', 'Venue', 'Religious building'
        area: Area name the place is in
        limit: Max results (default 5)
        offset: Number of results to skip for pagination (default 0)
    """
    parts = [f"place:{name}"]
    if place_type:
        parts.append(f"type:{place_type}")
    if area:
        parts.append(f"area:{area}")
    return _search_entities("place", " AND ".join(parts), limit=limit, offset=offset)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def search_series(name: str, series_type: str | None = None, limit: int = 5, offset: int = 0) -> str:
    """
    Search for series (release series, tours, etc.).
    Args:
        name: Series name
        series_type: e.g. 'Release group series', 'Tour', 'Festival'
        limit: Max results (default 5)
        offset: Number of results to skip for pagination (default 0)
    """
    parts = [f"series:{name}"]
    if series_type:
        parts.append(f"type:{series_type}")
    return _search_entities("series", " AND ".join(parts), limit=limit, offset=offset)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def get_artist_details(
    artist_id: MBID, alias_limit: int = 10, discography_limit: int = 10, discography_offset: int = 0
) -> str:
    """
    Get comprehensive info about an artist including aliases, tags,
    and their discography (Release Groups) with MBIDs.
    Args:
        artist_id: The MBID
        alias_limit: Max number of aliases to show (default 10)
        discography_limit: Max number of release groups to show (default 10)
        discography_offset: Paging offset for the discography (default 0)
    """
    res = musicbrainzngs.get_artist_by_id(
        artist_id,
        includes=[
            "aliases",
            "tags",
            "ratings",
            "url-rels",
            "annotation",
        ],
    )
    a = res["artist"]
    aliases, tags = _extract_aliases_and_tags(a, alias_limit)
    urls = "\n".join(f"  - {r['type']}: {r['target']}" for r in a.get("url-relation-list", []))

    rg_res = musicbrainzngs.browse_release_groups(
        artist=artist_id,
        limit=min(discography_limit, 100),
        offset=discography_offset,
    )
    rg_list = rg_res.get("release-group-list", [])
    rg_count = rg_res.get("release-group-count", len(rg_list))
    albums = []
    for rg in rg_list:
        rtype = rg.get("type", "Unknown")
        date = rg.get("first-release-date", "????")
        albums.append(f"  - {rg['title']} ({date}) [{rtype}] | release-group ID: {rg['id']}")

    lifespan = a.get("life-span", {})
    begin = lifespan.get("begin", "?")
    end = lifespan.get("end", "present")
    rating_str = _fmt_rating(a)

    parts = [
        f"Name: {a['name']}",
        f"Type: {a.get('type', 'N/A')}",
        f"Country: {a.get('country', 'N/A')}",
        f"Life-span: {begin} to {end}",
        f"Tags: {tags or 'None listed'}",
        f"Rating: {rating_str}",
        f"Aliases: {aliases or 'None'}",
        f"MBID: {a['id']}",
    ]
    _append_extras(parts, a)
    if urls:
        parts.append(f"URLs:\n{urls}")

    showing = f"{discography_offset + 1}–{discography_offset + len(rg_list)}" if rg_list else "0"
    hint = (
        " Increase discography_limit or use discography_offset to page."
        if rg_count > discography_offset + len(rg_list)
        else ""
    )
    parts.append(f"\nDISCOGRAPHY (Showing {showing} of {rg_count} release groups.{hint})\n" + "\n".join(albums))
    return "\n".join(parts)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def get_release_details(release_id: MBID) -> str:
    """Get tracklist with durations, barcode, and label for a specific release.
    Takes a release_id (a specific edition), NOT a release_group_id.
    To get tracks for an album concept, use get_album_tracks with a release_group_id."""
    res = musicbrainzngs.get_release_by_id(
        release_id,
        includes=[
            "recordings",
            "labels",
            "artist-credits",
            "media",
            "release-groups",
            "annotation",
        ],
    )
    r = res["release"]
    tracks = _format_tracks(r.get("medium-list", []))

    labels = ", ".join(
        f"{li.get('label', {}).get('name', '?')} ({li.get('catalog-number', 'N/A')})"
        for li in r.get("label-info-list", [])
    )
    barcode = r.get("barcode", "N/A")
    status = r.get("status", "N/A")
    country = r.get("country", "N/A")
    rg = r.get("release-group", {})
    rg_type = rg.get("type", "N/A")
    rg_tags = _fmt_tags(rg)

    parts = [
        f"Title: {r['title']}",
        f"Artist: {r.get('artist-credit-phrase', 'N/A')}",
        f"Date: {r.get('date', 'Unknown')}",
        f"Country: {country}",
        f"Status: {status}",
        f"Type: {rg_type}",
        f"Barcode: {barcode}",
        f"Label: {labels or 'N/A'}",
        f"Tags: {rg_tags or 'None listed'}",
        f"Release Group: {rg.get('title', 'N/A')} | release-group ID: {rg.get('id', 'N/A')}",
        f"MBID: {release_id}",
    ]
    _append_extras(parts, r)
    parts.append("\nTracklist:\n" + "\n".join(tracks))
    return "\n".join(parts)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def get_recording_details(recording_id: MBID, releases_limit: int = 25) -> str:
    """
    Get recording details: artist, duration, ISRCs, performer credits
    (instruments, vocals), tags, and which releases (albums/singles) it appears on.
    Use get_album_tracks to see performers for all tracks on an album at once.
    Args:
        recording_id: The MBID
        releases_limit: Max number of releases to show (default 25)
    """
    res = musicbrainzngs.get_recording_by_id(
        recording_id,
        includes=[
            "releases",
            "artist-credits",
            "isrcs",
            "tags",
            "ratings",
            "work-level-rels",
            "artist-rels",
            "annotation",
        ],
    )
    rec = res["recording"]
    releases = [
        f"  - {rel['title']} ({rel.get('date', '?')}) | release ID: {rel['id']}" for rel in rec.get("release-list", [])
    ]
    isrcs = ", ".join(rec.get("isrc-list", [])) or "None"
    tags = _fmt_tags(rec)
    artist = rec.get("artist-credit-phrase", "N/A")
    dur = _fmt_duration(rec.get("length"))

    rating_str = _fmt_rating(rec)

    # Extract performer credits from artist relationships
    performers = _format_performers(rec.get("artist-relation-list", []))

    # Extract linked works and their artist relationships (composers, lyricists)
    works = []
    for rel in rec.get("work-relation-list", []):
        w = rel.get("work", {})
        w_title = w.get("title", "?")
        w_id = w.get("id", "")
        creators = []
        for ar in w.get("artist-relation-list", []):
            creators.append(f"{ar['type'].capitalize()}: {ar['artist']['name']}")
        creators_str = f" — {', '.join(creators)}" if creators else ""
        works.append(f"  - {w_title}{creators_str} | work ID: {w_id}")

    parts = [
        f"Title: {rec['title']}",
        f"Artist: {artist}",
        f"Duration: {dur}",
        f"ISRCs: {isrcs}",
        f"Tags: {tags or 'None listed'}",
        f"Rating: {rating_str}",
        f"MBID: {recording_id}",
    ]
    _append_extras(parts, rec)
    if performers:
        parts.append(f"\nPerformers ({len(performers)}):")
        parts.extend(performers)
    if works:
        parts.append(f"\nWorks ({len(works)}):")
        parts.extend(works)
    parts.append(f"\nAppears on ({len(releases)} releases):")
    parts.extend(releases[:releases_limit])
    if len(releases) > releases_limit:
        parts.append(
            f"  ... and {len(releases) - releases_limit} more."
            f" Use browse_entities(entity_type='releases', linked_type='recording',"
            f" linked_id='{recording_id}') for the full list."
        )
    return "\n".join(parts)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def get_album_tracks(release_group_id: MBID) -> str:
    """Fetches the tracklist with durations and performer credits for a release group
    (album/EP/single). Each track lists the musicians and their instruments/roles.
    Best tool for "who plays what on this album?" questions.
    Takes a release_group_id (NOT a release_id). For a specific release's tracklist,
    use get_release_details instead."""
    rg_result = musicbrainzngs.get_release_group_by_id(release_group_id, includes=["releases"])
    releases = rg_result["release-group"].get("release-list", [])
    if not releases:
        return "No releases found for this release group."

    release_id = releases[0]["id"]
    release_details = musicbrainzngs.get_release_by_id(
        release_id, includes=["recordings", "artist-rels", "recording-level-rels"]
    )
    r = release_details["release"]
    tracks = _format_tracks(r.get("medium-list", []), include_performers=True)
    if not tracks:
        return "No tracks found."
    header = f"Tracklist from release: {r.get('title', '?')} ({r.get('date', '?')}) | release ID: {release_id}"
    if len(releases) > 1:
        header += f"\n({len(releases)} releases available; use get_release_group_details to see all editions)"
    result = header + "\n" + "\n".join(tracks)
    # Check if any recording had performer credits
    has_performers = any(
        rec.get("artist-relation-list")
        for medium in r.get("medium-list", [])
        for t in medium.get("track-list", [])
        for rec in [t.get("recording", {})]
    )
    if not has_performers:
        result += (
            "\n\n(No per-track performer credits found in MusicBrainz for this release."
            " Try get_recording_details on individual tracks, or"
            f" get_entity_relationships(entity_type='release', entity_id='{release_id}',"
            " include_rels=['artist-rels']) for release-level credits.)"
        )
    return result


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def get_release_group_details(release_group_id: MBID, releases_limit: int = 25) -> str:
    """Get details about a release group (the album/EP/single concept).
    A release group contains one or more releases (specific editions),
    each shown with its label, catalog number, country, and format.
    Use get_release_details for a specific edition's tracklist and barcode.
    Args:
        release_group_id: The MBID
        releases_limit: Max number of releases to show (default 25)
    """
    res = musicbrainzngs.get_release_group_by_id(
        release_group_id,
        includes=["artists", "tags", "ratings", "url-rels", "annotation"],
    )
    rg = res["release-group"]
    tags = _fmt_tags(rg)
    artist = rg.get("artist-credit-phrase", "Unknown")
    rtype = rg.get("type", "Unknown")
    date = rg.get("first-release-date", "Unknown")

    # Fetch releases with label and media info for richer output
    browse_res = musicbrainzngs.browse_releases(
        release_group=release_group_id, includes=["labels", "media"], limit=min(releases_limit, 100)
    )
    release_list = browse_res.get("release-list", [])
    release_count = browse_res.get("release-count", len(release_list))

    releases = []
    for r in release_list:
        label_parts = []
        for li in r.get("label-info-list", []):
            lbl = li.get("label", {}).get("name")
            cat = li.get("catalog-number")
            if lbl:
                label_parts.append(f"{lbl} ({cat})" if cat else lbl)
        formats = [m.get("format", "") for m in r.get("medium-list", []) if m.get("format")]
        info = [p for p in [r.get("date", ""), r.get("country", ""), "+".join(formats)] if p]
        if label_parts:
            info.append(", ".join(label_parts))
        extra = f" ({' | '.join(info)})" if info else ""
        releases.append(f"  - {r['title']}{extra} | release ID: {r['id']}")

    rating_str = _fmt_rating(rg)

    parts = [
        f"Title: {rg['title']}",
        f"Artist: {artist}",
        f"Type: {rtype}",
        f"First Release Date: {date}",
        f"Tags: {tags or 'None listed'}",
        f"Rating: {rating_str}",
        f"MBID: {release_group_id}",
    ]
    _append_extras(parts, rg)
    parts.append(f"\nReleases in this group ({release_count}):")
    parts.extend(releases)
    if release_count > releases_limit:
        parts.append(
            f"  ... and {release_count - len(releases)} more."
            f" Use browse_entities(entity_type='releases', linked_type='release_group',"
            f" linked_id='{release_group_id}') for the full list."
        )
    return "\n".join(parts)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def get_work_details(work_id: MBID) -> str:
    """Get details about a musical work (composers, lyricists, etc.)."""
    res = musicbrainzngs.get_work_by_id(
        work_id,
        includes=["artist-rels", "label-rels", "work-rels", "tags", "ratings", "annotation"],
    )
    w = res["work"]
    tags = _fmt_tags(w)

    creators = []
    for rel in w.get("artist-relation-list", []):
        rtype = rel["type"]
        artist = rel["artist"]["name"]
        creators.append(f"  - {rtype.capitalize()}: {artist}")

    publishers = []
    for rel in w.get("label-relation-list", []):
        rtype = rel["type"]
        label = rel["label"]["name"]
        publishers.append(f"  - {rtype.capitalize()}: {label}")

    related_works = []
    for rel in w.get("work-relation-list", []):
        rtype = rel["type"]
        direction = rel.get("direction", "")
        attrs = rel.get("attribute-list", [])
        target = rel["work"]
        lang = target.get("language", "")
        lang_str = f" [{lang}]" if lang else ""
        attrs_str = f" ({', '.join(attrs)})" if attrs else ""
        related_works.append(
            f"  - {rtype.capitalize()}{attrs_str} ({direction}): {target['title']}{lang_str} | work ID: {target['id']}"
        )

    rating_str = _fmt_rating(w)

    parts = [
        f"Title: {w['title']}",
        f"Type: {w.get('type', 'Unknown')}",
        f"Tags: {tags or 'None listed'}",
        f"Rating: {rating_str}",
        f"MBID: {work_id}",
    ]
    _append_extras(parts, w)
    parts.append("\nCreators:")
    parts.extend(creators or ["  - No creators listed"])
    if publishers:
        parts.append("\nPublishers:")
        parts.extend(publishers)
    if related_works:
        parts.append("\nRelated works:")
        parts.extend(related_works)
    return "\n".join(parts)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def get_area_details(area_id: MBID, alias_limit: int = 10) -> str:
    """Get details about a geographic area (country, city).
    Args:
        area_id: The MBID
        alias_limit: Max number of aliases to show (default 10)
    """
    res = musicbrainzngs.get_area_by_id(
        area_id,
        includes=["aliases", "url-rels", "annotation"],
    )
    a = res["area"]
    aliases = ", ".join(al["alias"] for al in a.get("alias-list", [])[:alias_limit])
    lifespan = a.get("life-span", {})
    begin = lifespan.get("begin", "?")
    end = lifespan.get("end", "present")

    parts = [
        f"Name: {a['name']}",
        f"Type: {a.get('type', 'N/A')}",
        f"Life-span: {begin} to {end}",
        f"Aliases: {aliases or 'None'}",
        f"MBID: {area_id}",
    ]
    _append_extras(parts, a)
    return "\n".join(parts)


def _fmt_disambiguation(entity: dict[str, Any]) -> str:
    """Return disambiguation string or empty string."""
    return entity.get("disambiguation", "")


def _fmt_annotation(entity: dict[str, Any]) -> str:
    """Return annotation text or empty string."""
    return entity.get("annotation", {}).get("text", "")


def _append_extras(parts: list[str], entity: dict[str, Any]) -> None:
    """Append disambiguation and annotation to output parts if present."""
    disambiguation = _fmt_disambiguation(entity)
    if disambiguation:
        parts.append(f"Disambiguation: {disambiguation}")
    annotation = _fmt_annotation(entity)
    if annotation:
        parts.append(f"\nAnnotation:\n{annotation}")


def _extract_aliases_and_tags(entity_dict: dict[str, Any], alias_limit: int = 10) -> tuple[str, str]:
    """Helper to extract formatted aliases and tags from an entity dictionary."""
    aliases = ", ".join(al["alias"] for al in entity_dict.get("alias-list", [])[:alias_limit])
    tags = _fmt_tags(entity_dict)
    return aliases, tags


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def get_event_details(event_id: MBID, alias_limit: int = 10) -> str:
    """Get details about a music event (concert, festival, etc.).
    Args:
        event_id: The MBID
        alias_limit: Max number of aliases to show (default 10)
    """
    res = musicbrainzngs.get_event_by_id(
        event_id,
        includes=["aliases", "tags", "url-rels", "annotation"],
    )
    ev = res["event"]
    aliases, tags = _extract_aliases_and_tags(ev, alias_limit)
    lifespan = ev.get("life-span", {})
    begin = lifespan.get("begin", "?")
    end = lifespan.get("end", "?")

    parts = [
        f"Name: {ev['name']}",
        f"Type: {ev.get('type', 'N/A')}",
        f"Date: {begin} to {end}",
        f"Time: {ev.get('time', 'N/A')}",
        f"Aliases: {aliases or 'None'}",
        f"Tags: {tags or 'None listed'}",
        f"MBID: {event_id}",
    ]
    _append_extras(parts, ev)
    return "\n".join(parts)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def get_instrument_details(instrument_id: MBID, alias_limit: int = 10) -> str:
    """Get details about a musical instrument.
    Args:
        instrument_id: The MBID
        alias_limit: Max number of aliases to show (default 10)
    """
    res = musicbrainzngs.get_instrument_by_id(
        instrument_id,
        includes=["aliases", "tags", "url-rels", "annotation"],
    )
    inst = res["instrument"]
    aliases, tags = _extract_aliases_and_tags(inst, alias_limit)

    parts = [
        f"Name: {inst['name']}",
        f"Type: {inst.get('type', 'N/A')}",
        f"Description: {inst.get('description', 'N/A')}",
        f"Aliases: {aliases or 'None'}",
        f"Tags: {tags or 'None listed'}",
        f"MBID: {instrument_id}",
    ]
    _append_extras(parts, inst)
    return "\n".join(parts)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def get_place_details(place_id: MBID, alias_limit: int = 10) -> str:
    """Get details about a place (venue, studio, etc.).
    Args:
        place_id: The MBID
        alias_limit: Max number of aliases to show (default 10)
    """
    res = musicbrainzngs.get_place_by_id(
        place_id,
        includes=["aliases", "tags", "url-rels", "annotation"],
    )
    pl = res["place"]
    aliases, tags = _extract_aliases_and_tags(pl, alias_limit)
    coords = pl.get("coordinates", {})
    lat = coords.get("latitude", "N/A")
    lon = coords.get("longitude", "N/A")
    address = pl.get("address", "N/A")

    parts = [
        f"Name: {pl['name']}",
        f"Type: {pl.get('type', 'N/A')}",
        f"Address: {address}",
        f"Coordinates: {lat}, {lon}",
        f"Aliases: {aliases or 'None'}",
        f"Tags: {tags or 'None listed'}",
        f"MBID: {place_id}",
    ]
    _append_extras(parts, pl)
    return "\n".join(parts)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def get_series_details(series_id: MBID, alias_limit: int = 10) -> str:
    """Get details about a series (release series, tour, etc.).
    Args:
        series_id: The MBID
        alias_limit: Max number of aliases to show (default 10)
    """
    res = musicbrainzngs.get_series_by_id(
        series_id,
        includes=["aliases", "tags", "url-rels", "annotation"],
    )
    sr = res["series"]
    aliases, tags = _extract_aliases_and_tags(sr, alias_limit)
    parts = [
        f"Name: {sr['name']}",
        f"Type: {sr.get('type', 'N/A')}",
        f"Aliases: {aliases or 'None'}",
        f"Tags: {tags or 'None listed'}",
        f"MBID: {series_id}",
    ]
    _append_extras(parts, sr)
    return "\n".join(parts)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def get_label_details(label_id: MBID, alias_limit: int = 10) -> str:
    """Get details about a record label including type, area, tags, and URLs.
    Args:
        label_id: The MBID
        alias_limit: Max number of aliases to show (default 10)
    """
    res = musicbrainzngs.get_label_by_id(
        label_id,
        includes=["aliases", "tags", "ratings", "url-rels", "annotation"],
    )
    lb = res["label"]
    aliases, tags = _extract_aliases_and_tags(lb, alias_limit)
    urls = "\n".join(f"  - {r['type']}: {r['target']}" for r in lb.get("url-relation-list", []))
    lifespan = lb.get("life-span", {})
    begin = lifespan.get("begin", "?")
    end = lifespan.get("end", "present")

    rating_str = _fmt_rating(lb)

    parts = [
        f"Name: {lb['name']}",
        f"Type: {lb.get('type', 'N/A')}",
        f"Country: {lb.get('country', 'N/A')}",
        f"Founded: {begin} to {end}",
        f"Label code: {lb.get('label-code', 'N/A')}",
        f"Tags: {tags or 'None listed'}",
        f"Rating: {rating_str}",
        f"Aliases: {aliases or 'None'}",
        f"MBID: {lb['id']}",
    ]
    _append_extras(parts, lb)
    if urls:
        parts.append(f"URLs:\n{urls}")
    return "\n".join(parts)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def lookup_recording_by_isrc(isrc: str) -> str:
    """
    Lookup a recording by its International Standard Recording Code (ISRC).
    This is the global ID used by Spotify, Apple Music, and record labels.
    Accepts both formatted (FI-UM7-07-00377) and compact (FIUM70700377) forms.
    """
    isrc = isrc.replace("-", "").replace(" ", "").upper()
    try:
        res = musicbrainzngs.get_recordings_by_isrc(isrc, includes=["artists", "releases"])
    except musicbrainzngs.ResponseError:
        return f"No recording found for ISRC: {isrc}"

    recordings = res.get("isrc", {}).get("recording-list", [])
    if not recordings:
        return f"No recording found for ISRC: {isrc}"

    lines = [f"Found {len(recordings)} recording(s) for ISRC {isrc}:"]
    for rec in recordings:
        title = rec.get("title", "Unknown")
        artist = rec.get("artist-credit-phrase", "Unknown")
        rec_id = rec.get("id")
        lines.append(f"  - {title} by {artist} | recording ID: {rec_id}")

    return "\n".join(lines)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def lookup_work_by_iswc(iswc: str) -> str:
    """
    Lookup a musical work (composition/sheet music) by its ISWC.
    This is the global ID used by music publishers and royalty societies.
    Accepts both formatted (T-345.246.800-1) and compact (T3452468001) forms.
    """
    # Normalize to formatted form: T-NNN.NNN.NNN-C
    clean = iswc.replace("-", "").replace(".", "").replace(" ", "").upper()
    if len(clean) == 11 and clean[0] == "T":
        iswc = f"{clean[0]}-{clean[1:4]}.{clean[4:7]}.{clean[7:10]}-{clean[10]}"
    else:
        iswc = clean
    try:
        res = musicbrainzngs.get_works_by_iswc(iswc)
    except musicbrainzngs.ResponseError:
        return f"No works found for ISWC: {iswc}"

    works = res.get("work-list", [])
    if not works:
        return f"No works found for ISWC: {iswc}"

    lines = [f"Found {len(works)} work(s) for ISWC {iswc}:"]
    for w in works:
        title = w.get("title", "Unknown")
        w_id = w.get("id")
        lines.append(f"  - {title} | work ID: {w_id}")

    return "\n".join(lines)


ENTITY_LOOKUP_FUNCS: dict[str, str] = {
    "artist": "get_artist_by_id",
    "release": "get_release_by_id",
    "release-group": "get_release_group_by_id",
    "recording": "get_recording_by_id",
    "work": "get_work_by_id",
    "label": "get_label_by_id",
    "area": "get_area_by_id",
    "place": "get_place_by_id",
    "event": "get_event_by_id",
    "instrument": "get_instrument_by_id",
    "series": "get_series_by_id",
}

# Relationship includes available for all entity types.
ALL_REL_INCLUDES = [
    "area-rels",
    "artist-rels",
    "event-rels",
    "instrument-rels",
    "label-rels",
    "place-rels",
    "recording-rels",
    "release-group-rels",
    "release-rels",
    "series-rels",
    "url-rels",
    "work-rels",
]


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def get_entity_relationships(entity_type: str, entity_id: MBID, include_rels: list[str] | None = None) -> str:
    """
    Get relationships for any entity type (e.g., band members, producers,
    recording studios, Wikipedia links).
    For performer credits on recordings, prefer get_album_tracks (whole album)
    or get_recording_details (single track) which include them directly.
    Args:
        entity_type: artist, release, release-group, recording, work, label, area,
                     place, event, instrument, series
        entity_id: The MBID (must match the entity_type)
        include_rels: Which relationship types to fetch. Default (None) fetches
            artist-rels and url-rels. Available types:
            - area-rels: linked geographic areas
            - artist-rels: linked artists (members, producers, performers)
            - event-rels: linked events
            - instrument-rels: linked instruments
            - label-rels: linked labels (publishers, distributors)
            - place-rels: linked places (studios, venues)
            - recording-rels: linked recordings
            - release-group-rels: linked release groups
            - release-rels: linked releases
            - series-rels: linked series
            - url-rels: linked URLs (Wikipedia, Discogs, etc.)
            - work-rels: linked works
    """
    if entity_type not in ENTITY_LOOKUP_FUNCS:
        return f"Invalid entity type. Choose from: {', '.join(ENTITY_LOOKUP_FUNCS.keys())}"

    if include_rels is None:
        includes = ["artist-rels", "url-rels"]
    else:
        invalid = [r for r in include_rels if r not in ALL_REL_INCLUDES]
        if invalid:
            return f"Invalid relationship types: {', '.join(invalid)}. Valid: {', '.join(ALL_REL_INCLUDES)}"
        includes = include_rels

    func = getattr(musicbrainzngs, ENTITY_LOOKUP_FUNCS[entity_type])
    res = func(entity_id, includes=includes)
    entity = res.get(entity_type)
    if not entity:
        return f"No data found for {entity_type} {entity_id}."

    lines = [f"Relationships for {entity_type} {entity_id}:"]
    found = False

    # Entity keys that use "name" vs "title"
    _TITLE_KEYS = {"work", "release", "release-group", "recording"}

    # Standardize relation list keys (artist-relation-list, url-relation-list, etc.)
    for key, value in entity.items():
        if key.endswith("-relation-list") and isinstance(value, list):
            # Derive target entity type from key (e.g. "artist-relation-list" -> "artist")
            rel_entity_type = key.removesuffix("-relation-list")
            for rel in value:
                rtype = rel.get("type", "Unknown")
                attrs = rel.get("attribute-list", [])
                target_entity = rel.get(rel_entity_type, {})
                name_key = "title" if rel_entity_type in _TITLE_KEYS else "name"
                target_name = target_entity.get(name_key) or rel.get("target", "Unknown")
                target_id = target_entity.get("id", "")

                attrs_str = f" ({', '.join(attrs)})" if attrs else ""
                id_str = f" | {rel_entity_type} ID: {target_id}" if target_id else ""

                # Date range (e.g. band membership periods)
                begin = rel.get("begin", "")
                end = rel.get("end", "")
                date_str = f" [{begin or '?'}–{end or 'present'}]" if begin or end else ""

                lines.append(f"  - {rtype.capitalize()}{attrs_str}: {target_name}{date_str}{id_str}")
                found = True

    if not found:
        return f"No relationships found for this {entity_type}."

    return "\n".join(lines)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def get_cover_art_urls(release_id: MBID) -> str:
    """Get cover art image URLs for a specific release (edition)
    from the Cover Art Archive.
    Takes a release_id, NOT a release_group_id.
    Returns URLs for front/back covers and thumbnails."""
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


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def get_release_group_cover_art(release_group_id: MBID) -> str:
    """Get cover art image URLs for a release group (album/EP concept)
    from the Cover Art Archive.
    Takes a release_group_id, NOT a release_id.
    Returns URLs for front covers and thumbnails."""
    try:
        images = musicbrainzngs.get_release_group_image_list(release_group_id)
    except musicbrainzngs.ResponseError as e:
        # A 404 error from the archive simply means no art is uploaded yet,
        # which is common. We catch it here to return a friendly message to the AI.
        if e.cause and getattr(e.cause, "code", None) == 404:
            return f"No cover art available for release group {release_group_id} in the archive."
        # If it's a different error (like 503), let the @cached_tool decorator handle it
        raise e

    img_list = images.get("images", [])
    if not img_list:
        return "No cover art images available."

    lines = [f"Cover art for release group {release_group_id} ({len(img_list)} images):"]
    for img in img_list:
        types = ", ".join(img.get("types", ["Unknown"]))
        lines.append(f"- [{types}] {img.get('image', 'N/A')}")
        thumbs = img.get("thumbnails", {})
        if thumbs:
            thumb_url = thumbs.get("500") or thumbs.get("large", "")
            if thumb_url:
                lines.append(f"  Thumbnail: {thumb_url}")
    return "\n".join(lines)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
@cached_tool()
def search_entities_fuzzy(entity_type: str, query: str, limit: int = 5) -> str:
    """
    Typo-tolerant fuzzy search. Tries an exact search first, then falls back to
    fuzzy matching if no results are found.
    Supports entity types: artist, release, recording, label, work,
    release-group, area, event, instrument, place, series.
    Use when the query may contain misspellings (e.g., 'Bjork' -> 'Björk').
    """
    # Try exact search first
    exact = _search_entities(entity_type=entity_type, query=query, limit=limit)
    if not exact.startswith("Found 0"):
        return exact

    # Fall back to fuzzy matching
    fuzzy_query = " ".join([f"{word}~" for word in query.split()])
    return _search_entities(entity_type=entity_type, query=fuzzy_query, limit=limit)


@mcp.tool(annotations={"readOnlyHint": False, "idempotentHint": True, "openWorldHint": False})
def clear_cache() -> str:
    """Clear the local response cache. Only use when the user explicitly asks to refresh cached data."""
    cache.clear()
    return "Cache cleared."
