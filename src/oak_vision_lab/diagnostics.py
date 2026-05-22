"""Environment diagnostics for oak-vision-lab."""

from __future__ import annotations

import importlib
import platform
import sys
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version


@dataclass(frozen=True)
class DiagnosticCheck:
    """Single diagnostic check result."""

    name: str
    ok: bool
    details: str


def check_python_version(
    *,
    minimum_major: int = 3,
    minimum_minor: int = 12,
) -> DiagnosticCheck:
    """Check whether the current Python version is supported."""

    current_version = sys.version_info
    current = f"{current_version.major}.{current_version.minor}.{current_version.micro}"
    required = f"{minimum_major}.{minimum_minor}+"

    is_supported = (current_version.major, current_version.minor) >= (
        minimum_major,
        minimum_minor,
    )

    details = f"current: {current}, required: {required}"

    return DiagnosticCheck(
        name="Python",
        ok=is_supported,
        details=details,
    )


def check_package_import(
    *,
    display_name: str,
    module_name: str,
    package_name: str | None = None,
) -> DiagnosticCheck:
    """Check whether a package can be imported and report its installed version."""

    metadata_name = package_name or module_name

    try:
        importlib.import_module(module_name)
    except ImportError as error:
        return DiagnosticCheck(
            name=display_name,
            ok=False,
            details=f"import failed: {error}",
        )

    try:
        installed_version = version(metadata_name)
    except PackageNotFoundError:
        installed_version = "unknown"

    return DiagnosticCheck(
        name=display_name,
        ok=True,
        details=f"version: {installed_version}",
    )


def run_doctor_checks() -> list[DiagnosticCheck]:
    """Run software environment diagnostics."""

    return [
        check_python_version(),
        check_package_import(
            display_name="DepthAI",
            module_name="depthai",
            package_name="depthai",
        ),
        check_package_import(
            display_name="OpenCV",
            module_name="cv2",
            package_name="opencv-python",
        ),
        check_package_import(
            display_name="NumPy",
            module_name="numpy",
            package_name="numpy",
        ),
        check_package_import(
            display_name="pytest",
            module_name="pytest",
            package_name="pytest",
        ),
        check_package_import(
            display_name="Ruff",
            module_name="ruff",
            package_name="ruff",
        ),
    ]


def are_all_checks_passing(checks: list[DiagnosticCheck]) -> bool:
    """Return True when all diagnostic checks are passing."""

    return all(check.ok for check in checks)


def format_doctor_report(checks: list[DiagnosticCheck]) -> str:
    """Format diagnostic checks for terminal output."""

    lines = [
        "oak-vision-lab environment doctor",
        "",
        f"System: {platform.system()} {platform.release()}",
        f"Machine: {platform.machine()}",
        "",
        "Checks:",
    ]

    for check in checks:
        status = "OK" if check.ok else "FAIL"
        lines.append(f"  [{status}] {check.name}: {check.details}")

    lines.append("")

    if are_all_checks_passing(checks):
        lines.append("Result: environment looks ready.")
    else:
        lines.append("Result: environment has problems that need attention.")

    return "\n".join(lines)
