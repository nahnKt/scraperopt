from sync import decide_action, group_by_article, is_source_complete, plan_removals


def make_file(articleId, uploadHash="h", configHash="c", status="completed"):
    return {
        "file_id": "file-" + articleId + "-" + uploadHash,
        "status": status,
        "attributes": {"article_id": articleId, "upload_hash": uploadHash, "index_config_hash": configHash},
    }


def test_group_by_article_skips_files_without_article_id():
    files = [make_file("1"), make_file("2"), make_file("1", "h2"), {"file_id": "x", "status": "completed", "attributes": {}}]
    groups = group_by_article(files)
    assert sorted(groups) == ["1", "2"]
    assert len(groups["1"]) == 2


def test_group_by_article_empty():
    assert group_by_article([]) == {}


def test_decide_action_add_when_no_file():
    assert decide_action([], "h", "c") == "add"


def test_decide_action_skip_when_hashes_match():
    assert decide_action([make_file("1")], "h", "c") == "skip"


def test_decide_action_update_when_content_changes():
    assert decide_action([make_file("1")], "new", "c") == "update"


def test_decide_action_update_when_chunking_config_changes():
    assert decide_action([make_file("1")], "h", "new") == "update"


def test_decide_action_update_when_old_file_failed():
    assert decide_action([make_file("1", status="failed")], "h", "c") == "update"


def test_decide_action_skip_if_any_duplicate_matches():
    assert decide_action([make_file("1", "old"), make_file("1", "h")], "h", "c") == "skip"


def test_source_complete():
    articles = [{"id": 1}, {"id": 2}, {"id": 3}]
    assert is_source_complete(articles, 3)
    assert not is_source_complete(articles, 4)
    assert not is_source_complete(articles + [{"id": 3}], 4)


def test_plan_removals_removes_deleted_article():
    groups = group_by_article([make_file("1"), make_file("2")])
    assert plan_removals(groups, {"1"}, True) == (["2"], "")


def test_plan_removals_blocked_when_fetch_incomplete():
    groups = group_by_article([make_file("1"), make_file("2")])
    assert plan_removals(groups, {"1"}, False) == ([], "source fetch incomplete")


def test_plan_removals_nothing_missing():
    groups = group_by_article([make_file("1"), make_file("2")])
    assert plan_removals(groups, {"1", "2", "3"}, True) == ([], "")
