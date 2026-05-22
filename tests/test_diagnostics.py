from oak_vision_lab.diagnostics import (
    DiagnosticCheck,
    are_all_checks_passing,
    check_package_import,
    check_python_version,
    format_doctor_report,
)


def test_check_python_version_returns_check_result() -> None:
    result = check_python_version(minimum_major=3, minimum_minor=8)

    assert result.name == "Python"
    assert result.ok
    assert "current:" in result.details


def test_check_package_import_returns_ok_for_standard_library_module() -> None:
    result = check_package_import(
        display_name="json",
        module_name="json",
        package_name="json",
    )

    assert result.name == "json"
    assert result.ok


def test_check_package_import_returns_failure_for_missing_module() -> None:
    result = check_package_import(
        display_name="Missing package",
        module_name="definitely_missing_oak_vision_lab_module",
    )

    assert result.name == "Missing package"
    assert not result.ok
    assert "import failed" in result.details


def test_are_all_checks_passing_returns_true_for_all_ok() -> None:
    checks = [
        DiagnosticCheck(name="A", ok=True, details="ok"),
        DiagnosticCheck(name="B", ok=True, details="ok"),
    ]

    assert are_all_checks_passing(checks)


def test_are_all_checks_passing_returns_false_for_failure() -> None:
    checks = [
        DiagnosticCheck(name="A", ok=True, details="ok"),
        DiagnosticCheck(name="B", ok=False, details="fail"),
    ]

    assert not are_all_checks_passing(checks)


def test_format_doctor_report_contains_checks() -> None:
    checks = [
        DiagnosticCheck(name="Python", ok=True, details="current: 3.12.0"),
        DiagnosticCheck(name="DepthAI", ok=True, details="version: 2.32.0.0"),
    ]

    report = format_doctor_report(checks)

    assert "oak-vision-lab environment doctor" in report
    assert "[OK] Python" in report
    assert "[OK] DepthAI" in report
    assert "environment looks ready" in report


def test_format_doctor_report_contains_failure_summary() -> None:
    checks = [
        DiagnosticCheck(name="DepthAI", ok=False, details="import failed"),
    ]

    report = format_doctor_report(checks)

    assert "[FAIL] DepthAI" in report
    assert "environment has problems" in report
