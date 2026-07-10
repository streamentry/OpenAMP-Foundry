"""Tests for J1 changelog generator from PR titles."""

from __future__ import annotations

import pytest

from openamp_foundry.changelog.changelog_entry import (
    KNOWN_ENTRY_TYPES,
    KNOWN_PHASES,
    UNKNOWN_SCOPE,
    UNKNOWN_TYPE,
    Changelog,
    ChangelogEntry,
    build_changelog,
    build_changelog_entry,
    format_changelog,
    group_entries_by_type,
    parse_pr_title,
)


def _make_entry(**kwargs) -> ChangelogEntry:
    defaults = dict(
        pr_number=1,
        pr_title="feat: Phase E E1 external review packet schema",
        commit_sha="abc1234def5678",
        merge_date="2026-01-01T00:00:00Z",
        entry_type="feat",
        scope="Phase E",
        description="Phase E E1 external review packet schema",
    )
    defaults.update(kwargs)
    return ChangelogEntry(**defaults)


class TestConstants:
    def test_known_types_is_frozenset(self):
        assert isinstance(KNOWN_ENTRY_TYPES, frozenset)

    def test_feat_in_known_types(self):
        assert "feat" in KNOWN_ENTRY_TYPES

    def test_fix_in_known_types(self):
        assert "fix" in KNOWN_ENTRY_TYPES

    def test_docs_in_known_types(self):
        assert "docs" in KNOWN_ENTRY_TYPES

    def test_test_in_known_types(self):
        assert "test" in KNOWN_ENTRY_TYPES

    def test_unknown_type_constant(self):
        assert UNKNOWN_TYPE == "other"

    def test_unknown_scope_constant(self):
        assert UNKNOWN_SCOPE == "unknown"

    def test_known_phases_is_frozenset(self):
        assert isinstance(KNOWN_PHASES, frozenset)

    def test_phase_e_in_known_phases(self):
        assert "Phase E" in KNOWN_PHASES

    def test_phase_j_in_known_phases(self):
        assert "Phase J" in KNOWN_PHASES


class TestParsePRTitle:
    def test_feat_with_phase(self):
        t, s, d = parse_pr_title("feat: Phase E E1 description here")
        assert t == "feat"
        assert "Phase E" in s
        assert "description here" in d

    def test_fix_with_phase(self):
        t, s, d = parse_pr_title("fix: Phase B B3 baseline caveat bug")
        assert t == "fix"
        assert "Phase B" in s

    def test_docs_no_phase(self):
        t, s, d = parse_pr_title("docs: update README")
        assert t == "docs"
        assert s == UNKNOWN_SCOPE

    def test_unknown_type(self):
        t, s, d = parse_pr_title("release: some release note")
        assert t == UNKNOWN_TYPE

    def test_scoped_commit(self):
        t, s, d = parse_pr_title("feat(Phase B): add certificate field")
        assert t == "feat"
        assert s == "Phase B"
        assert "add certificate field" in d

    def test_empty_title(self):
        t, s, d = parse_pr_title("")
        assert t == UNKNOWN_TYPE
        assert s == UNKNOWN_SCOPE
        assert d == ""

    def test_whitespace_only_title(self):
        t, s, d = parse_pr_title("   ")
        assert t == UNKNOWN_TYPE

    def test_no_colon_no_phase(self):
        t, s, d = parse_pr_title("just a plain title")
        assert t == UNKNOWN_TYPE
        assert s == UNKNOWN_SCOPE
        assert d == "just a plain title"

    def test_no_colon_with_phase(self):
        t, s, d = parse_pr_title("Phase C benchmarking update")
        assert t == UNKNOWN_TYPE
        assert "Phase C" in s

    def test_feat_uppercase_type_normalised(self):
        t, s, d = parse_pr_title("FEAT: Phase D something")
        assert t == "feat"

    def test_chore_is_known(self):
        t, s, d = parse_pr_title("chore: cleanup stale branches")
        assert t == "chore"

    def test_refactor_is_known(self):
        t, s, d = parse_pr_title("refactor: Phase A code cleanup")
        assert t == "refactor"

    def test_description_stripped(self):
        t, s, d = parse_pr_title("feat:   Phase F F7 link schema   ")
        assert not d.startswith(" ")
        assert not d.endswith(" ")


class TestBuildChangelogEntry:
    def test_returns_entry(self):
        entry = build_changelog_entry(
            pr_number=898,
            pr_title="feat: Phase E E2 example packet",
            commit_sha="abc1234",
            merge_date="2026-07-10",
        )
        assert isinstance(entry, ChangelogEntry)

    def test_pr_number_stored(self):
        entry = build_changelog_entry(901, "fix: bug", "sha1", "2026-01-01")
        assert entry.pr_number == 901

    def test_title_stored(self):
        entry = build_changelog_entry(1, "docs: update README", "sha", "2026-01-01")
        assert entry.pr_title == "docs: update README"

    def test_commit_sha_stored(self):
        entry = build_changelog_entry(1, "feat: X", "deadbeef", "2026-01-01")
        assert entry.commit_sha == "deadbeef"

    def test_merge_date_stored(self):
        entry = build_changelog_entry(1, "feat: X", "sha", "2026-07-10T12:00:00Z")
        assert entry.merge_date == "2026-07-10T12:00:00Z"

    def test_entry_type_parsed(self):
        entry = build_changelog_entry(1, "feat: Phase E E1 schema", "sha", "2026")
        assert entry.entry_type == "feat"

    def test_scope_parsed(self):
        entry = build_changelog_entry(1, "feat: Phase E E1 schema", "sha", "2026")
        assert "Phase E" in entry.scope

    def test_description_parsed(self):
        entry = build_changelog_entry(1, "feat: Phase E E1 schema", "sha", "2026")
        assert len(entry.description) > 0

    def test_unknown_type_for_bad_title(self):
        entry = build_changelog_entry(1, "not conventional at all", "sha", "2026")
        assert entry.entry_type == UNKNOWN_TYPE

    def test_unknown_scope_for_no_phase(self):
        entry = build_changelog_entry(1, "docs: just docs", "sha", "2026")
        assert entry.scope == UNKNOWN_SCOPE


class TestGroupEntriesByType:
    def test_groups_by_type(self):
        entries = [
            _make_entry(entry_type="feat"),
            _make_entry(entry_type="fix"),
            _make_entry(entry_type="feat"),
        ]
        groups = group_entries_by_type(entries)
        assert len(groups["feat"]) == 2
        assert len(groups["fix"]) == 1

    def test_empty_list(self):
        groups = group_entries_by_type([])
        assert groups == {}

    def test_single_entry(self):
        entry = _make_entry(entry_type="docs")
        groups = group_entries_by_type([entry])
        assert "docs" in groups
        assert len(groups["docs"]) == 1

    def test_returns_dict(self):
        groups = group_entries_by_type([_make_entry()])
        assert isinstance(groups, dict)

    def test_all_same_type(self):
        entries = [_make_entry(entry_type="test") for _ in range(5)]
        groups = group_entries_by_type(entries)
        assert len(groups) == 1
        assert len(groups["test"]) == 5

    def test_unknown_type_grouped(self):
        entries = [_make_entry(entry_type=UNKNOWN_TYPE)]
        groups = group_entries_by_type(entries)
        assert UNKNOWN_TYPE in groups


class TestBuildAndFormatChangelog:
    def setup_method(self):
        self.entries = [
            build_changelog_entry(901, "feat: Phase F F7 link schema", "abc1234", "2026-07-10"),
            build_changelog_entry(898, "feat: Phase E E2 example packet", "def5678", "2026-07-10"),
            build_changelog_entry(895, "docs: update NEXT_100_PR_MAP", "ghi9012", "2026-07-09"),
        ]
        self.changelog = build_changelog(
            version="0.2.0",
            generated_at="2026-07-10T00:00:00Z",
            entries=self.entries,
        )
        self.formatted = format_changelog(self.changelog)

    def test_build_returns_changelog(self):
        assert isinstance(self.changelog, Changelog)

    def test_entry_count_matches(self):
        assert self.changelog.entry_count == 3

    def test_version_stored(self):
        assert self.changelog.version == "0.2.0"

    def test_generated_at_stored(self):
        assert self.changelog.generated_at == "2026-07-10T00:00:00Z"

    def test_entries_stored(self):
        assert len(self.changelog.entries) == 3

    def test_format_returns_string(self):
        assert isinstance(self.formatted, str)

    def test_format_contains_version(self):
        assert "0.2.0" in self.formatted

    def test_format_contains_pr_numbers(self):
        assert "#901" in self.formatted
        assert "#898" in self.formatted
        assert "#895" in self.formatted

    def test_format_contains_feat_section(self):
        assert "Feat" in self.formatted

    def test_format_contains_docs_section(self):
        assert "Docs" in self.formatted

    def test_format_contains_total_entries(self):
        assert "3" in self.formatted

    def test_empty_entries_changelog(self):
        empty = build_changelog("0.0.0", "2026-01-01", [])
        assert empty.entry_count == 0
        text = format_changelog(empty)
        assert "0.0.0" in text
