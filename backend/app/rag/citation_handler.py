def format_citations(retrieved_docs):
    """
    Format citations from retrieved documents.

    Returns a list of formatted citation dictionaries.
    """

    seen = set()
    formatted = []

    for doc in retrieved_docs:

        meta = doc.get("metadata", {})
        source_type = meta.get("source", "unknown")

        # Unique key to avoid duplicates
        unique_key = str(meta)

        if unique_key in seen:
            continue

        seen.add(unique_key)

        # -------------------------
        # YouTube Source
        # -------------------------
        if source_type == "youtube":

            formatted.append({
                "type": "YouTube",
                "title": meta.get("title", "YouTube Video"),
                "timestamp": meta.get("timestamp", "N/A"),
                "link": meta.get("link", ""),
                "display": f"{meta.get('title', '')} ({meta.get('timestamp', 'N/A')})"
            })

        # -------------------------
        # PDF Source
        # -------------------------
        elif source_type == "pdf":

            formatted.append({
                "type": "PDF",
                "file": meta.get("filename", "Document"),
                "page": meta.get("page", "N/A"),
                "display": f"{meta.get('filename', 'Document')} (Page {meta.get('page', 'N/A')})"
            })

        # -------------------------
        # Default / Other Sources
        # -------------------------
        else:

            formatted.append({
                "type": source_type,
                "display": meta.get("title", "Unknown Source")
            })

    return formatted


# -------------------------
# Pretty Print (for terminal)
# -------------------------

def print_citations(citations):
    """
    Nicely print citations in terminal
    """

    print("\n📚 SOURCES:\n")

    for c in citations:

        if c["type"] == "YouTube":
            print(f"📺 {c['display']}")
            if c.get("link"):
                print(f"🔗 {c['link']}")

        elif c["type"] == "PDF":
            print(f"📄 {c['display']}")

        else:
            print(f"📌 {c['display']}")

        print()