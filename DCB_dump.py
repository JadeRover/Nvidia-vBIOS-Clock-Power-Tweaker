"""Small CLI helper for NVCPR v1.2 DCB display-config summaries."""
import sys
from pathlib import Path
from CPR_DCB import DCBParser


def main(argv):
    if len(argv) < 2:
        print("Usage: python DCB_dump.py <vbios.rom|vbios.bin> [--all-copies]")
        return 2
    path = Path(argv[1])
    data = path.read_bytes()
    parser = DCBParser(data)
    print(f"File: {path}")
    print(parser.summarize(include_duplicates="--all-copies" in argv[2:]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
