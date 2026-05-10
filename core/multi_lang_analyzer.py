# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

"""
Multi-Language Analyzer – запускает линтеры для JS/TS, Go, Rust, Dockerfile, K8s.
"""
import subprocess
import os
import json
import tempfile
from typing import Dict, List


class MultiLangAnalyzer:
    """Анализирует файлы разных языков."""

    def analyze(self, files: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Принимает {путь: содержимое}, возвращает {путь: [список замечаний]}.
        """
        results: Dict[str, List[str]] = {}

        # Группируем по языкам
        for path, content in files.items():
            ext = os.path.splitext(path)[1].lower()
            if ext in ('.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs'):
                issues = self._run_eslint(path, content)
            elif ext == '.go':
                issues = self._run_staticcheck(path, content)
            elif ext == '.rs':
                issues = self._run_clippy(path, content)
            elif 'Dockerfile' in path:
                issues = self._run_hadolint(path, content)
            elif ext in ('.yaml', '.yml') and ('deployment' in path or 'service' in path):
                issues = self._run_kubeval(path, content)
            else:
                continue

            if issues:
                results[path] = issues

        return results

    def _run_eslint(self, rel_path: str, content: str) -> List[str]:
        """Запускает ESLint для JavaScript/TypeScript файла."""
        if not self._which('eslint'):
            return [f"[eslint] ESLint не установлен в системе."]
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, os.path.basename(rel_path))
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            try:
                proc = subprocess.run(
                    ['eslint', '--format', 'json', file_path],
                    capture_output=True, text=True, timeout=30
                )
                if proc.stdout:
                    data = json.loads(proc.stdout)
                    if isinstance(data, list) and len(data) > 0:
                        messages = data[0].get('messages', [])
                        return [f"[eslint] {m.get('ruleId', '')}: {m.get('message', '')}" for m in messages]
                if proc.stderr:
                    return [f"[eslint] {proc.stderr.strip()}"]
                return []
            except Exception as e:
                return [f"[eslint] Ошибка: {str(e)}"]

    def _run_staticcheck(self, rel_path: str, content: str) -> List[str]:
        """Запускает staticcheck для Go файла."""
        if not self._which('staticcheck'):
            return [f"[staticcheck] staticcheck не установлен в системе."]
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, os.path.basename(rel_path))
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            try:
                proc = subprocess.run(
                    ['staticcheck', file_path],
                    capture_output=True, text=True, timeout=30
                )
                if proc.stdout or proc.stderr:
                    lines = (proc.stdout + proc.stderr).splitlines()
                    return [f"[staticcheck] {line.strip()}" for line in lines if line.strip()]
                return []
            except Exception as e:
                return [f"[staticcheck] Ошибка: {str(e)}"]

    def _run_clippy(self, rel_path: str, content: str) -> List[str]:
        """Запускает clippy для Rust файла (требуется cargo)."""
        if not self._which('cargo'):
            return [f"[clippy] cargo не установлен в системе."]
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, os.path.basename(rel_path))
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            try:
                # Создаём минимальный Cargo.toml, чтобы clippy работал
                cargo_toml = os.path.join(tmpdir, 'Cargo.toml')
                with open(cargo_toml, 'w') as f:
                    f.write('[package]\nname = "tmp"\nversion = "0.1.0"\nedition = "2021"\n')
                src_dir = os.path.join(tmpdir, 'src')
                os.makedirs(src_dir, exist_ok=True)
                os.rename(file_path, os.path.join(src_dir, 'main.rs'))
                proc = subprocess.run(
                    ['cargo', 'clippy', '--message-format', 'short'],
                    capture_output=True, text=True, timeout=60, cwd=tmpdir
                )
                lines = (proc.stdout + proc.stderr).splitlines()
                return [f"[clippy] {line.strip()}" for line in lines if line.strip()]
            except Exception as e:
                return [f"[clippy] Ошибка: {str(e)}"]

    def _run_hadolint(self, rel_path: str, content: str) -> List[str]:
        """Запускает hadolint для Dockerfile."""
        if not self._which('hadolint'):
            return [f"[hadolint] hadolint не установлен в системе."]
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, os.path.basename(rel_path))
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            try:
                proc = subprocess.run(
                    ['hadolint', file_path],
                    capture_output=True, text=True, timeout=30
                )
                return [f"[hadolint] {line.strip()}" for line in proc.stdout.splitlines() if line.strip()]
            except Exception as e:
                return [f"[hadolint] Ошибка: {str(e)}"]

    def _run_kubeval(self, rel_path: str, content: str) -> List[str]:
        """Запускает kubeval для Kubernetes манифеста."""
        if not self._which('kubeval'):
            return [f"[kubeval] kubeval не установлен в системе."]
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, os.path.basename(rel_path))
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            try:
                proc = subprocess.run(
                    ['kubeval', file_path],
                    capture_output=True, text=True, timeout=30
                )
                return [f"[kubeval] {line.strip()}" for line in proc.stdout.splitlines() if line.strip()]
            except Exception as e:
                return [f"[kubeval] Ошибка: {str(e)}"]

    @staticmethod
    def _which(cmd: str) -> bool:
        """Проверяет наличие команды в системе."""
        return subprocess.run(['which', cmd], capture_output=True).returncode == 0
