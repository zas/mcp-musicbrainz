from mcp_musicbrainz.server import mcp


def main():
    print("Starting MusicBrainz FastMCP Server over HTTP/SSE on port 8000...")
    mcp.run(transport="sse", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
