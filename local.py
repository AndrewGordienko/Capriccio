"""Build/query a local POLARIS landmark fingerprint catalog (no online catalog)."""
import argparse
import json

from polaris.engine import Polaris, build_reference_index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("index")
    build.add_argument("database")
    build.add_argument("files", nargs="+")
    query = commands.add_parser("query")
    query.add_argument("database")
    query.add_argument("file")
    query.add_argument("--mode", choices=["o", "a", "f"], default="a")
    args = parser.parse_args()
    if args.command == "index":
        count = build_reference_index(args.files, args.database)
        print(json.dumps({"inserted": count}))
    else:
        with Polaris(args.database) as matcher:
            result = matcher.recognize_file(args.file, mode=args.mode, topn=5)
        # Return evidence rather than labeling an uncalibrated top candidate a match.
        result["status"] = "candidate_ranking_only"
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
