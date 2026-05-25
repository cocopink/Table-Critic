import pytest
from unittest.mock import patch, MagicMock
from refine.TableQA.utils.verifier import (
    verify_chain,
    VerificationReport,
    StepVerification,
    Verdict,
    _extract_question_keywords,
    _parse_selected_rows,
    _parse_sort_column,
    _parse_group_column,
    _safe_float,
    _verify_select_row,
    _verify_select_column,
    _verify_sort_column,
    _verify_group_column,
    _verify_add_column,
    _verify_simple_query,
    _compute_verdict,
)


def _make_table(headers, rows):
    return [headers] + rows


def _make_op(op_name, param):
    return {"operation_name": op_name, "parameter_and_conf": [(param, 0.9)], "thought": "reasoning..."}


def _make_table_info(table):
    return {"table_text": table, "act_chain": []}


def _make_table_log_for_chain(table, chain):
    """Build a fake table_log that mimics get_table_log output."""
    log = [_make_table_info(table)]
    for i, op in enumerate(chain):
        # Each step just passes table through unchanged
        post = _make_table_info(table)
        post["act_chain"] = [f"f_{op['operation_name']}(fake_action)"]
        log.append(post)
    return log, []


def _make_sample(table, question, chain):
    return {"table_text": table, "statement": question, "chain": chain}


# --- Helper Functions ---


class TestHelperFunctions:
    def test_parse_selected_rows(self):
        assert _parse_selected_rows("f_select_row([row 3, row 5])") == ["3", "5"]
        assert _parse_selected_rows("f_select_row([*])") == []
        assert _parse_selected_rows("f_select_row([row 1])") == ["1"]
        assert _parse_selected_rows("garbage") == []

    def test_parse_sort_column(self):
        assert _parse_sort_column("f_sort_column(points)") == "points"
        assert _parse_sort_column("garbage") is None

    def test_parse_group_column(self):
        assert _parse_group_column("f_group_column(party)") == "party"
        assert _parse_group_column("garbage") is None

    def test_safe_float(self):
        assert _safe_float("42.5") == 42.5
        assert _safe_float("-3") == -3.0
        assert _safe_float("N/A") is None
        assert _safe_float("") is None
        assert _safe_float("heat 3") == 3.0

    def test_extract_question_keywords(self):
        kw = _extract_question_keywords("What is the average score of students in France?")
        assert "average" in kw
        assert "score" in kw
        assert "students" in kw
        assert "france" in kw
        assert "what" not in kw
        assert "is" not in kw
        assert "the" not in kw


# --- Per-Operation Verifiers (direct call, no get_table_log) ---


class TestSelectRowVerifier:
    @patch("refine.TableQA.utils.verifier._parse_selected_rows")
    def test_valid_selection(self, mock_parse):
        mock_parse.return_value = ["1", "2"]
        table = _make_table(["name", "score"], [["Alice", "90"], ["Bob", "85"]])
        sv = _verify_select_row(
            step_num=1, action_str="f_select_row([row 1, row 2])",
            operation=None, pre_table=table, post_table=table,
            post_info={}, question="What is Alice's score?", original_table=table,
        )
        assert sv.verdict == Verdict.PASS

    @patch("refine.TableQA.utils.verifier._parse_selected_rows")
    def test_out_of_bounds(self, mock_parse):
        mock_parse.return_value = ["1", "99"]
        table = _make_table(["name", "score"], [["Alice", "90"], ["Bob", "85"]])
        sv = _verify_select_row(
            step_num=1, action_str="f_select_row([row 1, row 99])",
            operation=None, pre_table=table, post_table=table,
            post_info={}, question="Who scored 90?", original_table=table,
        )
        assert sv.verdict == Verdict.FAIL
        bounds_check = [c for c in sv.checks if c["name"] == "row_bounds"]
        assert not bounds_check[0]["passed"]

    @patch("refine.TableQA.utils.verifier._parse_selected_rows")
    def test_keyword_relevance_pass(self, mock_parse):
        mock_parse.return_value = ["1", "2"]
        table = _make_table(["player", "points"], [["France", "90"], ["France", "85"]])
        sv = _verify_select_row(
            step_num=1, action_str="f_select_row([row 1, row 2])",
            operation=None, pre_table=table, post_table=table,
            post_info={}, question="How many points does France have?", original_table=table,
        )
        kw_check = [c for c in sv.checks if c["name"] == "keyword_relevance"]
        assert kw_check[0]["passed"]

    @patch("refine.TableQA.utils.verifier._parse_selected_rows")
    def test_keyword_relevance_fail(self, mock_parse):
        mock_parse.return_value = ["2"]
        table = _make_table(["player", "points"], [["France", "90"], ["Germany", "85"]])
        sv = _verify_select_row(
            step_num=1, action_str="f_select_row([row 2])",
            operation=None, pre_table=table, post_table=table,
            post_info={}, question="What is France's score?", original_table=table,
        )
        kw_check = [c for c in sv.checks if c["name"] == "keyword_relevance"]
        assert not kw_check[0]["passed"]

    def test_empty_table(self):
        table = _make_table(["name"], [])
        sv = _verify_select_row(
            step_num=1, action_str="f_select_row([row 1])",
            operation=None, pre_table=table, post_table=table,
            post_info={}, question="Who is there?", original_table=table,
        )
        # Empty table: no data rows, selected rows out of bounds
        assert sv.verdict == Verdict.FAIL


class TestSelectColumnVerifier:
    def test_valid_selection(self):
        pre = _make_table(["name", "age", "city"], [["Alice", "25", "Paris"]])
        post = _make_table(["name", "city"], [["Alice", "Paris"]])
        sv = _verify_select_column(
            step_num=1, action_str="f_select_column([name, city])",
            operation=None, pre_table=pre, post_table=post,
            post_info={}, question="What cities?", original_table=pre,
        )
        assert sv.verdict == Verdict.PASS

    def test_dropped_relevant_column(self):
        pre = _make_table(["name", "age", "score"], [["Alice", "25", "90"]])
        post = _make_table(["name", "age"], [["Alice", "25"]])
        sv = _verify_select_column(
            step_num=1, action_str="f_select_column([name, age])",
            operation=None, pre_table=pre, post_table=post,
            post_info={}, question="What is the score?", original_table=pre,
        )
        # relevant_columns_retained is non-critical, so verdict is WARN not FAIL
        assert sv.verdict == Verdict.WARN
        rel_check = [c for c in sv.checks if c["name"] == "relevant_columns_retained"]
        assert not rel_check[0]["passed"]


class TestSortColumnVerifier:
    def test_headers_preserved_after_sort(self):
        table = _make_table(["name", "score"], [["Bob", "85"], ["Alice", "90"]])
        sorted_table = _make_table(["name", "score"], [["Alice", "90"], ["Bob", "85"]])
        sv = _verify_sort_column(
            step_num=1, action_str="f_sort_column(score)",
            operation=None, pre_table=table, post_table=sorted_table,
            post_info={}, question="Who scored highest?", original_table=table,
        )
        headers_check = [c for c in sv.checks if c["name"] == "headers_preserved"]
        assert headers_check[0]["passed"]

    def test_row_count_preserved(self):
        table = _make_table(["name", "score"], [["Bob", "85"], ["Alice", "90"]])
        sorted_table = _make_table(["name", "score"], [["Alice", "90"], ["Bob", "85"]])
        sv = _verify_sort_column(
            step_num=1, action_str="f_sort_column(score)",
            operation=None, pre_table=table, post_table=sorted_table,
            post_info={}, question="Who scored highest?", original_table=table,
        )
        row_check = [c for c in sv.checks if c["name"] == "row_count_preserved"]
        assert row_check[0]["passed"]

    def test_unknown_sort_column(self):
        table = _make_table(["name", "score"], [["Bob", "85"], ["Alice", "90"]])
        sv = _verify_sort_column(
            step_num=1, action_str="f_sort_column(nonexistent)",
            operation=None, pre_table=table, post_table=table,
            post_info={}, question="Who scored highest?", original_table=table,
        )
        col_check = [c for c in sv.checks if c["name"] == "sort_column_exists"]
        assert not col_check[0]["passed"]


class TestGroupColumnVerifier:
    def test_valid_group(self):
        table = _make_table(["city", "score"], [["Paris", "90"], ["Paris", "85"], ["London", "92"]])
        post_info = {"group_sub_table": ("city", [("Paris", 2), ("London", 1)])}
        sv = _verify_group_column(
            step_num=1, action_str="f_group_column(city)",
            operation=None, pre_table=table, post_table=table,
            post_info=post_info, question="What is the average score per city?", original_table=table,
        )
        assert len(sv.checks) >= 2
        table_check = [c for c in sv.checks if c["name"] == "table_unchanged"]
        assert table_check[0]["passed"]

    def test_nonexistent_column(self):
        table = _make_table(["city", "score"], [["Paris", "90"]])
        sv = _verify_group_column(
            step_num=1, action_str="f_group_column(country)",
            operation=None, pre_table=table, post_table=table,
            post_info={}, question="What is the average score per city?", original_table=table,
        )
        col_check = [c for c in sv.checks if c["name"] == "column_exists"]
        assert not col_check[0]["passed"]


class TestAddColumnVerifier:
    def test_row_count_preserved(self):
        pre = _make_table(["name", "age"], [["Alice", "25"], ["Bob", "30"]])
        post = _make_table(["name", "age", "full_name"], [["Alice", "25", "Alice Smith"], ["Bob", "30", "Bob Johnson"]])
        sv = _verify_add_column(
            step_num=1, action_str="f_add_column(full_name)",
            operation=None, pre_table=pre, post_table=post,
            post_info={}, question="What are the full names?", original_table=pre,
        )
        row_check = [c for c in sv.checks if c["name"] == "row_count_preserved"]
        assert row_check[0]["passed"]

    def test_values_not_identical(self):
        pre = _make_table(["name", "age"], [["Alice", "25"], ["Bob", "30"]])
        post = _make_table(["name", "age", "full_name"], [["Alice", "25", "Alice Smith"], ["Bob", "30", "Bob Johnson"]])
        sv = _verify_add_column(
            step_num=1, action_str="f_add_column(full_name)",
            operation=None, pre_table=pre, post_table=post,
            post_info={}, question="What are the full names?", original_table=pre,
        )
        val_check = [c for c in sv.checks if c["name"] == "values_not_identical"]
        assert val_check[0]["passed"]

    def test_no_new_column(self):
        pre = _make_table(["name", "age"], [["Alice", "25"]])
        sv = _verify_add_column(
            step_num=1, action_str="f_add_column(?)",
            operation=None, pre_table=pre, post_table=pre,
            post_info={}, question="?", original_table=pre,
        )
        unique_check = [c for c in sv.checks if c["name"] == "unique_column_name"]
        assert not unique_check[0]["passed"]


class TestSimpleQueryVerifier:
    def test_non_empty_answer(self):
        table = _make_table(["name", "score"], [["Alice", "90"]])
        op = _make_op("simple_query", "90")
        sv = _verify_simple_query(
            step_num=1, action_str="90",
            operation=op, pre_table=table, post_table=table,
            post_info={}, question="What is the score?", original_table=table,
        )
        assert sv.verdict == Verdict.SKIP

    def test_answer_in_table(self):
        table = _make_table(["name", "score"], [["Alice", "90"]])
        op = _make_op("simple_query", "90")
        sv = _verify_simple_query(
            step_num=1, action_str="90",
            operation=op, pre_table=table, post_table=table,
            post_info={}, question="What is the score?", original_table=table,
        )
        in_table_check = [c for c in sv.checks if c["name"] == "answer_in_table"]
        assert in_table_check[0]["passed"]

    def test_answer_not_in_table(self):
        table = _make_table(["name", "score"], [["Alice", "90"]])
        op = _make_op("simple_query", "Paris")
        sv = _verify_simple_query(
            step_num=1, action_str="Paris",
            operation=op, pre_table=table, post_table=table,
            post_info={}, question="What is the score?", original_table=table,
        )
        in_table_check = [c for c in sv.checks if c["name"] == "answer_in_table"]
        assert not in_table_check[0]["passed"]

    def test_multi_value_answer(self):
        table = _make_table(["name", "score"], [["Alice", "90"], ["Bob", "85"]])
        op = _make_op("simple_query", "90|85")
        sv = _verify_simple_query(
            step_num=1, action_str="90|85",
            operation=op, pre_table=table, post_table=table,
            post_info={}, question="What are the scores?", original_table=table,
        )
        in_table_check = [c for c in sv.checks if c["name"] == "answer_in_table"]
        assert in_table_check[0]["passed"]


class TestVerificationReport:
    def test_empty_chain(self):
        sample = {"chain": [], "table_text": [["a"]], "statement": "q"}
        report = verify_chain(sample)
        assert report.total_steps == 0
        assert not report.has_failures
        assert report.first_fail_step is None

    def test_no_failures(self):
        table = _make_table(["name", "age"], [["Alice", "25"]])
        chain = [_make_op("select_column", "['name', 'age']")]
        sample = _make_sample(table, "How old is Alice?", chain)
        report = verify_chain(sample)
        assert not report.has_failures

    def test_to_critic_prompt(self):
        table = _make_table(["name", "score"], [["Alice", "90"]])
        chain = [_make_op("select_column", "['name', 'score']")]
        sample = _make_sample(table, "Who scored 90?", chain)
        report = verify_chain(sample)
        prompt = report.to_critic_prompt()
        assert "Automated Step Verification Results" in prompt
        assert "Step 1" in prompt
        assert "OK" in prompt

    def test_to_critic_step_prompt(self):
        table = _make_table(["name", "score"], [["Alice", "90"]])
        chain = [_make_op("select_column", "['name']")]
        sample = _make_sample(table, "Who?", chain)
        report = verify_chain(sample)
        prompt = report.to_critic_step_prompt(1)
        assert "Step 1" in prompt

    def test_to_critic_prompt_with_failure(self):
        report = VerificationReport(
            steps=[
                StepVerification(step_num=1, operation_name="select_column",
                                 action_str="f_select_column([name, age])",
                                 verdict=Verdict.FAIL,
                                 checks=[{"name": "test", "passed": False, "detail": "failed"}],
                                 summary="failed"),
            ],
            failed_steps=[1],
        )
        prompt = report.to_critic_prompt()
        assert "potential issues at steps: [1]" in prompt

    def test_to_critic_prompt_all_pass(self):
        table = _make_table(["name", "age"], [["Alice", "25"]])
        chain = [_make_op("select_column", "['name', 'age']")]
        sample = _make_sample(table, "How old is Alice?", chain)
        report = verify_chain(sample)
        prompt = report.to_critic_prompt()
        assert "All verifiable steps passed" in prompt


class TestVerifyChain:
    def test_sample_without_chain(self):
        report = verify_chain({"table_text": [["a"]], "statement": "q"})
        assert report.total_steps == 0

    def test_chain_with_skip(self):
        table = _make_table(["name", "age"], [["Alice", "25"]])
        chain = [
            {"operation_name": "select_column", "parameter_and_conf": [("['nonexistent']", 0.9)], "thought": "skip reason..."},
        ]
        sample = _make_sample(table, "How old?", chain)
        report = verify_chain(sample)
        assert report.total_steps >= 0

    def test_compute_verdict_pass(self):
        checks = [{"name": "a", "passed": True}, {"name": "b", "passed": True}]
        assert _compute_verdict(checks) == Verdict.PASS

    def test_compute_verdict_fail_critical(self):
        checks = [{"name": "row_bounds", "passed": False}, {"name": "b", "passed": True}]
        assert _compute_verdict(checks) == Verdict.FAIL

    def test_compute_verdict_fail_non_critical(self):
        checks = [{"name": "meaningful_selection", "passed": False}]
        assert _compute_verdict(checks) == Verdict.WARN

    def test_compute_verdict_skip_on_empty(self):
        assert _compute_verdict([]) == Verdict.PASS
