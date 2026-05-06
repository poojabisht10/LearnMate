from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import urllib.request
import re

try:
    from pytube import YouTube
except ImportError:
    YouTube = None


def extract_video_id(url):
    parsed_url = urlparse(url)

    if parsed_url.hostname == "youtu.be":
        return parsed_url.path[1:]

    if parsed_url.hostname in ("www.youtube.com", "youtube.com"):
        return parse_qs(parsed_url.query)["v"][0]


def get_video_title(url):
    """
    Fetch YouTube video title.
    Tries pytube first, then falls back to scraping page HTML.
    Returns None if all methods fail.
    """
    try:
        # Method 1: Try pytube
        if YouTube is not None:
            try:
                yt = YouTube(url)
                title = yt.title
                if title and title.strip() and title != "YouTube Video":
                    return title
            except Exception as e:
                print(f"Pytube failed: {e}")
        
        # Method 2: Try scraping HTML
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                html = response.read().decode('utf-8')
                # Look for title in meta tags
                match = re.search(r'<meta\s+name="title"\s+content="([^"]*)"', html)
                if match:
                    title = match.group(1)
                    if title and title.strip():
                        return title
                
                # Alternative: Look for og:title
                match = re.search(r'<meta\s+property="og:title"\s+content="([^"]*)"', html)
                if match:
                    title = match.group(1)
                    if title and title.strip():
                        return title
        except Exception as e:
            print(f"HTML scraping failed: {e}")
        
        return None
    
    except Exception as e:
        print(f"Error fetching video title: {e}")
        return None


def format_timestamp(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"


def load_youtube_transcript(url, chunk_duration=30):
    try:
        video_id = extract_video_id(url)
        video_title = get_video_title(url)

        # Create API instance and fetch transcript
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id, languages=['en', 'hi'])

        # Group snippets into 30-second chunks
        chunks = {}
        docs = []

        for snippet in transcript:
            start = snippet.start
            chunk_start = int(start // chunk_duration) * chunk_duration

            if chunk_start not in chunks:
                chunks[chunk_start] = []

            chunks[chunk_start].append(snippet)

        # Create documents for each chunk
        for chunk_start, snippets in sorted(chunks.items()):
            # Combine text from all snippets in this chunk
            combined_text = " ".join(snippet.text for snippet in snippets)

            # Calculate chunk end time
            chunk_end = chunk_start + chunk_duration

            # Base URL without timestamp (for deduplication)
            base_url = f"https://www.youtube.com/watch?v={video_id}"
            # Timestamped URL for direct playback
            timestamped_url = f"{base_url}&t={int(chunk_start)}s"

            docs.append({
                "text": combined_text,
                "timestamp_seconds": chunk_start,
                "timestamp": format_timestamp(chunk_start),
                "chunk_end_seconds": chunk_end,
                "chunk_end_timestamp": format_timestamp(chunk_end),
                "source": base_url,  # Use base URL for source deduplication
                "timestamped_link": timestamped_url,  # Keep timestamp URL if needed
                "chunk_duration": chunk_duration,
                "video_title": video_title,  # Include video title
                "video_id": video_id,  # Include video ID
            })

        return docs

    except Exception as e:
        error_name = type(e).__name__
        if "IpBlocked" in error_name:
            print(f"Error: YouTube is blocking requests from this IP address. This is common when using YouTube APIs.")
            print("Solutions:")
            print("1. Use a VPN or proxy service")
            print("2. Try from a different network")
            print("3. Wait a few hours before trying again")
            print("4. For production use, consider using residential proxies")
        elif "NoTranscriptFound" in error_name:
            print(f"Error: No transcript available for video {url}")
            print("This video may not have captions/subtitles available.")
        else:
            print(f"Error loading transcript: {error_name}: {e}")
        return []


if __name__ == "__main__":
    # Note: YouTube may block requests from certain IP addresses/networks
    # If you get an IpBlocked error, try using a VPN or different network
    # For production use, consider using residential proxies

    # Test with a popular video that usually has transcripts
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up

    data = load_youtube_transcript(url)

    if data:
        print(f"Successfully loaded {len(data)} transcript chunks (60 seconds each)")
        print(f"Total chunks: {len(data)}")
        for i, d in enumerate(data[:3]):  # Show first 3 chunks
            print(f"\nChunk {i+1}:")
            print(f"  Time: {d['timestamp']} - {d['chunk_end_timestamp']}")
            print(f"  Text: {d['text'][:100]}..." if len(d['text']) > 100 else f"  Text: {d['text']}")
    else:
        print("Failed to load transcript. This could be due to:")
        print("- Video has no available transcripts/captions")
        print("- YouTube blocking requests from this IP (common issue)")
        print("- Network connectivity issues")
        print("\nTry a different video URL or use a VPN if IP blocking persists.")