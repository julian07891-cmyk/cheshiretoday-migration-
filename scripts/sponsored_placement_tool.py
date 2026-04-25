#!/usr/bin/env python3
"""
Sponsored placement helper for Cheshire Today.

Examples:

List active article sidebar adverts:
  python3 scripts/sponsored_placement_tool.py list --placement article_sidebar

Create/update desktop sidebar advert:
  python3 scripts/sponsored_placement_tool.py upsert \
    --slug local-business-april-2026 \
    --placement article_sidebar \
    --sponsor-name "Example Cheshire Business" \
    --title "Book your free local consultation" \
    --description "A short sponsored message for Cheshire readers." \
    --target-url "https://example.com" \
    --cta-text "Visit sponsor" \
    --priority 10

Create/update mobile article advert:
  python3 scripts/sponsored_placement_tool.py upsert \
    --slug local-business-april-2026-mobile \
    --placement article_mobile \
    --sponsor-name "Example Cheshire Business" \
    --title "Book your free local consultation" \
    --description "A short sponsored message for mobile readers." \
    --target-url "https://example.com" \
    --cta-text "Visit sponsor" \
    --priority 10

Delete an advert:
  python3 scripts/sponsored_placement_tool.py delete --slug local-business-april-2026
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.server import db  # noqa: E402


VALID_PLACEMENTS = {"article_sidebar", "article_mobile"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value):
    return str(value or "").strip()


async def list_placements(args):
    query = {}
    if args.placement:
        query["placement"] = args.placement
    if not args.include_inactive:
        query["active"] = True

    cursor = db.sponsored_placements.find(query).sort([("priority", -1), ("updated_at", -1)]).limit(args.limit)
    rows = []
    async for doc in cursor:
        doc["id"] = str(doc.get("_id", ""))
        doc.pop("_id", None)
        rows.append(doc)

    print(json.dumps({"count": len(rows), "placements": rows}, indent=2, default=str))


async def upsert_placement(args):
    placement = clean(args.placement)
    target_url = clean(args.target_url)

    if placement not in VALID_PLACEMENTS:
        raise SystemExit(f"Invalid placement. Use one of: {', '.join(sorted(VALID_PLACEMENTS))}")

    if not target_url.startswith(("https://", "http://")):
        raise SystemExit("target-url must start with http:// or https://")

    required = {
        "slug": args.slug,
        "sponsor_name": args.sponsor_name,
        "title": args.title,
        "target_url": target_url,
    }
    missing = [k for k, v in required.items() if not clean(v)]
    if missing:
        raise SystemExit("Missing required fields: " + ", ".join(missing))

    timestamp = now_iso()
    doc = {
        "slug": clean(args.slug),
        "placement": placement,
        "sponsor_name": clean(args.sponsor_name),
        "title": clean(args.title),
        "description": clean(args.description),
        "target_url": target_url,
        "image_url": clean(args.image_url),
        "cta_text": clean(args.cta_text) or "Learn more",
        "package_tier": clean(args.package_tier),
        "rotation_weight": int(args.rotation_weight or 0) or None,
        "active": not args.inactive,
        "priority": int(args.priority or 0),
        "starts_at": clean(args.starts_at) or None,
        "ends_at": clean(args.ends_at) or None,
        "updated_at": timestamp,
    }

    await db.sponsored_placements.update_one(
        {"slug": doc["slug"]},
        {"$set": doc, "$setOnInsert": {"created_at": timestamp}},
        upsert=True,
    )

    saved = await db.sponsored_placements.find_one({"slug": doc["slug"]})
    saved["id"] = str(saved.get("_id", ""))
    saved.pop("_id", None)
    print(json.dumps({"success": True, "placement": saved}, indent=2, default=str))


async def delete_placement(args):
    slug = clean(args.slug)
    if not slug:
        raise SystemExit("slug is required")

    result = await db.sponsored_placements.delete_one({"slug": slug})
    print(json.dumps({"success": True, "deleted_count": result.deleted_count}, indent=2))


async def main():
    parser = argparse.ArgumentParser(description="Manage Cheshire Today sponsored placements")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list")
    list_parser.add_argument("--placement", choices=sorted(VALID_PLACEMENTS))
    list_parser.add_argument("--include-inactive", action="store_true")
    list_parser.add_argument("--limit", type=int, default=20)

    upsert_parser = sub.add_parser("upsert")
    upsert_parser.add_argument("--slug", required=True)
    upsert_parser.add_argument("--placement", required=True, choices=sorted(VALID_PLACEMENTS))
    upsert_parser.add_argument("--sponsor-name", required=True)
    upsert_parser.add_argument("--title", required=True)
    upsert_parser.add_argument("--description", default="")
    upsert_parser.add_argument("--target-url", required=True)
    upsert_parser.add_argument("--image-url", default="")
    upsert_parser.add_argument("--cta-text", default="Learn more")
    upsert_parser.add_argument("--package-tier", default="")
    upsert_parser.add_argument("--rotation-weight", type=int, default=0)
    upsert_parser.add_argument("--priority", type=int, default=0)
    upsert_parser.add_argument("--starts-at", default="")
    upsert_parser.add_argument("--ends-at", default="")
    upsert_parser.add_argument("--inactive", action="store_true")

    delete_parser = sub.add_parser("delete")
    delete_parser.add_argument("--slug", required=True)

    args = parser.parse_args()

    if args.command == "list":
        await list_placements(args)
    elif args.command == "upsert":
        await upsert_placement(args)
    elif args.command == "delete":
        await delete_placement(args)


if __name__ == "__main__":
    asyncio.run(main())
