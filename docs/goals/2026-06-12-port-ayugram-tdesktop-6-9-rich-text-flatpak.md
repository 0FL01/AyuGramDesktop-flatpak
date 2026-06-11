# Goal: Port AyuGram Flatpak to Telegram Desktop 6.9 Rich Text

Date started: 2026-06-12
Status: active
Codex goal: `/goal Implement docs/goals/2026-06-12-port-ayugram-tdesktop-6-9-rich-text-flatpak.md until every Completion Audit item is verified by its required evidence, while preserving listed constraints and non-goals. Work checkpoint by checkpoint, update the doc after each meaningful verification, and stop only on verified completion or a repeated blocker with exact evidence and the smallest external action needed.`
Source spec: user request and RECON from 2026-06-12
Goal doc owner: Codex
Last updated: 2026-06-12 00:00

## Objective

Produce a reviewable branch that ports this Flatpak fork from the current AyuGram 6.7.x baseline to a Telegram Desktop 6.9.x source base that includes Rich Text Formatting for Bots, then verify the result through the existing remote-runner feature Flatpak workflow.

Done when every required Completion Audit item is verified by its listed evidence and all out-of-scope constraints are preserved.

## Scope

In scope:
- Create and maintain a dedicated integration branch from `dev`.
- Use Telegram Desktop `v6.9.1` as the current practical source target because public source tags currently expose `v6.9.1`, not `v6.9.2`.
- Move to `v6.9.2` only if a public source tag appears before integration is finalized.
- Port AyuGram-specific source changes, branding, app identity, Flatpak packaging assets, and submodule overrides onto the selected Telegram Desktop 6.9.x base.
- Use the existing remote-runner feature workflow `.github/workflows/flatpak-feature.yml` for binary and Flatpak verification.
- Update this goal document after each meaningful checkpoint and commit each completed checkpoint.

Out of scope:
- Do not build Release locally.
- Do not change the stable release workflow unless the user explicitly asks after feature-branch validation.
- Do not publish a stable Flatpak release from this goal before user review.
- Do not commit secrets, runner credentials, `.env` files, generated build outputs, or private runtime logs.
- Do not force-push `main`, `master`, or `dev`.

## Missing Inputs

- Exact `v6.9.2` source tag availability.
  - Impact: the user requested `v6.9.2`, but public source tags found during RECON expose Telegram Desktop `v6.9.1` and AyuGram `v6.7.8` only.
  - Low-risk assumption or fallback: target Telegram Desktop `v6.9.1`, which already contains Rich Text Formatting for Bots and the follow-up rich-message layout fixes.
  - User/external action needed: if a `v6.9.2` source tag appears, confirm whether to retarget from `v6.9.1` before final verification.

## Repository Context

- Relevant entry points:
  - `.github/workflows/flatpak-feature.yml` checks out a chosen branch and builds the feature Flatpak on the self-hosted runner.
  - `.github/scripts/build-tdesktop-binary.sh` runs the Telegram Desktop Docker build inside `ghcr.io/telegramdesktop/tdesktop/centos_env:latest`.
  - `.github/scripts/build-flatpak-bundle.sh` wraps `flatpak-builder` and creates the bundle.
  - `docs/assets/flatpak-files-feature/com.ayugram.desktop.feature.yml` is the feature Flatpak manifest copied by the feature workflow.
- Existing conventions:
  - Workflows expect `out/Release/AyuGram` before repacking into Flatpak.
  - Source builds require `TDESKTOP_API_ID` and `TDESKTOP_API_HASH` from GitHub secrets.
  - Commit after each completed checkpoint before moving to the next phase.
- Dependencies or runtime assumptions:
  - Telegram Desktop 6.9.x adds `Telegram/ThirdParty/cmark-gfm` and `Telegram/ThirdParty/MicroTeX` submodules for markdown/rich text support.
  - AyuGram keeps forked submodules for `Telegram/codegen`, `Telegram/lib_ui`, `Telegram/lib_tl`, and `Telegram/lib_icu`.
- Validation infrastructure:
  - Primary build validation is remote GitHub Actions workflow `Build AyuGram Flatpak (Feature Branch)`.
  - Local validation before remote dispatch should include git merge status, conflict-free tree, submodule metadata review, and targeted source/build-file inspection.
- Risky areas:
  - `Telegram/SourceFiles/history/*`
  - `Telegram/SourceFiles/data/*`
  - `Telegram/SourceFiles/ui/*`
  - `Telegram/SourceFiles/settings/*`
  - `.gitmodules`
  - `Telegram/CMakeLists.txt`
  - `Telegram/lib_ui`

## Completion Audit

- G1: Dedicated integration branch exists from `dev`.
  - Source: user request, "работаем на отдельной ветке (checkout от dev до новой ветки)".
  - Acceptance: branch is not `dev`, `main`, or `master`; its initial base is current `dev`; checkpoint commits are isolated.
  - Evidence required: `git branch --show-current`, `git merge-base --is-ancestor origin/dev HEAD`, and commit log showing checkpoint commits.
  - Status: in_progress
  - Evidence collected: branch `goal/port-tdesktop-6.9-rich-text-flatpak` created from `dev` before this goal doc was added.

- G2: Source base is updated to Telegram Desktop 6.9.x with Rich Text Formatting for Bots.
  - Source: user request for upstream 6.9.2 feature and RECON confirming the feature appears in Telegram Desktop 6.9/6.9.1.
  - Acceptance: selected source base is `telegramdesktop/tdesktop` `v6.9.1` or later public 6.9.x tag; `Telegram/build/version` and `Telegram/SourceFiles/core/version.h` reflect the selected base; changelog includes Rich Text Formatting for Bots.
  - Evidence required: `git show --no-patch --oneline <selected-source-ref>`, `git show <selected-source-ref>:Telegram/build/version`, and diff review after integration.
  - Status: pending
  - Evidence collected:

- G3: AyuGram-specific behavior and branding are preserved on the 6.9.x base.
  - Source: repository purpose as AyuGram Flatpak fork and user request for an AyuGram binary.
  - Acceptance: AyuGram app name, binary name, icons, Flatpak app IDs/manifests, and core AyuGram feature source files remain present after integration.
  - Evidence required: targeted diff review for `CMakeLists.txt`, `Telegram/CMakeLists.txt`, `Telegram/SourceFiles/ayu`, `lib/xdg`, `docs/assets/flatpak-files*`, and generated workflow artifact name.
  - Status: pending
  - Evidence collected:

- G4: Rich Text Formatting for Bots is retained and not accidentally reverted during conflict resolution.
  - Source: Telegram blog announcement and Telegram Desktop 6.9 changelog found during RECON.
  - Acceptance: rich-message/markdown/IV code paths from Telegram Desktop 6.9.x remain in the integrated tree, including support files and build registration.
  - Evidence required: source diff review for `Telegram/SourceFiles/iv`, rich-message files, markdown parser integration, `Telegram/CMakeLists.txt`, and submodules `cmark-gfm` and `MicroTeX`.
  - Status: pending
  - Evidence collected:

- G5: Submodule metadata and pointers are valid for both AyuGram forks and Telegram Desktop 6.9.x additions.
  - Source: RECON `.gitmodules` diff and existing AyuGram fork overrides.
  - Acceptance: `.gitmodules` preserves AyuGram URLs for `codegen`, `lib_ui`, `lib_tl`, `lib_icu`; adds Telegram 6.9.x `cmark-gfm` and `MicroTeX`; `git submodule sync --recursive` and update can run on the remote runner.
  - Evidence required: `.gitmodules` diff review and successful remote workflow submodule initialization logs.
  - Status: pending
  - Evidence collected:

- G6: Existing feature Flatpak workflow builds a `.flatpak` bundle on the remote runner.
  - Source: user clarification to use ready build manifests and `flatpak-feature.yml`.
  - Acceptance: workflow `Build AyuGram Flatpak (Feature Branch)` completes for the integration branch and publishes or exposes the feature `.flatpak` artifact/release.
  - Evidence required: GitHub Actions run URL or release URL, successful job summary, and artifact filename.
  - Status: pending
  - Evidence collected:

- Q1: Keep packaging changes minimal and maintainable.
  - Source: repository policy and user request to use existing manifests.
  - Acceptance: no new dependency framework or replacement build pipeline is introduced; feature workflow remains the primary verification path.
  - Evidence required: diff review showing only necessary source, submodule, and metadata changes.
  - Status: pending
  - Evidence collected:

- Q2: Do not leak secrets or runner-local data.
  - Source: repository safety requirements and GitHub Actions secret usage.
  - Acceptance: no secrets, tokens, `.env`, runner logs with credentials, or generated build outputs are committed.
  - Evidence required: `git status --short`, staged diff review, and absence of secret-like files in commits.
  - Status: pending
  - Evidence collected:

- V1: Integration tree is conflict-free before remote build.
  - Source: merge/rebase workflow requirement.
  - Acceptance: no conflict markers remain and `git status` does not show unmerged paths.
  - Evidence required: `git status --short`, `rg '<<<<<<<|=======|>>>>>>>'` limited to source/config/docs with expected exclusions if any.
  - Status: pending
  - Evidence collected:

- V2: Remote feature build validates source build and Flatpak repack.
  - Source: `.github/workflows/flatpak-feature.yml`.
  - Acceptance: remote workflow completes `Build AyuGram binary`, `Verify binary exists`, and `Build Flatpak package` steps.
  - Evidence required: GitHub Actions run URL/log summary.
  - Status: pending
  - Evidence collected:

- V3: User review gate is respected after the first checkpoint.
  - Source: user request, "далее коммит, упоминание первого шага, я сделаю ревью".
  - Acceptance: stop after committing this goal contract checkpoint and report the branch, commit, file, and next checkpoint for user review.
  - Evidence required: commit hash and user-facing progress update.
  - Status: in_progress
  - Evidence collected:

- N1: Stable release workflow is not used for the first integration validation.
  - Source: user clarification to use `flatpak-feature.yml`.
  - Must preserve: stable workflow remains out of first-pass validation and is not dispatched for this checkpoint.
  - Evidence required: progress log and command history showing feature workflow as planned validation.
  - Status: pending
  - Evidence collected:

## Implementation Plan

1. Goal contract and review checkpoint.
   - Audit IDs: G1, V3, N1
   - Expected changes: create this goal document on a dedicated branch from `dev`.
   - Validation: `git status --short --branch`, staged diff review, commit the goal doc only.
   - Exit condition: user receives branch, commit hash, and the next checkpoint for review.

2. Prepare integration base.
   - Audit IDs: G2, G5
   - Expected changes: fetch selected Telegram Desktop 6.9.x source ref and AyuGram 6.7.8 reference; document exact selected source ref.
   - Validation: ref existence checks and version file inspection.
   - Exit condition: selected source ref is recorded and ready for merge/rebase.

3. Integrate AyuGram delta onto Telegram Desktop 6.9.x.
   - Audit IDs: G2, G3, G4, G5, V1
   - Expected changes: source tree merge/rebase, conflict resolution, submodule metadata updates.
   - Validation: conflict-free status, targeted diff review, conflict-marker grep.
   - Exit condition: tree is commit-ready and source-level audit has no known missing Rich Text or AyuGram pieces.

4. Remote feature build.
   - Audit IDs: G6, V2, Q1, Q2
   - Expected changes: none unless build fixes are required.
   - Validation: dispatch `.github/workflows/flatpak-feature.yml` for the integration branch on the remote runner.
   - Exit condition: successful workflow run or documented blocker with exact failing step and smallest next action.

5. Review and final audit.
   - Audit IDs: all
   - Expected changes: final goal-doc evidence update, any small fixes from review.
   - Validation: verify every Completion Audit item has current evidence.
   - Exit condition: all required items are verified or the remaining gaps are explicitly blocked or deferred by user decision.

## Validation Contract

- Static checks:
  - `git status --short --branch`
  - `rg '<<<<<<<|=======|>>>>>>>' Telegram CMakeLists.txt .gitmodules docs .github`
  - targeted diff review for `.gitmodules`, `Telegram/CMakeLists.txt`, `Telegram/SourceFiles/history`, `Telegram/SourceFiles/data`, `Telegram/SourceFiles/ui`, `Telegram/SourceFiles/iv`, and `Telegram/SourceFiles/ayu`
- Tests:
  - No dedicated local unit-test target is required for the first checkpoint.
  - Build validation is the remote feature workflow.
- Runtime/manual verification:
  - User reviews this first checkpoint before integration starts.
  - After a successful feature build, install or inspect the produced `.flatpak` bundle and verify it launches as AyuGram.
- Artifact verification:
  - Remote workflow run URL.
  - Feature Flatpak release or artifact filename.
  - `out/Release/AyuGram` existence in workflow logs.
- Done when:
  - Every Completion Audit item is `verified` or explicitly resolved by user decision.

## Decisions

- 2026-06-12: Use a dedicated branch from `dev`: `goal/port-tdesktop-6.9-rich-text-flatpak`, because the user requested reviewable work separate from `dev`.
- 2026-06-12: Target Telegram Desktop `v6.9.1` unless `v6.9.2` source appears, because public source discovery found `v6.9.1` as the latest Telegram Desktop tag and AyuGram `v6.7.8` as the latest AyuGram tag.
- 2026-06-12: Use `.github/workflows/flatpak-feature.yml` for first build validation, because the user confirmed the build runs on a remote runner with the existing feature manifest.

## Progress Log

- 2026-06-12 00:00: Checkpoint 1 started: goal contract and review gate.
  - Changed: created `docs/goals/2026-06-12-port-ayugram-tdesktop-6-9-rich-text-flatpak.md`.
  - Evidence: RECON found no public AyuGram `v6.9.2` tag, no public Telegram Desktop `v6.9.2` tag, Telegram Desktop `v6.9.1` as latest source tag, 32 simulated content conflicts and 7 modify/delete conflicts for the AyuGram 6.7.8 to Telegram 6.9.1 integration.
  - Commands: `git switch dev`, `git switch -c goal/port-tdesktop-6.9-rich-text-flatpak`.
  - Audit IDs updated: G1, V3, N1.
  - Next: commit this checkpoint and wait for user review before integration.

## Risks and Blockers

- Telegram Desktop 6.9.x rich-message pipeline overlaps with AyuGram message rendering changes.
  - Impact: conflict resolution can compile while subtly breaking Rich Text layout or AyuGram badges/filters/ghost-mode rendering.
  - Evidence: RECON overlap showed 185 changed files in common and conflicts concentrated in history/data/ui/settings.
  - Mitigation or requested decision: resolve in small commits with targeted diff review and remote feature builds after source integration.
  - Audit IDs affected: G3, G4, V1, V2.

- Public `v6.9.2` source tag is not currently available.
  - Impact: exact requested version cannot be used until a public source tag exists.
  - Evidence: RECON saw Telegram Desktop tags through `v6.9.1` and AyuGram tags through `v6.7.8`.
  - Mitigation or requested decision: proceed with `v6.9.1`, retarget if `v6.9.2` appears before final build.
  - Audit IDs affected: G2, G6.

## Final Verification

Filled only when complete.

- Completion Audit result:
- Commands run:
- Artifacts inspected:
- Remaining gaps:
- User-accepted exceptions:
- Final status:
