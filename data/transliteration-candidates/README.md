# Transliteration candidate inputs

This directory intentionally contains source descriptors only. Existing Kemenag Latin
and Tanzil English bytes are reused from their original snapshots; no duplicate corpus is
stored here. Tanzil Turkish is restricted and QUL resources are unknown or authenticated
manual exports, so no new third party transliteration bytes are committed.

`registry.json` records the source identity, scheme, granularity, markup policy, expected
coverage, and rights state for the requested candidates. QUL 72 and 468 are dedupe candidates,
not aliases: a complete official export and canonical comparison must prove identity before
either can be promoted. `quranjson.transliterations` validates a user supplied official export
before a future rights-cleared integration can publish it. The default build must continue to
withhold every candidate whose rights state is not `granted`.
