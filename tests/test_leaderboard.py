"""Tests for core.leaderboard.LeaderboardManager."""
import json
import os
import pytest

from core.leaderboard import LeaderboardManager


@pytest.fixture
def lb(tmp_path, monkeypatch):
    """Create a LeaderboardManager that stores its file inside tmp_path."""
    file_path = str(tmp_path / "leaderboard.json")
    # Patch the file path attribute after construction
    mgr = LeaderboardManager.__new__(LeaderboardManager)
    mgr.max_entries = 10
    mgr.leaderboard_file = file_path
    mgr.entries = []
    mgr.load_leaderboard()
    return mgr


@pytest.fixture
def empty_lb(tmp_path):
    """A leaderboard that starts completely empty (no defaults)."""
    file_path = str(tmp_path / "leaderboard.json")
    mgr = LeaderboardManager.__new__(LeaderboardManager)
    mgr.max_entries = 10
    mgr.leaderboard_file = file_path
    mgr.entries = []
    # Write an empty entries file so load_leaderboard won't create defaults
    with open(file_path, "w") as f:
        json.dump({"entries": []}, f)
    mgr.load_leaderboard()
    return mgr


# ---------------------------------------------------------------------------
# Loading / saving
# ---------------------------------------------------------------------------

class TestLeaderboardPersistence:
    def test_default_entries_on_first_load(self, lb):
        """First load should produce default entries."""
        assert len(lb.entries) > 0

    def test_save_and_reload(self, tmp_path):
        file_path = str(tmp_path / "lb.json")
        mgr = LeaderboardManager.__new__(LeaderboardManager)
        mgr.max_entries = 10
        mgr.leaderboard_file = file_path
        mgr.entries = []
        # Write empty to avoid defaults
        with open(file_path, "w") as f:
            json.dump({"entries": []}, f)
        mgr.load_leaderboard()

        mgr.add_score("TestPlayer", 999, "TestChallenge")

        # Create a fresh manager pointing at the same file
        mgr2 = LeaderboardManager.__new__(LeaderboardManager)
        mgr2.max_entries = 10
        mgr2.leaderboard_file = file_path
        mgr2.entries = []
        mgr2.load_leaderboard()

        assert len(mgr2.entries) == 1
        assert mgr2.entries[0]["name"] == "TestPlayer"
        assert mgr2.entries[0]["score"] == 999

    def test_corrupt_file_graceful(self, tmp_path):
        file_path = str(tmp_path / "corrupt.json")
        with open(file_path, "w") as f:
            f.write("NOT VALID JSON!!!")

        mgr = LeaderboardManager.__new__(LeaderboardManager)
        mgr.max_entries = 10
        mgr.leaderboard_file = file_path
        mgr.entries = []
        mgr.load_leaderboard()
        # Should recover gracefully with empty entries
        assert mgr.entries == []


# ---------------------------------------------------------------------------
# Adding scores
# ---------------------------------------------------------------------------

class TestAddScore:
    def test_add_score_returns_position(self, empty_lb):
        made_it, pos = empty_lb.add_score("Alice", 500)
        assert made_it is True
        assert pos == 0  # first entry

    def test_scores_sorted_descending(self, empty_lb):
        empty_lb.add_score("Low", 100)
        empty_lb.add_score("High", 900)
        empty_lb.add_score("Mid", 500)
        scores = [e["score"] for e in empty_lb.entries]
        assert scores == sorted(scores, reverse=True)

    def test_max_entries_enforced(self, tmp_path):
        file_path = str(tmp_path / "small.json")
        mgr = LeaderboardManager.__new__(LeaderboardManager)
        mgr.max_entries = 3
        mgr.leaderboard_file = file_path
        mgr.entries = []
        with open(file_path, "w") as f:
            json.dump({"entries": []}, f)
        mgr.load_leaderboard()

        for i in range(5):
            mgr.add_score(f"Player{i}", (i + 1) * 100)
        assert len(mgr.entries) == 3
        # Only the top 3 scores should remain
        assert mgr.entries[0]["score"] == 500
        assert mgr.entries[-1]["score"] == 300

    def test_name_truncated(self, empty_lb):
        long_name = "A" * 50
        empty_lb.add_score(long_name, 100)
        assert len(empty_lb.entries[0]["name"]) == 20

    def test_low_score_rejected_when_full(self, tmp_path):
        file_path = str(tmp_path / "full.json")
        mgr = LeaderboardManager.__new__(LeaderboardManager)
        mgr.max_entries = 2
        mgr.leaderboard_file = file_path
        mgr.entries = []
        with open(file_path, "w") as f:
            json.dump({"entries": []}, f)
        mgr.load_leaderboard()

        mgr.add_score("A", 500)
        mgr.add_score("B", 400)
        made_it, pos = mgr.add_score("C", 100)
        assert made_it is False
        assert pos == -1
        assert len(mgr.entries) == 2


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

class TestLeaderboardQueries:
    def test_check_if_high_score(self, empty_lb):
        empty_lb.add_score("A", 500)
        assert empty_lb.check_if_high_score(600) is True
        # With space remaining, any score qualifies
        assert empty_lb.check_if_high_score(1) is True

    def test_check_if_high_score_full(self, tmp_path):
        file_path = str(tmp_path / "full.json")
        mgr = LeaderboardManager.__new__(LeaderboardManager)
        mgr.max_entries = 1
        mgr.leaderboard_file = file_path
        mgr.entries = []
        with open(file_path, "w") as f:
            json.dump({"entries": []}, f)
        mgr.load_leaderboard()
        mgr.add_score("A", 500)

        assert mgr.check_if_high_score(600) is True
        assert mgr.check_if_high_score(400) is False

    def test_get_top_entries(self, empty_lb):
        for i in range(5):
            empty_lb.add_score(f"P{i}", (i + 1) * 100)
        top3 = empty_lb.get_top_entries(3)
        assert len(top3) == 3
        assert top3[0]["score"] == 500

    def test_get_rank_for_score(self, empty_lb):
        empty_lb.add_score("A", 500)
        empty_lb.add_score("B", 300)
        assert empty_lb.get_rank_for_score(600) == 1
        assert empty_lb.get_rank_for_score(400) == 2
        assert empty_lb.get_rank_for_score(100) == 3

    def test_get_entries_for_map(self, empty_lb):
        empty_lb.add_score("A", 500, field_config="Maze")
        empty_lb.add_score("B", 400, field_config="Treasure")
        maze_entries = empty_lb.get_entries_for_map("Maze")
        assert len(maze_entries) == 1
        assert maze_entries[0]["name"] == "A"

    def test_get_top_score_per_map(self, empty_lb):
        empty_lb.add_score("A", 500, field_config="Maze")
        empty_lb.add_score("B", 800, field_config="Maze")
        empty_lb.add_score("C", 300, field_config="Treasure")
        result = empty_lb.get_top_score_per_map()
        assert result["Maze"] == 800
        assert result["Treasure"] == 300

    def test_clear_leaderboard(self, empty_lb):
        empty_lb.add_score("A", 500)
        empty_lb.clear_leaderboard()
        assert empty_lb.entries == []


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

class TestLeaderboardStats:
    def test_stats_empty(self, empty_lb):
        stats = empty_lb.get_stats()
        assert stats["total_entries"] == 0
        assert stats["highest_score"] == 0

    def test_stats_with_entries(self, empty_lb):
        empty_lb.add_score("A", 500, challenge="Basic MZ")
        empty_lb.add_score("B", 300, challenge="Basic MZ")
        empty_lb.add_score("C", 100, challenge="Advanced")
        stats = empty_lb.get_stats()
        assert stats["total_entries"] == 3
        assert stats["highest_score"] == 500
        assert stats["average_score"] == 300
        assert stats["most_common_challenge"] == "Basic MZ"
