# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

"""
Dependency Analyzer – анализ устаревших пакетов, уязвимостей (CVE), лицензий.
"""
import subprocess
import json
import os
from typing import Dict, List


class DependencyAnalyzer:
    """Проверяет зависимости Python‑проекта."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def analyze(self) -> Dict:
        """Возвращает словарь с результатами анализа зависимостей."""
        results: Dict[str, any] = {
            "outdated": [],
            "vulnerabilities": [],
            "licenses": [],
            "error": None
        }

        # Ищем файлы зависимостей (requirements.txt, Pipfile, pyproject.toml и т.д.)
        dep_files = self._find_dep_files()
        if not dep_files:
            results["error"] = "Файлы зависимостей (requirements.txt, Pipfile, pyproject.toml) не найдены."
            return results

        # 1. Устаревшие пакеты (заглушка – можно расширить)
        # В реальной реализации здесь будет запрос к PyPI API

        # 2. Уязвимости через pip-audit
        try:
            results["vulnerabilities"] = self._check_vulnerabilities(dep_files)
        except Exception as e:
            results["error"] = f"Ошибка проверки уязвимостей: {e}"

        # 3. Лицензии через pip-licenses
        try:
            results["licenses"] = self._check_licenses(dep_files)
        except Exception:
            pass  # не критично

        return results

    def _find_dep_files(self) -> List[str]:
        patterns = ['requirements.txt', 'Pipfile', 'pyproject.toml', 'setup.py', 'setup.cfg']
        found = []
        for pattern in patterns:
            path = os.path.join(self.repo_path, pattern)
            if os.path.isfile(path):
                found.append(path)
        return found

    def _check_vulnerabilities(self, dep_files: List[str]) -> List[Dict]:
        """Ищет уязвимости через pip-audit."""
        req_file = None
        for f in dep_files:
            if os.path.basename(f) == 'requirements.txt':
                req_file = f
                break
        if not req_file:
            return []

        cmd = ['pip-audit', '--requirement', req_file, '--format', 'json']
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            # pip-audit возвращает JSON даже при наличии уязвимостей (returncode != 0)
            if proc.stdout:
                data = json.loads(proc.stdout)
                # pip-audit >= 2.4 возвращает объект с ключом "dependencies" или список
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    # извлекаем все уязвимости из всех зависимостей
                    all_vulns = []
                    for dep in data.get('dependencies', []):
                        for vuln in dep.get('vulns', []):
                            vuln['package'] = dep.get('name', '')
                            all_vulns.append(vuln)
                    return all_vulns
                return [{"error": "Неизвестный формат ответа pip-audit"}]
            else:
                return [{"error": proc.stderr.strip() or "Пустой ответ pip-audit"}]
        except subprocess.TimeoutExpired:
            return [{"error": "Превышено время ожидания pip-audit"}]
        except FileNotFoundError:
            return [{"error": "pip-audit не установлен. Добавьте pip-audit в requirements.txt."}]

    def _check_licenses(self, dep_files: List[str]) -> List[Dict]:
        """Извлекает лицензии через pip-licenses."""
        req_file = None
        for f in dep_files:
            if os.path.basename(f) == 'requirements.txt':
                req_file = f
                break
        if not req_file:
            return []

        cmd = ['pip-licenses', '--from', req_file, '--format', 'json']
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if proc.returncode == 0 and proc.stdout.strip():
                return json.loads(proc.stdout)
            else:
                return []
        except FileNotFoundError:
            return []
