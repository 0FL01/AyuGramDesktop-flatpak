#!/usr/bin/env python3
#
# Issue #30645 fix: gsl::not_null<T*> constructed from a dangling pointer
# in a deferred main-loop callback, causing "ptr_ != nullptr" assertion
# (pointers:110) → SIGSEGV in reaction/sticker/photo preview overlay.
#
# Root cause: history_view_reaction_preview.cpp has two defects that combine:
#
#   A) extraHide lambdas capture RAW pointers (wrapRaw, backgroundRaw,
#      labelRaw) and test them with `if (rawPtr)` — raw pointers are never
#      nulled on QObject destruction, so the check is always true → deref
#      after the owning unique_qptr was reset → use-after-free →
#      not_null(null) in Ui::Animations::HideWidgets (which takes
#      std::vector<not_null<Ui::RpWidget*>>).
#
#   B) PreviewOverlayState::clear() resets clickable LAST — but clickable is
#      the crl::guard context for the DropdownMenu's setHiddenCallback, so
#      during menuWrap.reset() the guard still passes → hideAll re-enters →
#      calls extraHide → derefs the just-destroyed widget.
#
# This script closes the class by:
#   1. Reordering clear() to reset clickable FIRST — invalidates the guard
#      before any widget destruction, making re-entry architecturally
#      impossible.
#   2. Replacing raw-pointer checks in extraHide with owning unique_qptr
#      checks (QPointer-backed, auto-nullify on ~QObject) — no-op after
#      reset even if re-entry somehow occurs.
#
# Belt and suspenders: either fix alone prevents the crash; together they
# eliminate the entire defect class. The correct pattern already exists in
# ShowWidgetPreview::hideAll (if (state->menuWrap) { ... }) — this brings
# the other two paths in line.
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
        "file": "Telegram/SourceFiles/history/view/history_view_reaction_preview.cpp",
        "edits": [
            # --- Fix B: reorder clear() to reset clickable first ---
            (
                "void clear() {\n"
                f"{T}{T}shutdownGuard.destroy();\n"
                f"{T}{T}menuWrap.reset();\n"
                f"{T}{T}background.reset();\n"
                f"{T}{T}label.reset();\n"
                f"{T}{T}mediaPreview.reset();\n"
                f"{T}{T}clickable.reset();\n"
                f"{T}}}",
                "void clear() {\n"
                f"{T}{T}shutdownGuard.destroy();\n"
                f"{T}{T}clickable.reset();\n"
                f"{T}{T}menuWrap.reset();\n"
                f"{T}{T}background.reset();\n"
                f"{T}{T}label.reset();\n"
                f"{T}{T}mediaPreview.reset();\n"
                f"{T}}}",
            ),
            # --- Fix A (SetupPreviewMenu): owning-pointer check ---
            (
                "state->extraHide = [=] {\n"
                f"{T}{T}if (wrapRaw) {{\n"
                f"{T}{T}{T}wrapRaw->hide(anim::type::normal);\n"
                f"{T}{T}}}\n"
                f"{T}}};",
                "state->extraHide = [=] {\n"
                f"{T}{T}if (state->menuWrap) {{\n"
                f"{T}{T}{T}state->menuWrap->hide(anim::type::normal);\n"
                f"{T}{T}}}\n"
                f"{T}}};",
            ),
            # --- Fix A (ShowReactionPreview): owning-pointer checks ---
            (
                "state->extraHide = [=] {\n"
                f"{T}{T}if (backgroundRaw && labelRaw) {{\n"
                f"{T}{T}{T}Ui::Animations::HideWidgets({{\n"
                f"{T}{T}{T}{T}backgroundRaw,\n"
                f"{T}{T}{T}{T}labelRaw,\n"
                f"{T}{T}{T}}});\n"
                f"{T}{T}}}\n"
                f"{T}}};",
                "state->extraHide = [=] {\n"
                f"{T}{T}if (state->background && state->label) {{\n"
                f"{T}{T}{T}Ui::Animations::HideWidgets({{\n"
                f"{T}{T}{T}{T}state->background.get(),\n"
                f"{T}{T}{T}{T}state->label.get(),\n"
                f"{T}{T}{T}}});\n"
                f"{T}{T}}}\n"
                f"{T}}};",
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
        print("::error::issue #30645 reaction preview fix did not fully apply; see errors above.", file=sys.stderr)
        return 1
    print("issue #30645 reaction preview fix applied successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
