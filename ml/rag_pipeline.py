"""
Standalone RAG Pipeline — run queries directly from the command line.

Usage:
  python rag_pipeline.py --prompt "What are the key digital initiatives?" --state "Delhi" --month "2025-01"
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.rag_service import run_rag
from app.utils.logger import get_logger

logger = get_logger("rag_pipeline")


def main():
    parser = argparse.ArgumentParser(description="NeGD RAG Pipeline CLI")
    parser.add_argument("--prompt", required=True, help="Question to ask")
    parser.add_argument("--state", help="Filter by state name")
    parser.add_argument("--month", help="Filter by month (YYYY-MM)")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"Query:  {args.prompt}")
    print(f"State:  {args.state or 'All'}")
    print(f"Month:  {args.month or 'All'}")
    print(f"{'='*60}\n")

    result = run_rag(prompt=args.prompt, state=args.state, month=args.month)

    print("ANSWER")
    print("-" * 60)
    print(result.answer)

    print(f"\nSOURCES ({result.chunks_retrieved} chunks retrieved)")
    print("-" * 60)
    for i, src in enumerate(result.sources, 1):
        print(f"{i}. State: {src.state} | Month: {src.month} | Section: {src.section} | Similarity: {src.similarity}")


if __name__ == "__main__":
    main()
