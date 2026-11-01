# How to tag and add a new batch of photos

This is the cheap way to add photos without running `tagger.py` (which costs
API money). A Claude chat does the tagging instead, and a small script drops
those tags into the gallery.

Do these four steps for each new batch.

---

## Step 1: Tag the photos in a Claude chat

Start a chat and give it two things:

1. Your local photos for this batch.
2. The file `tag-vocabulary.txt` (the list of tags the gallery already uses).

Ask it:

> Tag these sign photos. Use the values in tag-vocabulary.txt where they fit.
> Return a single JSON file, a list with one object per photo, keyed by the
> photo's original filename, using exactly these fields: filename,
> text_content, medium, surface, lettering_style, decorative_technique,
> finish, condition, colors, era_estimate, country_hint, description, tags.

Save what it gives you as a `.json` file, for example `batch1.json`.

One object should look like this:

```json
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
```

`decorative_technique`, `colors`, and `tags` are lists (square brackets).
Everything else is plain text. `text_content` is the words on the sign, or
empty if none.

---

## Step 2: Upload the photos

Go to https://signreference.vercel.app/upload.html and upload the same photos.
You can skip the manual tagging there now, Step 3 handles tags.

The upload page quietly remembers each photo's original filename, which is how
the tags get matched back to the right image.

---

## Step 3: Merge the tags

Put your `.json` file (e.g. `batch1.json`) in the project folder, then run:

```bash
python3 merge_tags.py batch1.json
```

It will:

- fill in the tags for each matching photo,
- make a safety backup at `signs.json.bak`,
- print a short report.

The report tells you:

- **matched and updated**: how many photos got their tags.
- **not found in gallery**: photos it could not match. Usually means they were
  not uploaded yet. Upload them (Step 2), then run Step 3 again.
- **values outside the current vocabulary**: new values it has not seen before.
  These are kept, not rejected. Just glance at them in case any are typos.
- **new freeform tags**: brand new tags added this batch.

---

## Step 4: Publish to the live gallery

```bash
git add signs.json && git commit -m "Merge tags for new batch" && git push
```

The gallery updates about a minute later.

---

## Important order note

Do Step 3 (merge) **after** Step 2 (upload), not before. The merge matches
tags to photos that already exist in the gallery. If you run it too early, it
just lists the photos as "not found" and changes nothing, which is safe.

## If something looks wrong

The merge always backs up the old file first. To undo the last merge, replace
`signs.json` with `signs.json.bak`, or run `git checkout signs.json` before you
push.
