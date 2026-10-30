#!/usr/bin/env python3
"""
Merge externally produced tags (from a Claude chat) into signs.json.

Usage:
    python3 merge_tags.py mytags.json

- Matches each entry to an uploaded image by its ORIGINAL filename
  (stored as `source_filename` when you upload through upload.html).
- Fills in the fields, in the same structure tagger.py writes.
- Only touches fields you actually provide; leaves everything else alone.
- Prints a report: matched, not-found, and any values outside the
  current vocabulary (kept anyway, just flagged for your review).
- Makes a backup at signs.json.bak before saving.

The tags file is a JSON list, one object per image, e.g.:
[
  {
    "filename": "myphoto_01.jpg",
    "text_content": "OPEN",
    "medium": "sign_painting",
    "surface": "glass",
    "lettering_style": "casual_script",
    "decorative_technique": ["outline"],
    "finish": "gloss",
    "condition": "good",
    "colors": ["red", "white"],
    "era_estimate": "2010s",
    "country_hint": "United Kingdom",
    "description": "one sentence.",
    "tags": ["sign_painting", "shop_window"]
  }
]
"""

import json, sys, shutil, os

SIGNS = "signs.json"

# Fields the chat may provide. Lists get stored as lists; the rest as text.
SINGLE_FIELDS = ["text_content", "medium", "surface", "lettering_style",
                 "finish", "condition", "era_estimate", "country_hint", "description"]
LIST_FIELDS   = ["decorative_technique", "colors", "tags"]

# Controlled fields we warn about when a value has never been used before.
# (tags is freeform, so we report new tags but do not fuss over them.)
CONTROLLED_SINGLE = ["medium", "surface", "lettering_style", "finish",
                     "condition", "era_estimate", "country_hint"]
CONTROLLED_LIST   = ["decorative_technique", "colors"]


def norm(name):
    """Original filename, path stripped and lowercased, for matching."""
    return os.path.basename(str(name)).strip().lower()


def build_vocab(images):
    vocab = {f: set() for f in CONTROLLED_SINGLE + CONTROLLED_LIST}
    seen_tags = set()
    for img in images.values():
        for f in CONTROLLED_SINGLE:
            v = img.get(f)
            if v: vocab[f].add(v)
        for f in CONTROLLED_LIST:
            for v in img.get(f, []) or []:
                vocab[f].add(v)
        for t in img.get("tags", []) or []:
            seen_tags.add(t)
    return vocab, seen_tags


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 merge_tags.py <tagsfile.json>")
        sys.exit(1)
    tags_path = sys.argv[1]

    with open(SIGNS) as f:
        data = json.load(f)
    images = data["images"]

    with open(tags_path) as f:
        entries = json.load(f)
    if not isinstance(entries, list):
        print("Error: the tags file must be a JSON list [ ... ].")
        sys.exit(1)

    # Index uploaded records by their original filename.
    index = {}
    for img in images.values():
        src = img.get("source_filename")
        if src:
            index[norm(src)] = img

    vocab, seen_tags = build_vocab(images)

    matched, notfound = 0, []
    new_values = {f: {} for f in CONTROLLED_SINGLE + CONTROLLED_LIST}
    new_tags = {}

    for entry in entries:
        key = entry.get("filename") or entry.get("source_filename")
        if not key:
            notfound.append("(entry with no filename)")
            continue
        img = index.get(norm(key))
        if img is None:
            notfound.append(key)
            continue

        for f in SINGLE_FIELDS:
            if f in entry and entry[f] is not None:
                img[f] = entry[f]
                if f in CONTROLLED_SINGLE and entry[f] and entry[f] not in vocab[f]:
                    new_values[f][entry[f]] = new_values[f].get(entry[f], 0) + 1
        for f in LIST_FIELDS:
            if f in entry and entry[f] is not None:
                vals = list(entry[f])
                img[f] = vals
                if f in CONTROLLED_LIST:
                    for v in vals:
                        if v not in vocab[f]:
                            new_values[f][v] = new_values[f].get(v, 0) + 1
                if f == "tags":
                    for t in vals:
                        if t not in seen_tags:
                            new_tags[t] = new_tags.get(t, 0) + 1
        matched += 1

    # Save (backup first).
    shutil.copy(SIGNS, SIGNS + ".bak")
    data["generated"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"
    with open(SIGNS, "w") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    # Report.
    print(f"\nMerged tags into {SIGNS} (backup at {SIGNS}.bak)\n")
    print(f"  matched and updated: {matched}")
    print(f"  not found in gallery: {len(notfound)}")
    if notfound:
        print("    (upload these through upload.html first, then re-run)")
        for n in notfound[:20]:
            print(f"      - {n}")
        if len(notfound) > 20:
            print(f"      ... and {len(notfound) - 20} more")

    flagged = any(new_values[f] for f in new_values)
    if flagged:
        print("\n  values outside the current vocabulary (kept, review when you like):")
        for f in CONTROLLED_SINGLE + CONTROLLED_LIST:
            if new_values[f]:
                items = ", ".join(f"{v} ({n})" for v, n in sorted(new_values[f].items()))
                print(f"    {f}: {items}")
    if new_tags:
        tops = sorted(new_tags.items(), key=lambda x: -x[1])
        shown = ", ".join(f"{t} ({n})" for t, n in tops[:30])
        print(f"\n  new freeform tags ({len(new_tags)}): {shown}")

    print("\nDone. Commit and push signs.json to update the live gallery.")


if __name__ == "__main__":
    main()
