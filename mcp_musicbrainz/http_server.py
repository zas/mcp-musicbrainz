import os

from mcp_musicbrainz.server import mcp


def main():
    host = os.environ.get("MCP_MUSICBRAINZ_HTTP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_MUSICBRAINZ_HTTP_PORT", "8000"))

    print(f"Starting MusicBrainz FastMCP Server over Streamable HTTP on {host}:{port}...")
    mcp.run(transport="http", host=host, port=port)


if __name__ == "__main__":
    main()
