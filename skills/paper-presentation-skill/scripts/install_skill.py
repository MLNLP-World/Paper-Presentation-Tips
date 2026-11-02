#!/usr/bin/env python3
"""Install one complete Agent Skills bundle; no third-party installer required."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import shutil
import sys
import uuid

NAME = 'academic-pptx-review'
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SOURCE = ROOT / 'skills' / NAME
CLIENTS = {'codex': '.agents', 'claude': '.claude', 'opencode': '.opencode'}
REQUIRED = ('SKILL.md', 'requirements.txt', 'scripts/analyze_pptx.py',
            'scripts/pptx_reader.py', 'scripts/pptx_runtime.py',
            'scripts/pptx_review_contract.py', 'scripts/pptx_report.py',
            'references/usage.md', 'references/presentation-tips.md',
            'references/frameworks.md', 'references/editing.md', 'references/step3-sources.md',
            'scripts/polish_pptx.py', 'scripts/pptx_edit_package.py',
            'scripts/pptx_edit_plan.py', 'scripts/pptx_edit_quality.py', 'scripts/pptx_preview.py', 'scripts/verify_powerpoint.ps1',
            'scripts/pptx_design.py', 'scripts/pptx_components.py', 'scripts/pptx_native_render.py',
            'scripts/render_office.ps1', 'references/design.md', 'references/generation.md',
            'upstream-lock.json', 'scripts/generate_pptx.py', 'scripts/pptx_pipeline.py',
            'scripts/pptx_upstream.py', 'scripts/pptx_backgrounds.py', 'scripts/pptx_import.py')
REQUIRED_BY_SKILL = {
    NAME: REQUIRED,
    'paper-presentation-skill': ('SKILL.md', 'LICENSE',
                   'requirements.txt', 'scripts/attribution_guard.py',
                   'scripts/project_manager.py', 'scripts/svg_to_pptx.py',
                   'scripts/reviewed_export.py', 'scripts/reference_review.py',
                   'references/academic-chat-design.md',
                   'references/page-reference-generation.md',
                   'references/entry-contract.md', 'references/workflows/routing.md',
                   'assets/templates/styles/academic-research/templates/design_spec.md',
                   'assets/templates/icons/THIRD_PARTY_NOTICES.md'),
}


def bundle_name(source: Path) -> str:
    entry = source / 'SKILL.md'
    if not entry.is_file():
        raise ValueError('Incomplete skill bundle: missing SKILL.md')
    text = entry.read_text(encoding='utf-8')
    if not text.startswith('---\n'):
        raise ValueError('SKILL.md must have Agent Skills frontmatter')
    match = re.search(r'^name:\s*[\'\"]?([a-z0-9-]+)[\'\"]?\s*$',
                      text.split('---', 2)[1], re.M)
    if not match or match[1] not in REQUIRED_BY_SKILL:
        raise ValueError('Unknown or invalid skill name in SKILL.md')
    return match[1]


def bundle_files(source: Path) -> list[Path]:
    source = source.resolve(strict=True)
    for name in REQUIRED_BY_SKILL[bundle_name(source)]:
        if not (source / name).is_file():
            raise ValueError(f'Incomplete skill bundle: missing {name}')
    files = []
    for path in sorted(source.rglob('*')):
        if '__pycache__' in path.parts or path.suffix in ('.pyc', '.pyo'):
            continue
        if (path.relative_to(source).parts[:2] == ('scripts', 'tests')
                or path.relative_to(source).parts[0] == 'tests'):
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(source):
            raise ValueError(f'Bundle resources must stay within the skill: {path}')
        if path.is_file():
            files.append(path)
    return files


def filesystem_path(path: Path) -> Path:
    """Use Windows extended paths for deep temporary installation trees."""
    if os.name != 'nt':
        return path
    value = str(path.resolve())
    if value.startswith('\\\\?\\'):
        return Path(value)
    if value.startswith('\\\\'):
        return Path('\\\\?\\UNC\\' + value[2:])
    return Path('\\\\?\\' + value)


def install(source: Path, target: Path, overwrite: bool = False) -> Path:
    files = bundle_files(source)
    source = source.resolve(strict=True)
    name = bundle_name(source)
    # Resolve and verify all endpoints before any directory move or cleanup.
    if target.is_symlink() or any(p.is_symlink() for p in target.parents):
        raise ValueError('Install target must not be a symlink or have symlink parents')
    target = target.resolve()
    if target.name != name:
        raise ValueError(f'Destination directory must be named {name}')
    if target == source or source.is_relative_to(target) or target.is_relative_to(source):
        raise ValueError('Install target must be separate from the source bundle')
    if target.exists() and not overwrite:
        raise ValueError(f'Install target already exists: {target}; use --overwrite to retain a backup and replace it')
    display_target = target
    target = filesystem_path(target)
    parent = target.parent
    parent.mkdir(parents=True, exist_ok=True)
    stage = parent / f'.{name}.install-{uuid.uuid4().hex}'
    stage.mkdir()
    backup = None
    try:
        for path in files:
            destination = stage / path.relative_to(source)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
            if hashlib.sha256(path.read_bytes()).digest() != hashlib.sha256(destination.read_bytes()).digest():
                raise ValueError(f'Copy verification failed: {path}')
        if target.exists():
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
            backup = parent / f'{name}.previous-{stamp}-{uuid.uuid4().hex[:8]}'
            if target.resolve().parent != parent or backup.resolve().parent != parent:
                raise ValueError('Install backup leaves the verified parent')
            target.rename(backup)
        try:
            stage.rename(target)
        except OSError:
            if backup is not None:
                backup.rename(target)
            raise
    finally:
        if stage.exists():
            if stage.is_symlink() or stage.resolve().parent != parent:
                raise ValueError('Refusing cleanup outside the verified install parent')
            shutil.rmtree(stage)
    print(f'Installed {len(files)} files: {display_target}')
    if backup is not None:
        print(f'Previous install retained: {backup}')
    return target


def sync_entries(source: Path, project: Path) -> None:
    bundle_files(source)
    name = bundle_name(source)
    text = (source / 'SKILL.md').read_text(encoding='utf-8')
    frontmatter = '---' + text.split('---', 2)[1] + '---\n'
    project = project.resolve()
    if source.resolve() != (project / 'skills' / name).resolve():
        raise ValueError(f'Repository entries require the canonical bundle in PROJECT/skills/{name}; use --source for that bundle')
    for directory in ('.agents', '.claude'):
        entry = project / directory / 'skills' / name / 'SKILL.md'
        if entry.is_symlink() or any(p.is_symlink() for p in entry.parents):
            raise ValueError('Repository entry must not use symlink paths')
        # Repo entries are intentionally tiny; standalone installation uses install().
        title = '学术 PPT 生成与润色' if name == 'paper-presentation-skill' else '学术 PPTX 审阅'
        body = (f'\n<!-- Generated by skills/paper-presentation-skill/scripts/install_skill.py --sync-entries. Edit skills/{name} instead. -->\n'
                f'# {title}：仓库入口\n\n'
                f'先完整读取 [通用 Skill](../../../skills/{name}/SKILL.md)，再执行其工作流。'
                '这份入口不包含另一套审阅规则。\n\n'
                f'读取通用 Skill 后，将 `<SKILL_DIR>` 解析为仓库中的 `skills/{name}` 绝对目录；'
                '其 scripts/ 和 references/ 都相对该目录解析，不相对当前工作目录或这份入口解析。\n\n'
                '若要在其他项目或框架独立使用，运行仓库的 `skills/paper-presentation-skill/scripts/install_skill.py` 安装整个通用包；'
                '不得只复制这份仓库入口。\n')
        entry.parent.mkdir(parents=True, exist_ok=True)
        entry.write_text(frontmatter + body, encoding='utf-8')
        print(f'Generated repository entry: {entry}')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill', choices=tuple(REQUIRED_BY_SKILL), default='paper-presentation-skill',
                        help='Bundle to install; defaults to paper-presentation-skill')
    parser.add_argument('--source', type=Path, help='Explicit complete source bundle; name is read from SKILL.md')
    parser.add_argument('--agent', choices=tuple(CLIENTS))
    parser.add_argument('--project', type=Path, default=Path.cwd(), help='Project directory; defaults to cwd')
    parser.add_argument('--destination', type=Path, help='Exact standalone skill directory for other hosts or user installs')
    parser.add_argument('--overwrite', action='store_true', help='Retain existing install as a sibling backup before replacement')
    parser.add_argument('--sync-entries', action='store_true', help='Generate Codex/Claude repository entries; maintainers only')
    args = parser.parse_args()
    if args.sync_entries and (args.agent or args.destination or args.overwrite):
        parser.error('--sync-entries cannot be combined with install options')
    if not args.sync_entries and bool(args.agent) == bool(args.destination):
        parser.error('Choose exactly one of --agent or --destination')
    try:
        source = args.source or ROOT / 'skills' / args.skill
        if args.sync_entries:
            sync_entries(source, args.project)
        else:
            target = args.destination or args.project / CLIENTS[args.agent] / 'skills' / bundle_name(source)
            install(source, target, args.overwrite)
        return 0
    except (ValueError, OSError) as exc:
        print(f'Skill installation failed: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
