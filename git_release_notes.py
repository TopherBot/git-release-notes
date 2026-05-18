#!/usr/bin/env python3
"""git-release-notes – generate markdown release notes from git tags.

Tiny, zero‑dependency, single‑file utility.

Usage:
    ./git_release_notes.py <old-tag> <new-tag> [--output FILE]
"""
import argparse, subprocess, sys, datetime

def run_git(args):
    """Execute a git command and return its stdout as a stripped string."""
    result = subprocess.run(['git'] + args, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(f"Git error: {result.stderr}\n")
        sys.exit(1)
    return result.stdout.strip()

def commit_hashes(old, new):
    rev = f"{old}..{new}"
    out = run_git(['rev-list', '--reverse', rev])
    return out.splitlines() if out else []

def commit_message(sha):
    return run_git(['log', '-1', '--pretty=%B', sha])

def parse_conventional(msg):
    """Very small Conventional Commits parser.
    Returns (type, scope, description).
    """
    first = msg.splitlines()[0].strip()
    if ':' not in first:
        return ('misc', None, first)
    hdr, desc = first.split(':', 1)
    desc = desc.strip()
    if '(' in hdr and hdr.endswith(')'):
        typ, scope = hdr.split('(', 1)
        scope = scope[:-1]
        return (typ.strip(), scope.strip(), desc)
    return (hdr.strip(), None, desc)

def group_by_type(commits):
    groups = {}
    mapping = {
        'feat': 'Features',
        'fix': 'Bug Fixes',
        'docs': 'Documentation',
        'refactor': 'Refactoring',
        'test': 'Tests',
        'chore': 'Chores'
    }
    for sha in commits:
        msg = commit_message(sha)
        typ, scope, desc = parse_conventional(msg)
        cat = mapping.get(typ, 'Misc')
        groups.setdefault(cat, []).append((sha[:7], desc, scope))
    return groups

def render_md(tag, groups):
    today = datetime.date.today().isoformat()
    lines = [f"## {tag} – {today}", ""]
    order = ['Features','Bug Fixes','Documentation','Refactoring','Tests','Chores','Misc']
    for cat in order:
        items = groups.get(cat)
        if not items:
            continue
        lines.append(f"### {cat}")
        for short_sha, desc, scope in items:
            prefix = f"({scope}) " if scope else ""
            lines.append(f"- {prefix}{desc} ({short_sha})")
        lines.append("")
    return "\n".join(lines).strip() + "\n"

def main():
    p = argparse.ArgumentParser(description='Generate markdown release notes from git tags.')
    p.add_argument('old_tag', help='previous tag (exclusive)')
    p.add_argument('new_tag', help='new tag (inclusive)')
    p.add_argument('--output', '-o', help='file to write notes, defaults to stdout')
    args = p.parse_args()

    hashes = commit_hashes(args.old_tag, args.new_tag)
    if not hashes:
        sys.stderr.write('No commits found between the given tags.\n')
        sys.exit(0)
    groups = group_by_type(hashes)
    markdown = render_md(args.new_tag, groups)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(markdown)
        print(f'Notes written to {args.output}')
    else:
        print(markdown)

if __name__ == '__main__':
    main()
