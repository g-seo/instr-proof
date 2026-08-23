#!/usr/bin/env bash

set -euo pipefail

usage() {
    printf 'Usage: run-demo.sh [--keep]\n' >&2
}

keep_requested=0
case "$#" in
    0) ;;
    1)
        if [ "$1" != "--keep" ]; then
            usage
            exit 2
        fi
        keep_requested=1
        ;;
    *)
        usage
        exit 2
        ;;
esac

script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd -P)
template_root="$repo_root/examples/demo-repo"
temp_base=""
demo_root=""
demo_repo=""
audit_root=""
snapshot_ready=0
repository_initialized=0
current_stage="setup"

fail() {
    printf 'Demo failed during %s: %s\n' "$current_stage" "$1" >&2
    exit 1
}

remove_allocated_root() {
    target=$1
    expected_prefix=$2
    target_parent=$(CDPATH= cd -- "$(dirname -- "$target")" && pwd -P) || return 1
    target_name=$(basename -- "$target") || return 1
    [ "$target_parent" = "$temp_base" ] || return 1
    case "$target_name" in
        "$expected_prefix".*) rm -rf -- "$target" ;;
        *) return 1 ;;
    esac
}

cleanup() {
    status=$?
    trap - EXIT INT TERM HUP
    if [ "$snapshot_ready" -eq 1 ]; then
        snapshot_parent "$audit_root/after.status" "$audit_root/after.files" || status=1
        if ! cmp -s "$audit_root/before.status" "$audit_root/after.status" ||
            ! cmp -s "$audit_root/before.files" "$audit_root/after.files"; then
            printf 'Demo failed during isolation: parent repository changed\n' >&2
            status=1
        fi
    fi
    if [ -n "$demo_root" ] && [ -d "$demo_root" ] &&
        { [ "$keep_requested" -eq 0 ] || [ "$repository_initialized" -eq 0 ]; }; then
        if ! remove_allocated_root "$demo_root" instrproof-demo; then
            printf 'Demo failed during cleanup: unsafe temporary path\n' >&2
            status=1
        fi
    fi
    if [ -n "$audit_root" ] && [ -d "$audit_root" ]; then
        if ! remove_allocated_root "$audit_root" instrproof-demo-audit; then
            printf 'Demo failed during cleanup: unsafe audit path\n' >&2
            status=1
        fi
    fi
    if [ "$keep_requested" -eq 1 ] && [ "$repository_initialized" -eq 1 ] &&
        [ -d "$demo_repo/.git" ]; then
        printf 'Retained demo repository: %s\n' "$demo_repo"
    fi
    exit "$status"
}

interrupted() {
    printf 'Demo failed during %s: interrupted\n' "$current_stage" >&2
    exit 130
}

trap cleanup EXIT
trap interrupted INT TERM HUP

command -v git >/dev/null 2>&1 || fail "Git is required"
command -v uv >/dev/null 2>&1 || fail "uv is required"

requested_temp_base=${TMPDIR:-/tmp}
case "$requested_temp_base" in
    /*) ;;
    *) fail "temporary base must be an absolute path" ;;
esac
[ -d "$requested_temp_base" ] || fail "temporary base does not exist"
temp_base=$(CDPATH= cd -- "$requested_temp_base" && pwd -P) || fail "temporary base is unavailable"
case "$temp_base" in
    "$repo_root"|"$repo_root"/*)
        fail "temporary base must be outside the InstrProof repository"
        ;;
esac

snapshot_parent() {
    status_output=$1
    files_output=$2
    paths_output="${files_output}.paths"
    if ! git -C "$repo_root" status --porcelain=v1 -z >"$status_output"; then
        printf 'Demo failed during isolation: could not read parent Git status\n' >&2
        return 1
    fi
    if ! git -C "$repo_root" ls-files -z --cached --others --exclude-standard >"$paths_output"; then
        printf 'Demo failed during isolation: could not enumerate parent files\n' >&2
        return 1
    fi
    : >"$files_output"
    while IFS= read -r -d '' relative_path; do
        parent_path="$repo_root/$relative_path"
        if [ -L "$parent_path" ]; then
            file_type=symlink
            content_digest=-
            link_target=$(readlink -- "$parent_path") || return 1
            executable_mode=-
        elif [ -f "$parent_path" ]; then
            file_type=regular
            content_digest=$(sha256sum -- "$parent_path") || return 1
            content_digest=${content_digest%% *}
            link_target=-
            executable_mode=$(stat -c '%a' -- "$parent_path") || return 1
        elif [ -d "$parent_path" ]; then
            file_type=directory
            content_digest=-
            link_target=-
            executable_mode=$(stat -c '%a' -- "$parent_path") || return 1
        else
            file_type=missing
            content_digest=-
            link_target=-
            executable_mode=-
        fi
        printf '%s\0%s\0%s\0%s\0%s\0' \
            "$relative_path" "$file_type" "$content_digest" "$link_target" \
            "$executable_mode" >>"$files_output"
    done <"$paths_output"
    rm -f -- "$paths_output"
}

audit_root=$(mktemp -d "$temp_base/instrproof-demo-audit.XXXXXX") || fail "could not create an audit directory"
snapshot_parent "$audit_root/before.status" "$audit_root/before.files" || fail "could not snapshot the parent repository"
snapshot_ready=1

for required in AGENTS.md src/auth/service.py tests/test_service.py; do
    [ -f "$template_root/$required" ] || fail "missing template file: $required"
done
[ ! -e "$template_root/.git" ] || fail "the demo template must not contain .git metadata"

if ! uv run --offline --project "$repo_root" instrproof --version >/dev/null 2>&1; then
    fail "the InstrProof CLI is unavailable in the project environment"
fi

demo_root=$(mktemp -d "$temp_base/instrproof-demo.XXXXXX") || fail "could not create a temporary directory"
demo_repo="$demo_root/repository"
mkdir "$demo_repo" || fail "could not create the demo repository"
cp -a "$template_root/." "$demo_repo/" || fail "could not copy the demo template"

git -C "$demo_repo" init -q || fail "Git initialization failed"
repository_initialized=1
git -C "$demo_repo" config user.name "InstrProof Demo" || fail "Git author setup failed"
git -C "$demo_repo" config user.email "demo@instrproof.invalid" || fail "Git author setup failed"
git -C "$demo_repo" add -- AGENTS.md src/auth/service.py tests/test_service.py || fail "could not stage the baseline"
git -C "$demo_repo" commit -q -m "Create valid InstrProof demo baseline" || fail "baseline commit failed"
git -C "$demo_repo" tag demo-base || fail "could not create demo-base"
base_commit=$(git -C "$demo_repo" rev-parse --verify 'demo-base^{commit}') || fail "demo-base is missing"

run_application_test() {
    printf '$ python -m unittest discover -s tests\n'
    if ! (cd "$demo_repo" && python3 -m unittest discover -s tests >/dev/null 2>&1); then
        fail "ordinary application tests failed"
    fi
    printf 'Application tests passed.\n'
}

assert_base_unchanged() {
    actual=$(git -C "$demo_repo" rev-parse --verify 'demo-base^{commit}') || fail "demo-base is missing"
    [ "$actual" = "$base_commit" ] || fail "demo-base changed"
}

printf '[1/3] Baseline: instruction matches repository\n'
current_stage="baseline"
run_application_test
printf '$ instrproof check\n'
baseline_stdout="$demo_root/baseline.stdout"
baseline_stderr="$demo_root/baseline.stderr"
if (cd "$demo_repo" && uv run --offline --project "$repo_root" instrproof check >"$baseline_stdout" 2>"$baseline_stderr"); then
    baseline_status=0
else
    baseline_status=$?
fi
cat "$baseline_stdout"
[ "$baseline_status" -eq 0 ] || fail "instrproof check returned status $baseline_status"
[ ! -s "$baseline_stderr" ] || fail "instrproof check wrote unexpected stderr"
expected_baseline='Found 1 verified instruction contract:
PathExists  source=AGENTS.md:1  target=src/auth/service.py  current=present'
[ "$(cat "$baseline_stdout")" = "$expected_baseline" ] || fail "baseline contract did not match the expected PathExists claim"
printf '\n'

printf '[2/3] Refactor: tests pass, instruction is stale\n'
current_stage="refactor"
printf '$ git mv src/auth/service.py src/auth/auth_service.py\n'
git -C "$demo_repo" mv -- src/auth/service.py src/auth/auth_service.py || fail "source refactor failed"
printf '$ update tests/test_service.py import for the moved source\n'
sed -i 's/from src\.auth\.service import/from src.auth.auth_service import/' "$demo_repo/tests/test_service.py" || fail "test import update failed"
[ "$(cat "$demo_repo/AGENTS.md")" = 'Authentication logic is implemented in `src/auth/service.py`.' ] || fail "AGENTS.md changed during the code refactor"
[ ! -e "$demo_repo/src/auth/service.py" ] || fail "the old source path still exists"
printf '$ git diff HEAD -- src/auth tests/test_service.py\n'
git -C "$demo_repo" --no-pager diff HEAD -- src/auth tests/test_service.py || fail "could not display the refactor diff"
run_application_test
assert_base_unchanged
printf '$ instrproof diff --base demo-base --ci\n'
broken_stdout="$demo_root/broken.stdout"
broken_stderr="$demo_root/broken.stderr"
if (cd "$demo_repo" && uv run --offline --project "$repo_root" instrproof diff --base demo-base --ci >"$broken_stdout" 2>"$broken_stderr"); then
    broken_status=0
else
    broken_status=$?
fi
cat "$broken_stdout"
printf 'Broken comparison status: %s\n' "$broken_status"
[ "$broken_status" -eq 1 ] || fail "expected comparison status 1, got $broken_status"
[ ! -s "$broken_stderr" ] || fail "broken comparison wrote unexpected stderr"
expected_broken='InstrProof ✗

1 instruction contract regression

AGENTS.md:1
PathExists(src/auth/service.py)'
[ "$(cat "$broken_stdout")" = "$expected_broken" ] || fail "broken comparison diagnostic did not match the expected single regression"
printf '\n'

printf '[3/3] Repair: instruction updated\n'
current_stage="repair"
printf '$ update AGENTS.md: src/auth/service.py -> src/auth/auth_service.py\n'
sed -i 's#src/auth/service\.py#src/auth/auth_service.py#' "$demo_repo/AGENTS.md" || fail "instruction update failed"
[ -f "$demo_repo/AGENTS.md" ] || fail "AGENTS.md was removed"
grep -Fxq 'Authentication logic is implemented in `src/auth/auth_service.py`.' "$demo_repo/AGENTS.md" || fail "the repaired instruction has the wrong target"
assert_base_unchanged
printf '$ git diff -- AGENTS.md\n'
git -C "$demo_repo" --no-pager diff -- AGENTS.md
run_application_test
assert_base_unchanged
printf '$ instrproof diff --base demo-base --ci\n'
repaired_stdout="$demo_root/repaired.stdout"
repaired_stderr="$demo_root/repaired.stderr"
if (cd "$demo_repo" && uv run --offline --project "$repo_root" instrproof diff --base demo-base --ci >"$repaired_stdout" 2>"$repaired_stderr"); then
    repaired_status=0
else
    repaired_status=$?
fi
cat "$repaired_stdout"
printf 'Repaired comparison status: %s\n' "$repaired_status"
[ "$repaired_status" -eq 0 ] || fail "expected repaired comparison status 0, got $repaired_status"
[ ! -s "$repaired_stderr" ] || fail "repaired comparison wrote unexpected stderr"
expected_repaired='InstrProof ✓

1 baseline contracts checked.
No instruction contract regressions.'
[ "$(cat "$repaired_stdout")" = "$expected_repaired" ] || fail "repaired comparison did not report zero regressions"

printf 'An ordinary refactor moved src/auth/service.py to src/auth/auth_service.py while ordinary tests kept passing.\n'
printf 'AGENTS.md was unchanged, so its old-path evidence was missing and InstrProof CI reported the expected status 1.\n'
printf 'Updating AGENTS.md to match the refactor repaired the instruction contract; the same immutable demo-base then restored CI success with status 0.\n'
