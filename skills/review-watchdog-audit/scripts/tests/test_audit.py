"""Tests for review-watchdog-audit scripts."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

# Ensure the scripts directory is importable
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from common import extract_job_name, safe_read_json, extract_jobs, save_jobs  # noqa: E402
from audit_cron_watch import (  # noqa: E402
    RunRecord,
    classify_job,
    score_watch_job,
    detect_duplicates,
    audit_state_file,
    apply_state_audit_to_findings,
    run_audit,
    JobFinding,
)
from patrol import _build_alert, _severity_meets_threshold  # noqa: E402


# ---------------------------------------------------------------------------
# common.py tests
# ---------------------------------------------------------------------------


class TestCommon:
    def test_extract_job_name_id(self):
        assert extract_job_name({"id": "my-job"}, 0) == "my-job"

    def test_extract_job_name_fallback(self):
        assert extract_job_name({}, 5) == "job-5"

    def test_extract_job_name_priority(self):
        """'id' takes precedence over 'name'."""
        assert extract_job_name({"id": "a", "name": "b"}, 0) == "a"

    def test_safe_read_json_missing(self, tmp_path):
        assert safe_read_json(tmp_path / "nope.json") is None

    def test_safe_read_json_valid(self, tmp_path):
        p = tmp_path / "ok.json"
        p.write_text('{"x": 1}')
        assert safe_read_json(p) == {"x": 1}

    def test_safe_read_json_corrupt(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{broken")
        assert safe_read_json(p) is None

    def test_extract_jobs_dict(self):
        payload = {"jobs": [{"id": "a"}]}
        jobs, schema = extract_jobs(payload)
        assert schema == "dict"
        assert len(jobs) == 1

    def test_extract_jobs_list(self):
        payload = [{"id": "a"}]
        jobs, schema = extract_jobs(payload)
        assert schema == "list"
        assert len(jobs) == 1

    def test_extract_jobs_invalid(self):
        with pytest.raises(ValueError):
            extract_jobs("bad")

    def test_save_jobs_roundtrip(self, tmp_path):
        p = tmp_path / "jobs.json"
        original = {"jobs": [{"id": "a"}], "meta": "keep"}
        save_jobs(p, original, [{"id": "a"}, {"id": "b"}], "dict")
        loaded = json.loads(p.read_text())
        assert loaded["meta"] == "keep"
        assert len(loaded["jobs"]) == 2


# ---------------------------------------------------------------------------
# score / classify tests
# ---------------------------------------------------------------------------


class TestScoring:
    def test_score_watch_job_positive(self):
        job = {"name": "review-group-pr-watch", "target": "github.com/org/repo"}
        assert score_watch_job(job) >= 2

    def test_score_watch_job_zero(self):
        job = {"name": "daily-backup", "target": "s3://bucket"}
        assert score_watch_job(job) == 0


class TestClassifyJob:
    def _make_records(self, statuses, error_types=None, tokens=None):
        records = []
        for i, s in enumerate(statuses):
            records.append(RunRecord(
                timestamp=f"2026-01-01T00:{i:02d}:00Z",
                status=s,
                error_type=(error_types[i] if error_types else None),
                token_usage=(tokens[i] if tokens else None),
            ))
        return records

    def test_p0_quota(self):
        """3+ quota/402 errors → P0."""
        records = self._make_records(
            ["fail"] * 4,
            error_types=["quota_402"] * 4,
        )
        f = classify_job({"name": "pr-watch"}, "pr-watch", 3, records)
        assert f.severity == "P0"
        assert any("402" in r for r in f.reasons)

    def test_p0_consecutive_streak(self):
        """5+ consecutive recent failures → P0."""
        records = self._make_records(
            ["success", "fail", "fail", "fail", "fail", "fail"],
            error_types=[None, "generic", "generic", "generic", "generic", "generic"],
        )
        f = classify_job({"name": "pr-watch"}, "pr-watch", 2, records)
        assert f.severity == "P0"
        assert f.consecutive_failures >= 5

    def test_p1_failures(self):
        """3+ generic failures (but not consecutive 5) → P1."""
        records = self._make_records(
            ["success", "fail", "success", "fail", "fail"],
            error_types=[None, "generic", None, "generic", "generic"],
        )
        f = classify_job({"name": "pr-watch"}, "pr-watch", 2, records)
        assert f.severity == "P1"

    def test_p2_healthy(self):
        """No issues → P2."""
        records = self._make_records(["success", "success"])
        f = classify_job({"name": "pr-watch"}, "pr-watch", 2, records)
        assert f.severity == "P2"

    def test_token_waste_p0(self):
        """Waste ratio > 50% → P0."""
        records = self._make_records(
            ["fail", "fail", "fail", "success"],
            error_types=["generic", "generic", "generic", None],
            tokens=[1000, 1000, 1000, 500],
        )
        f = classify_job({"name": "pr-watch"}, "pr-watch", 2, records)
        assert f.severity == "P0"
        assert f.wasted_tokens == 3000
        assert f.total_tokens == 3500
        assert f.waste_ratio is not None and f.waste_ratio > 0.5

    def test_no_backoff_warning(self):
        """Many failures with no backoff should warn."""
        now = datetime.now(timezone.utc)
        records = [
            RunRecord(
                timestamp=(now + timedelta(seconds=i * 60)).isoformat(),
                status="fail",
                error_type="generic",
            )
            for i in range(6)
        ]
        f = classify_job({"name": "pr-watch"}, "pr-watch", 2, records)
        assert f.has_backoff is False
        assert any("backoff" in r.lower() for r in f.reasons)


# ---------------------------------------------------------------------------
# duplicate detection tests
# ---------------------------------------------------------------------------


class TestDuplicateDetection:
    def test_overlap_detected(self):
        jobs = [
            {"id": "watch-a", "repo": "org/repo1"},
            {"id": "watch-b", "repo": "org/repo1"},
        ]
        findings = [
            JobFinding(name="watch-a", score=2, severity="P2"),
            JobFinding(name="watch-b", score=2, severity="P2"),
        ]
        pairs = detect_duplicates(jobs, findings)
        assert len(pairs) == 1
        dup = next(f for f in findings if f.name == "watch-b")
        assert dup.duplicate_of == "watch-a"
        assert dup.severity == "P1"  # boosted from P2

    def test_no_overlap(self):
        jobs = [
            {"id": "watch-a", "repo": "org/repo1"},
            {"id": "watch-b", "repo": "org/repo2"},
        ]
        findings = [
            JobFinding(name="watch-a", score=2, severity="P2"),
            JobFinding(name="watch-b", score=2, severity="P2"),
        ]
        pairs = detect_duplicates(jobs, findings)
        assert len(pairs) == 0


# ---------------------------------------------------------------------------
# state audit tests
# ---------------------------------------------------------------------------


class TestStateAudit:
    def test_stale_cursor(self, tmp_path):
        state_file = tmp_path / "state.json"
        old_date = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
        state_file.write_text(json.dumps({
            "cursor": "abc123",
            "lastUpdated": old_date,
        }))
        audit = audit_state_file(state_file)
        assert audit.is_stale is True
        assert len(audit.issues) >= 1

    def test_cursor_regression(self, tmp_path):
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({
            "cursor": "200",
            "cursorHistory": ["300", "200"],
        }))
        audit = audit_state_file(state_file)
        assert audit.cursor_regressed is True

    def test_duplicate_prs(self, tmp_path):
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({
            "processedPrs": [1, 2, 3, 2, 4, 3],
        }))
        audit = audit_state_file(state_file)
        assert len(audit.duplicate_prs) == 2

    def test_healthy_state(self, tmp_path):
        state_file = tmp_path / "state.json"
        recent = datetime.now(timezone.utc).isoformat()
        state_file.write_text(json.dumps({
            "cursor": "abc",
            "lastUpdated": recent,
        }))
        audit = audit_state_file(state_file)
        assert audit.is_stale is False
        assert audit.cursor_regressed is False
        assert len(audit.issues) == 0

    def test_apply_state_audit_p0(self, tmp_path):
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({
            "cursor": "200",
            "cursorHistory": ["300", "200"],
        }))
        audit = audit_state_file(state_file)
        findings = [JobFinding(name="pr-watch", score=2, severity="P2")]
        apply_state_audit_to_findings(audit, findings)
        assert findings[0].severity == "P0"


# ---------------------------------------------------------------------------
# patrol tests
# ---------------------------------------------------------------------------


class TestPatrol:
    def test_severity_meets_threshold(self):
        assert _severity_meets_threshold("P0", "P1") is True
        assert _severity_meets_threshold("P1", "P1") is True
        assert _severity_meets_threshold("P2", "P1") is False

    def test_build_alert_triggers(self):
        report = {
            "findings": [
                {"name": "job-a", "severity": "P0", "wasted_tokens": 5000, "reasons": ["bad"]},
                {"name": "job-b", "severity": "P2", "wasted_tokens": 0, "reasons": []},
            ]
        }
        alert = _build_alert(report, "P1")
        assert alert is not None
        assert alert["level"] == "P0"
        assert len(alert["findings"]) == 1

    def test_build_alert_none(self):
        report = {
            "findings": [
                {"name": "job-b", "severity": "P2", "wasted_tokens": 0, "reasons": []},
            ]
        }
        alert = _build_alert(report, "P1")
        assert alert is None


# ---------------------------------------------------------------------------
# stop_cleanup tests
# ---------------------------------------------------------------------------


class TestStopCleanup:
    def _setup_jobs(self, tmp_path, jobs_list):
        jobs_file = tmp_path / "jobs.json"
        jobs_file.write_text(json.dumps({"jobs": jobs_list}, ensure_ascii=False, indent=2))
        return jobs_file

    def _setup_report(self, tmp_path, findings):
        report_file = tmp_path / "report.json"
        report_file.write_text(json.dumps({"findings": findings}))
        return report_file

    def test_dry_run_no_changes(self, tmp_path):
        jobs_file = self._setup_jobs(tmp_path, [{"id": "pr-watch", "enabled": True}])
        report_file = self._setup_report(tmp_path, [{"name": "pr-watch", "severity": "P0"}])

        original = jobs_file.read_text()

        # Import and run with subprocess to test CLI
        import subprocess
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "stop_cleanup_watch.py"),
             "--report", str(report_file),
             "--jobs", str(jobs_file)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "Dry-run" in result.stdout
        assert jobs_file.read_text() == original  # no mutation

    def test_apply_disables_job(self, tmp_path):
        jobs_file = self._setup_jobs(tmp_path, [
            {"id": "pr-watch", "enabled": True},
            {"id": "healthy-job", "enabled": True},
        ])
        report_file = self._setup_report(tmp_path, [{"name": "pr-watch", "severity": "P0"}])

        import subprocess
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "stop_cleanup_watch.py"),
             "--report", str(report_file),
             "--jobs", str(jobs_file),
             "--apply", "--confirm", "STOP_AND_CLEANUP"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "disabled" in result.stdout

        data = json.loads(jobs_file.read_text())
        pr_job = next(j for j in data["jobs"] if j["id"] == "pr-watch")
        assert pr_job["enabled"] is False
        assert pr_job["disabledBy"] == "review-watchdog-audit"

        healthy = next(j for j in data["jobs"] if j["id"] == "healthy-job")
        assert healthy["enabled"] is True

        # backup should exist
        backups = list(tmp_path.glob("jobs.json.bak.*"))
        assert len(backups) == 1


# ---------------------------------------------------------------------------
# Integration test: full audit pipeline
# ---------------------------------------------------------------------------


class TestRunAudit:
    def test_full_pipeline(self, tmp_path):
        # setup jobs
        jobs_file = tmp_path / "jobs.json"
        jobs_file.write_text(json.dumps({
            "jobs": [
                {"id": "review-pr-watch", "repo": "org/repo1", "schedule": "*/10 * * * *", "enabled": True},
                {"id": "daily-backup", "target": "s3://bucket", "schedule": "0 2 * * *"},
            ]
        }))

        # setup runs with some failures
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        log_file = runs_dir / "run-001.jsonl"
        lines = []
        for i in range(6):
            lines.append(json.dumps({
                "timestamp": f"2026-01-01T00:{i:02d}:00Z",
                "status": "failed",
                "error": "402 payment required",
                "total_tokens": 500,
            }))
        lines.append(json.dumps({
            "timestamp": "2026-01-01T00:06:00Z",
            "status": "success",
            "total_tokens": 200,
        }))
        # include the job name somewhere so grep matches
        lines.append(json.dumps({"job": "review-pr-watch", "msg": "run complete"}))
        log_file.write_text("\n".join(lines))

        # state file
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"cursor": "abc", "lastUpdated": "2026-01-01T00:00:00Z"}))

        report = run_audit(
            jobs_path=jobs_file,
            runs_dir=runs_dir,
            state_path=state_file,
        )

        assert report["summary"]["watchJobsFound"] >= 1
        # review-pr-watch should be found with issues
        watch_finding = next((f for f in report["findings"] if f["name"] == "review-pr-watch"), None)
        assert watch_finding is not None
        assert watch_finding["severity"] in ("P0", "P1")
        assert watch_finding["wasted_tokens"] is not None and watch_finding["wasted_tokens"] > 0

        # daily-backup should not be in findings (score 0)
        backup_finding = next((f for f in report["findings"] if f["name"] == "daily-backup"), None)
        assert backup_finding is None
