#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
work_dir=$(mktemp -d)
validation_python=${INSTRPROOF_VALIDATION_PYTHON:-3.12}
if [[ -z ${INSTRPROOF_VALIDATION_PYTHON:-} ]]; then
  export UV_PYTHON_INSTALL_DIR="$work_dir/python"
fi

cleanup() {
  find "$work_dir" -depth -delete
}
trap cleanup EXIT

phase() {
  printf '\n==> %s\n' "$1"
}

run_capture() {
  local result_dir=$1
  local name=$2
  local expected_status=$3
  shift 3
  local actual_status

  if "$@" >"$result_dir/$name.stdout" 2>"$result_dir/$name.stderr"; then
    actual_status=0
  else
    actual_status=$?
  fi
  printf '%s\n' "$actual_status" >"$result_dir/$name.status"
  if [[ $actual_status -ne $expected_status ]]; then
    printf 'Smoke test %s returned %s; expected %s.\n' \
      "$name" "$actual_status" "$expected_status" >&2
    return 1
  fi
}

make_fixture() {
  local fixture=$1
  mkdir -p "$fixture/src"
  printf 'value = 1\n' >"$fixture/src/app.py"
  printf 'Use `src/app.py`.\n' >"$fixture/AGENTS.md"
  git -C "$fixture" init -q
  git -C "$fixture" config user.name "InstrProof release validation"
  git -C "$fixture" config user.email "release-validation@example.invalid"
  git -C "$fixture" add AGENTS.md src/app.py
  git -C "$fixture" commit -qm "Create smoke-test fixture"
}

smoke_artifact() {
  local python_path=$1
  local cli_path=$2
  local fixture=$3
  local result_dir=$4
  mkdir -p "$result_dir"
  make_fixture "$fixture"

  if [[ ! -x $cli_path ]]; then
    printf 'Installed instrproof CLI is missing or not executable: %s\n' \
      "$cli_path" >&2
    return 1
  fi

  (
    cd "$fixture"
    unset PYTHONPATH
    run_capture "$result_dir" help 0 "$cli_path" --help
    run_capture "$result_dir" version 0 "$cli_path" --version
    run_capture "$result_dir" import-version 0 "$python_path" -I -c \
      'import instrproof; print(instrproof.__version__)'
    run_capture "$result_dir" check 0 "$cli_path" check
    run_capture "$result_dir" diff-pass 0 "$cli_path" diff --base HEAD
    find src -type f -name app.py -delete
    local expected_status=1
    run_capture "$result_dir" diff-regression "$expected_status" \
      "$cli_path" diff --base HEAD
  )

  "$python_path" -I -c \
    'import instrproof, pathlib, sys; p = pathlib.Path(instrproof.__file__).resolve(); prefix = pathlib.Path(sys.prefix).resolve(); assert p.is_relative_to(prefix), (p, prefix)'
}

create_development_environment() {
  local environment=$1
  phase "Create clean development environment"
  uv venv --python 3.12 "$environment"
  VIRTUAL_ENV="$environment" uv sync \
    --active --locked --dev --python "$environment/bin/python"
}

build_artifacts() {
  local python_path=$1
  local output_dir=$2
  phase "Build wheel and source distribution"
  uv build --python "$python_path" --out-dir "$output_dir"
}

validate_artifacts() {
  local python_path=$1
  local output_dir=$2
  local wheel_files=("$output_dir"/*.whl)
  local sdist_files=("$output_dir"/*.tar.gz)
  local wheel_path=${wheel_files[0]}
  local sdist_path=${sdist_files[0]}

  phase "Validate package metadata"
  PATH="$(dirname "$python_path"):$PATH" \
    twine check --strict "$wheel_path" "$sdist_path"
  phase "Inspect artifact contents"
  "$python_path" "$repo_root/scripts/inspect_artifacts.py" "$output_dir"
}

install_and_smoke() {
  local kind=$1
  local artifact=$2
  local result_dir=$3
  local environment="$work_dir/$kind-environment"
  local fixture="$work_dir/$kind-fixture"

  case "$kind" in
    wheel) phase "Validate wheel installation" ;;
    sdist) phase "Validate source distribution installation" ;;
    *) printf 'Unknown artifact kind: %s\n' "$kind" >&2; return 2 ;;
  esac
  uv venv --python "$validation_python" "$environment"
  uv pip install --python "$environment/bin/python" "$artifact"
  smoke_artifact \
    "$environment/bin/python" "$environment/bin/instrproof" \
    "$fixture" "$result_dir"
}

compare_results() {
  local wheel_results=$1
  local sdist_results=$2
  phase "Compare artifact behavior"
  diff -ru "$wheel_results" "$sdist_results"
}

cd "$repo_root"

case "${1:-}" in
  --build)
    [[ $# -eq 2 ]] || { printf 'Usage: %s --build OUTPUT_DIR\n' "$0" >&2; exit 2; }
    dev_env="$work_dir/development"
    create_development_environment "$dev_env"
    build_artifacts "$dev_env/bin/python" "$(realpath -m "$2")"
    ;;
  --validate-artifacts)
    [[ $# -eq 2 ]] || { printf 'Usage: %s --validate-artifacts ARTIFACT_DIR\n' "$0" >&2; exit 2; }
    dev_env="$work_dir/development"
    create_development_environment "$dev_env"
    validate_artifacts "$dev_env/bin/python" "$(realpath "$2")"
    ;;
  --smoke)
    [[ $# -eq 4 ]] || { printf 'Usage: %s --smoke wheel|sdist ARTIFACT RESULTS\n' "$0" >&2; exit 2; }
    install_and_smoke "$2" "$(realpath "$3")" "$(realpath -m "$4")"
    ;;
  --compare)
    [[ $# -eq 3 ]] || { printf 'Usage: %s --compare WHEEL_RESULTS SDIST_RESULTS\n' "$0" >&2; exit 2; }
    compare_results "$(realpath "$2")" "$(realpath "$3")"
    ;;
  "")
    dev_env="$work_dir/development"
    dist_dir="$work_dir/dist"
    create_development_environment "$dev_env"
    phase "Run complete test suite"
    "$dev_env/bin/python" -m pytest
    build_artifacts "$dev_env/bin/python" "$dist_dir"
    validate_artifacts "$dev_env/bin/python" "$dist_dir"
    wheel_files=("$dist_dir"/*.whl)
    sdist_files=("$dist_dir"/*.tar.gz)
    wheel_path=${wheel_files[0]}
    sdist_path=${sdist_files[0]}
    install_and_smoke wheel "$wheel_path" "$work_dir/wheel-results"
    install_and_smoke sdist "$sdist_path" "$work_dir/sdist-results"
    compare_results "$work_dir/wheel-results" "$work_dir/sdist-results"
    printf '\nRelease validation passed for %s and %s.\n' \
      "$(basename "$wheel_path")" "$(basename "$sdist_path")"
    ;;
  *)
    printf 'Usage: %s [--build OUTPUT_DIR | --validate-artifacts ARTIFACT_DIR | --smoke wheel|sdist ARTIFACT RESULTS | --compare WHEEL_RESULTS SDIST_RESULTS]\n' "$0" >&2
    exit 2
    ;;
esac
