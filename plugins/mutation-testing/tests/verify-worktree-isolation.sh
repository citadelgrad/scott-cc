#!/usr/bin/env bash
# Regression check for the main-tree isolation fix in test-saboteur.md /
# test-quality-reviewer.md.
#
# Background: the Edit/Write tools require an absolute file_path and ignore
# a Bash shell's current directory. The pre-fix instructions told the
# saboteur agent to `cd` into a worktree and then "use the Edit tool" with
# the bare relative filename, which silently edited the file in the MAIN
# tree instead of the worktree. This script runs the fixed procedure
# end-to-end against a disposable sandbox repo (never the real
# scott-cc repo) and asserts `git status --short` on the main tree stays
# empty throughout, exactly as the hardened test-saboteur.md now requires.
#
# Usage: ./verify-worktree-isolation.sh
# Exit code 0 = isolation held. Non-zero = isolation broke (bug reproduced).

set -euo pipefail

sandbox="$(mktemp -d)"
cleanup() {
  cd /
  rm -rf "$sandbox"
}
trap cleanup EXIT

echo "== Setting up disposable sandbox repo at $sandbox/main =="
main_repo_root="$sandbox/main"
mkdir -p "$main_repo_root"
git -C "$main_repo_root" init -q
git -C "$main_repo_root" config user.email "test@example.com"
git -C "$main_repo_root" config user.name "Isolation Test"

target_file="payment.py"
cat > "$main_repo_root/$target_file" <<'EOF'
def is_eligible(retry_count):
    return retry_count >= 3
EOF
git -C "$main_repo_root" add "$target_file"
git -C "$main_repo_root" commit -q -m "initial"

baseline="$(git -C "$main_repo_root" status --short)"
if [ -n "$baseline" ]; then
  echo "FAIL: sandbox main tree was not clean before the test even started" >&2
  exit 1
fi

echo "== Step 2: create worktree (fixed pattern: git -C, absolute path) =="
worktree_abs_path="$main_repo_root/../test-mutation-001"
git -C "$main_repo_root" worktree add -q "$worktree_abs_path" HEAD

echo "== Mid-run check: worktree creation must not touch the main tree =="
after_worktree="$(git -C "$main_repo_root" status --short)"
if [ -n "$after_worktree" ]; then
  echo "FAIL: creating the worktree dirtied the main tree" >&2
  echo "$after_worktree" >&2
  exit 1
fi

echo "== Step 3: apply mutation using the fixed absolute edit_target =="
edit_target="${worktree_abs_path}/${target_file}"
# Stand-in for the Edit tool call: it must operate on edit_target, never
# on the bare relative $target_file, exactly as test-saboteur.md now requires.
sed -i.bak 's/retry_count >= 3/retry_count > 3/' "$edit_target"
rm -f "${edit_target}.bak"

echo "== Mandatory post-mutation check (from the hardened test-saboteur.md) =="
after_mutation="$(git -C "$main_repo_root" status --short)"
if [ -n "$after_mutation" ]; then
  echo "FAIL: mutation leaked into the main tree — isolation bug reproduced" >&2
  echo "$after_mutation" >&2
  exit 1
fi

echo "== Sanity: confirm the mutation actually landed in the worktree =="
if ! grep -q 'retry_count > 3' "$edit_target"; then
  echo "FAIL: mutation did not apply to the worktree copy either — test is broken" >&2
  exit 1
fi
if grep -q 'retry_count > 3' "$main_repo_root/$target_file"; then
  echo "FAIL: main tree's file was mutated — isolation bug reproduced" >&2
  exit 1
fi

echo "== Cleanup: remove worktree, as test-quality-reviewer does post-run =="
git -C "$main_repo_root" worktree remove "$worktree_abs_path" --force >/dev/null

final="$(git -C "$main_repo_root" status --short)"
if [ -n "$final" ]; then
  echo "FAIL: main tree not clean after worktree cleanup" >&2
  echo "$final" >&2
  exit 1
fi

echo "PASS: main repo git status --short stayed empty through worktree create, mutate, and cleanup."
exit 0
