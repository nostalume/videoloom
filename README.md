# Video Loom

Video Loom is a selective personal archive of video content collected from my own
interests. It is not a comprehensive collection or an official mirror of the
original sources.

Browse the generated [recording index](INDEX.md) for titles, uploaders, durations,
original sources, and readable transcripts.

## Adding a recording

Add or refresh a source in the shared pack, then update the index locally:

```powershell
vctx prepare <input> --out sources
python tools/build_index.py
```

The local index command makes the source and catalog change reviewable together
and is required for pull requests. On direct pushes to `main`, GitHub Actions
regenerates and commits `INDEX.md` automatically when needed. If branch rules
reject the bot commit, run the index command locally and commit `INDEX.md` with
the source update; this avoids granting the workflow a branch-protection bypass.

## Archive contents

The recording pack is generated with
[vctx](https://github.com/nostalume/vctx) and retains its manifest, source
metadata, transcript, chunks, and readable Markdown projections. Original audio
and video assets, along with the local processing cache, are intentionally
excluded from Git.

## Limitations

Transcripts are produced by automatic speech recognition and may contain errors.
Including a recording reflects personal interest only; it does not imply
endorsement or independent fact-checking of the video's claims.
