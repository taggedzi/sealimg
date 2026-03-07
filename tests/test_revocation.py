from sealimg.revocation import find_revoked, parse_revocation_lines


def test_parse_revocation_lines_and_lookup() -> None:
    entries = parse_revocation_lines(
        [
            "# comment",
            "",
            "abc123 2026-03-06 key compromise",
            "def456 2026-03-07",
        ]
    )
    assert len(entries) == 2
    assert entries[0].reason == "key compromise"
    assert find_revoked("abc123", entries) is not None
    assert find_revoked("missing", entries) is None
