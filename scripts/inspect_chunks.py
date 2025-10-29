#!/usr/bin/env python3
"""Inspect extracted chunks from PDF ingestion"""
import sys
import os
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from see_dr_ragbot.config import load_config

console = Console()


def inspect_chunks(processed_dir: str, limit: int = 10):
    """Display extracted chunks in a readable format"""
    files = [f for f in os.listdir(processed_dir) if f.endswith(".jsonl")]
    
    if not files:
        console.print("[red]No processed chunks found. Run build_index.py first.[/red]")
        return
    
    console.print(f"[green]Found {len(files)} processed documents[/green]\n")
    
    for filename in files[:limit]:
        filepath = os.path.join(processed_dir, filename)
        doc_id = os.path.splitext(filename)[0]
        
        chunks = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    chunks.append(json.loads(line))
        
        if not chunks:
            continue
        
        # Get document metadata from first chunk
        meta = chunks[0].get("metadata", {})
        title = meta.get("title", "Unknown")
        
        table = Table(title=f"{title} ({len(chunks)} chunks)")
        table.add_column("Chunk", style="cyan", width=6)
        table.add_column("Tokens", style="yellow", width=8)
        table.add_column("Preview", style="white", width=80)
        table.add_column("Page", style="magenta", width=6)
        
        for i, chunk in enumerate(chunks, 1):
            text = chunk.get("text", "")
            preview = text[:100] + "..." if len(text) > 100 else text
            tokens = chunk.get("tokens", 0)
            page = chunk.get("metadata", {}).get("page_number", "?")
            
            table.add_row(str(i), str(tokens), preview, str(page))
        
        console.print(Panel(table, border_style="blue"))
        console.print()
        
        # Show a full example
        if chunks:
            example = chunks[0]
            console.print(Panel(
                f"[bold]Full Text:[/bold]\n{example.get('text', '')[:500]}...",
                title=f"Example Chunk 1",
                border_style="green"
            ))
            console.print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Inspect extracted PDF chunks")
    parser.add_argument("--limit", type=int, default=5, help="Max docs to show")
    args = parser.parse_args()
    
    cfg = load_config()
    inspect_chunks(cfg.paths.processed_dir, limit=args.limit)

