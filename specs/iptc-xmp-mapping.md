# IPTC/XMP Field Mapping

| Concept          | IPTC Core / XMP Property                         | Example                           |
|------------------|---------------------------------------------------|-----------------------------------|
| Author/Creator   | `Iptc4xmpCore:Creator`, `dc:creator`              | "Matthew Craig"                   |
| Copyright Notice | `dc:rights` / `xmpRights:Marked` / `photoshop:Copyright` | "© Matthew Craig 2025"     |
| Website/URL      | `Iptc4xmpExt:WebStatement`, `dcterms:identifier`  | "https://taggedz.me"              |
| License          | `xmpRights:UsageTerms`                            | "CC BY-NC 4.0"                    |
| Description      | `dc:description`                                  | "Short description…"              |
| Title            | `dc:title`                                        | "Piece Title"                     |

Notes:
- Write both IPTC Core and XMP Dublin Core where practical.
- Keep values short, ASCII-safe where possible for broader tool compatibility.
