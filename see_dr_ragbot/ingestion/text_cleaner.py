"""Text cleaning utilities to remove boilerplate and unwanted content"""
from __future__ import annotations
import re
from typing import List


# Common patterns to remove
BOILERPLATE_PATTERNS = [
    r"©.*?All rights reserved",
    r"©.*?rights reserved",
    r"Published by.*?Inc\.?\s*All rights reserved",
    r"https?://[^\s]+",  # URLs
    r"DOI:\s*https?://[^\s]+",  # DOI links
    r"URL:\s*https?://[^\s]+",  # URL links
    r"www\.[^\s]+",  # www URLs without http
    r"doi\.org/[^\s]+",  # DOI URLs
    r"\(cid:\d+\)",  # Character ID placeholders from PDFs
    r"Received:.*?Published:.*?Date:",  # Publication metadata lines
    r"Volume\s+\d+.*?Issue\s+\d+",  # Volume/Issue info
    r"Page\s+\d+.*?of\s+\d+",  # Page numbers
    r"Figure\s+\d+[:.]?",  # Figure references (standalone)
    r"Table\s+\d+[:.]?",  # Table references (standalone)
    r"^[\d\s-]+$",  # Lines that are only numbers/dashes
    r"^\s*[©®™]\s*$",  # Lines with only copyright symbols
    r"^Key Words?:.*?$",  # Keyword lines
    r"^Abbreviations?:.*?$",  # Abbreviation lines
    r"^Abstract$",
    r"^Introduction$",
    r"^References?$",
    r"^Acknowledgments?$",
    r"^\s*\d+\s*$",  # Standalone page numbers
    r"Scientific Reports.*?\([0-9]{4}\)",  # Journal header
    r"Vol:\.\s*\(.*?\)",  # Volume formatting
    r"nature\.com/scientificreports",  # Journal URLs
    r"WJM\s+https?://[^\s]*",  # WJM journal URLs
    r"wjgnet\.com[^\s]*",  # wjgnet URLs
    r"Citation:\s*[A-Z].*?(?:URL:|DOI:|$)",  # Citation lines
    r"^Citation:.*?$",  # Citation headers
    r"URL:\s*DOI:",  # Malformed URL/DOI lines
    r"DOI:\s*$",  # Empty DOI lines
    r"URL:\s*$",  # Empty URL lines
]


def clean_text(text: str) -> str:
    """Clean text by removing boilerplate and unwanted patterns"""
    if not text:
        return ""
    
    # Remove patterns
    cleaned = text
    for pattern in BOILERPLATE_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
    
    # Remove excessive whitespace
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)  # Max 2 newlines
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)  # Multiple spaces to single
    cleaned = re.sub(r"^\s+|\s+$", "", cleaned, flags=re.MULTILINE)  # Trim lines
    
    # Remove very short lines that are likely artifacts
    lines = cleaned.split("\n")
    filtered_lines = []
    for line in lines:
        line = line.strip()
        if len(line) < 3:  # Skip very short lines
            continue
        # Skip lines that are mostly special characters
        if len(re.sub(r"[^\w\s]", "", line)) < len(line) * 0.3 and len(line) < 20:
            continue
        filtered_lines.append(line)
    
    cleaned = "\n".join(filtered_lines)
    
    # Final cleanup
    cleaned = re.sub(r"\s+", " ", cleaned)  # Normalize whitespace
    cleaned = cleaned.strip()
    
    return cleaned


def clean_chunk_text(text: str) -> str:
    """Clean chunk text while preserving sentence structure"""
    cleaned = clean_text(text)
    # Ensure sentences are properly separated
    cleaned = re.sub(r"\.([A-Z])", r". \1", cleaned)
    return cleaned

