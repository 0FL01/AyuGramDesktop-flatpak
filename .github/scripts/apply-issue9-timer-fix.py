#!/usr/bin/env python3
#
# Issue #9 fix: base::Timer::setTimeout / ConcurrentTimer::setTimeout /
# DelayedCallTimer::call / CallDelayedEvent ctor aborted (Expects) when a
# caller passed a timeout outside [0, INT_MAX]. Dozens of call sites compute
# timeouts from server flood-wait values, deadline arithmetic and int
# multiplication, none of which can reliably guarantee that range, so the
# range requirement was an unreliable contract pushed onto transmitters and
# the abort recurred across unrelated scenarios (proxy connect, message load,
# QR login, config read). This script closes the class by saturating the
# timeout to [0, INT_MAX] inside the single receiver that owns the int
# conversion, instead of aborting. It also fixes the int*int overflow in the
# delayed-request sendAt computation.
#
# Fail-closed: if an exact target string is missing (upstream drifted) the
# script errors out so the build fails loudly rather than shipping an
# unpatched binary. If a site is already patched (new text present) it is
# skipped, so re-running or an upstream fix is handled gracefully.

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

T = "\t"

patches = [
    {
        "file": "Telegram/lib_base/base/timer.cpp",
        "edits": [
            (
                "#include <QtCore/QTimerEvent>\n\nnamespace base {",
                "#include <QtCore/QTimerEvent>\n#include <algorithm>\n\nnamespace base {",
            ),
            (
                "void Timer::setTimeout(crl::time timeout) {\n"
                f"{T}Expects(timeout >= 0 && timeout <= std::numeric_limits<int>::max());\n\n"
                f"{T}_timeout = static_cast<unsigned int>(timeout);\n"
                "}",
                "void Timer::setTimeout(crl::time timeout) {\n"
                f"{T}_timeout = static_cast<unsigned int>(std::clamp(\n"
                f"{T}{T}timeout,\n"
                f"{T}{T}crl::time(0),\n"
                f"{T}{T}crl::time(std::numeric_limits<int>::max())));\n"
                "}",
            ),
            (
                f"{T}Expects(timeout >= 0);\n\n"
                f"{T}if (!callback) {{\n"
                f"{T}{T}return 0;\n"
                f"{T}}}\n"
                f"{T}auto timerId = startTimer(static_cast<int>(timeout), type);",
                f"{T}if (!callback) {{\n"
                f"{T}{T}return 0;\n"
                f"{T}}}\n"
                f"{T}auto timerId = startTimer(static_cast<int>(std::clamp(\n"
                f"{T}{T}timeout,\n"
                f"{T}{T}crl::time(0),\n"
                f"{T}{T}crl::time(std::numeric_limits<int>::max()))), type);",
            ),
        ],
    },
    {
        "file": "Telegram/lib_base/base/concurrent_timer.cpp",
        "edits": [
            (
                "#include <QtCore/QCoreApplication>\n\nusing namespace base::details;",
                "#include <QtCore/QCoreApplication>\n#include <algorithm>\n\nusing namespace base::details;",
            ),
            (
                ": QEvent(CallDelayedEventType())\n"
                ", _timeout(timeout)\n"
                ", _type(type)\n"
                ", _method(std::move(method)) {\n"
                f"{T}Expects(_timeout >= 0 && _timeout < std::numeric_limits<int>::max());\n"
                "}",
                ": QEvent(CallDelayedEventType())\n"
                ", _timeout(std::clamp(\n"
                f"{T}timeout,\n"
                f"{T}crl::time(0),\n"
                f"{T}crl::time(std::numeric_limits<int>::max())))\n"
                ", _type(type)\n"
                ", _method(std::move(method)) {\n"
                "}",
            ),
            (
                "void ConcurrentTimer::setTimeout(crl::time timeout) {\n"
                f"{T}Expects(timeout >= 0 && timeout <= std::numeric_limits<int>::max());\n\n"
                f"{T}_timeout = static_cast<unsigned int>(timeout);\n"
                "}",
                "void ConcurrentTimer::setTimeout(crl::time timeout) {\n"
                f"{T}_timeout = static_cast<unsigned int>(std::clamp(\n"
                f"{T}{T}timeout,\n"
                f"{T}{T}crl::time(0),\n"
                f"{T}{T}crl::time(std::numeric_limits<int>::max())));\n"
                "}",
            ),
        ],
    },
    {
        "file": "Telegram/SourceFiles/mtproto/mtp_instance.cpp",
        "edits": [
            (
                "auto sendAt = crl::now() + secs * 1000 + 10;",
                "auto sendAt = crl::now() + crl::time(secs) * 1000 + 10;",
            ),
        ],
    },
]


def main():
    failed = False
    for patch in patches:
        path = ROOT / patch["file"]
        if not path.exists():
            print(f"::error::missing file: {patch['file']}", file=sys.stderr)
            failed = True
            continue
        text = path.read_text(encoding="utf-8")
        changed = False
        for old, new in patch["edits"]:
            if new in text:
                print(f"skip (already patched): {patch['file']} :: {old.splitlines()[0][:60]}")
                continue
            if old not in text:
                print(
                    f"::error::target not found in {patch['file']} :: {old.splitlines()[0][:70]}",
                    file=sys.stderr,
                )
                failed = True
                continue
            text = text.replace(old, new, 1)
            changed = True
            print(f"patched: {patch['file']} :: {old.splitlines()[0][:60]}")
        if changed:
            path.write_text(text, encoding="utf-8")
    if failed:
        print("::error::issue #9 timer fix did not fully apply; see errors above.", file=sys.stderr)
        return 1
    print("issue #9 timer fix applied successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
