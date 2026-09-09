#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests",
#     "beautifulsoup4",
#     "mcp<2",  # server uses FastMCP, renamed to MCPServer in mcp 2.x
#     "pypdf",
# ]
# ///
"""
MCP server for fetching arXiv papers as plain text.

Input: arXiv ID (e.g., "2502.16681" or "2502.16681v1")
Output: Full paper text extracted from HTML

Usage:
    Add to ~/.claude.json via: claude mcp add arxiv python /path/to/arxiv_server.py
"""

import hashlib
import io
import os
import re
import time
import requests
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP
from pypdf import PdfReader

mcp = FastMCP("arxiv")

# Rate limiting: arXiv asks for 1 request per 3 seconds
_last_request_time = 0

# Cache fetched papers to avoid re-fetching for chunked reads
_paper_cache: dict[str, str] = {}

def _rate_limit():
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < 3:
        time.sleep(3 - elapsed)
    _last_request_time = time.time()

def _clean_arxiv_id(arxiv_id: str) -> str:
    """Extract arxiv ID from various input formats."""
    # Handle full URLs
    if "arxiv.org" in arxiv_id:
        match = re.search(r'(\d{4}\.\d{4,5})(v\d+)?', arxiv_id)
        if match:
            return match.group(0)
    # Handle bare IDs
    match = re.match(r'^(\d{4}\.\d{4,5})(v\d+)?$', arxiv_id.strip())
    if match:
        return match.group(0)
    return arxiv_id.strip()

def _extract_text_from_html(html: str) -> str:
    """Extract clean text from arXiv HTML."""
    soup = BeautifulSoup(html, 'html.parser')

    # Remove script, style, nav elements
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        tag.decompose()

    # Drop the style-violation banner arXiv's renderer injects above the title.
    for tag in soup.find_all(class_=lambda c: c and 'ltx_ERROR' in c):
        tag.decompose()

    # LaTeXML keeps the original LaTeX on every <math> as alttext=. Rendered MathML
    # flattens to symbol soup (D_{KL} becomes an unsubscripted glyph run), so swap each
    # one for its source wrapped in $.
    for node in soup.find_all('math'):
        latex = node.get('alttext')
        node.replace_with(f" ${latex}$ " if latex else node.get_text(strip=True))

    # Try to find main article content
    article = soup.find('article') or soup.find('main') or soup.find('div', class_='ltx_page_content')

    if article:
        content = article
    else:
        content = soup.body or soup

    # Extract text with some structure preservation
    lines = []

    # LaTeXML renders code listings as div.ltx_listingline, never as <pre>, so a
    # tag-only whitelist silently drops prompt and code appendices.
    def _wanted(tag):
        if tag.name in ('h1', 'h2', 'h3', 'h4', 'p', 'li', 'figcaption', 'td', 'th',
                        'pre', 'blockquote'):
            return True
        classes = tag.get('class') or []
        return any(c in ('ltx_listingline', 'ltx_verbatim') for c in classes)

    for element in content.find_all(_wanted):
        classes = element.get('class') or []
        verbatim = element.name == 'pre' or 'ltx_verbatim' in classes
        text = element.get_text(separator='\n' if verbatim else ' ', strip=True)
        if not text:
            continue

        # Add markdown-style headers
        if element.name == 'h1':
            lines.append(f"\n# {text}\n")
        elif element.name == 'h2':
            lines.append(f"\n## {text}\n")
        elif element.name == 'h3':
            lines.append(f"\n### {text}\n")
        elif element.name == 'h4':
            lines.append(f"\n#### {text}\n")
        elif element.name == 'li':
            lines.append(f"- {text}")
        else:
            lines.append(text)

    return '\n'.join(lines)

_REFS_HEADING = re.compile(r"^#+\s*(references|bibliography)\s*$", re.M | re.I)


def _strip_references(text: str) -> tuple[str, int]:
    """Cut everything from the last References heading. Returns (text, chars_dropped)."""
    matches = list(_REFS_HEADING.finditer(text))
    if not matches:
        return text, 0
    cut = matches[-1].start()
    return text[:cut].rstrip(), len(text) - cut


def _extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    lines = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            lines.append(text)
    return '\n\n'.join(lines)

def _fetch_paper(arxiv_id: str) -> str:
    """Fetch paper, using cache if available. Tries HTML first, falls back to PDF."""
    clean_id = _clean_arxiv_id(arxiv_id)

    if clean_id in _paper_cache:
        return _paper_cache[clean_id]

    headers = {
        'User-Agent': 'arxiv-mcp-server/1.0 (research tool; respects rate limits)'
    }

    # Try HTML first (better formatting)
    _rate_limit()
    html_url = f"https://arxiv.org/html/{clean_id}"
    try:
        response = requests.get(html_url, headers=headers, timeout=30)
        if response.status_code == 200:
            text = _extract_text_from_html(response.text)
            if len(text) >= 500:
                full_text = f"# arXiv:{clean_id}\nSource: {html_url}\n\n{text}"
                _paper_cache[clean_id] = full_text
                return full_text
    except requests.exceptions.RequestException:
        pass  # Fall through to PDF

    # Fall back to PDF
    _rate_limit()
    pdf_url = f"https://arxiv.org/pdf/{clean_id}.pdf"
    try:
        response = requests.get(pdf_url, headers=headers, timeout=60)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            return f"Error: Paper {clean_id} not found on arXiv."
        return f"Error fetching PDF: {e}"
    except requests.exceptions.RequestException as e:
        return f"Error fetching PDF: {e}"

    try:
        text = _extract_text_from_pdf(response.content)
    except Exception as e:
        return f"Error extracting text from PDF: {e}"

    if len(text) < 500:
        return f"Error: Could not extract meaningful content from {pdf_url}."

    full_text = f"# arXiv:{clean_id}\nSource: {pdf_url} (PDF)\n\n{text}"
    _paper_cache[clean_id] = full_text
    return full_text

@mcp.tool()
def fetch_arxiv_paper(
    arxiv_id: str,
    chunk: int | None = None,
    chunk_size: int = 15000,
    save_to: str | None = None,
    include_references: bool = False,
) -> str:
    """
    Fetch an arXiv paper as markdown. Tries the HTML render, falls back to the PDF.

    Args:
        arxiv_id: arXiv ID ("2502.16681", "2502.16681v1", or a full URL)
        chunk: Which chunk to return (0-indexed). None returns the whole paper.
        chunk_size: Characters per chunk (default 15000, roughly 4k tokens)
        save_to: Write the complete paper to this path and return a receipt instead of
            the text. Use it to archive a paper without carrying it through context.
            No default — the caller owns the location.
        include_references: Keep the bibliography. Off by default; it is 40-50% of a
            typical paper and is dead weight for summarization.

    Returns:
        The requested chunk, the whole paper, or a save receipt when save_to is set.
    """
    text = _fetch_paper(arxiv_id)

    if text.startswith("Error:"):
        return text

    dropped = 0
    if not include_references:
        text, dropped = _strip_references(text)
    note = f", {dropped:,} chars of references omitted" if dropped else ""

    if save_to:
        path = os.path.abspath(os.path.expanduser(save_to))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        return (f"Saved {len(text):,} chars to {path}{note}\n"
                f"sha256:{digest}\n"
                f"Read it with the Read tool, or call again with chunk=N to page through.")

    total_chars = len(text)
    total_chunks = (total_chars + chunk_size - 1) // chunk_size

    if chunk is None:
        return f"[Full paper: {total_chars:,} chars, {total_chunks} chunks of {chunk_size:,}{note}]\n\n{text}"

    start = chunk * chunk_size
    end = start + chunk_size

    if start >= total_chars:
        return f"Error: Chunk {chunk} out of range. Paper has {total_chunks} chunks (0-{total_chunks-1})."

    return (f"[Chunk {chunk}/{total_chunks-1}, chars {start:,}-{min(end, total_chars):,} "
            f"of {total_chars:,}{note}]\n\n{text[start:end]}")

if __name__ == "__main__":
    mcp.run()
