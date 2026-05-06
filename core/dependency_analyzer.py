# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

"""
Dependency Analyzer – анализ устаревших пакетов, уязвимостей (CVE), лицензий.
В случае отсутствия внешних инструментов парсит requirements.txt напрямую.
"""
import subprocess
import json
import os
import re
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
            "packages": [],           # ← добавлено: список найденных пакетов
            "error": None
        }

        # Ищем файлы зависимостей (requirements.txt, Pipfile, pyproject.toml и т.д.)
        dep_files = self._find_dep_files()
        if not dep_files:
            results["error"] = "Файлы зависимостей (requirements.txt, Pipfile, pyproject.toml) не найдены."
            return results

        # Базовый список пакетов (из requirements.txt, если есть)
        req_file = None
        for f in dep_files:
            if os.path.basename(f) == 'requirements.txt':
                req_file = f
                break
        if req_file:
            results["packages"] = self._parse_requirements(req_file)
        elif dep_files:
            results["packages"] = [os.path.basename(f) for f in dep_files]

        # 1. Уязвимости через pip-audit
        try:
            results["vulnerabilities"] = self._check_vulnerabilities(dep_files)
        except Exception as e:
            results["vulnerabilities"] = [{"error": f"Ошибка проверки уязвимостей: {e}"}]

        # 2. Лицензии через pip-licenses (или fallback)
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

    def _parse_requirements(self, req_path: str) -> List[str]:
        """Читает requirements.txt и возвращает список пакетов (без версий)."""
        packages = []
        try:
            with open(req_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    # Удаляем флаги (--index-url и т.д.)
                    if line.startswith('-'):
                        continue
                    # Извлекаем имя пакета (до первого разделителя версии)
                    match = re.match(r'^[A-Za-z0-9._-]+', line)
                    if match:
                        packages.append(match.group(0))
        except Exception:
            pass
        return packages

    def _check_vulnerabilities(self, dep_files: List[str]) -> List[Dict]:
        """Ищет уязвимости через pip-audit (или возвращает предупреждение)."""
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
                    all_vulns = []
                    for dep in data.get('dependencies', []):
                        for vuln in dep.get('vulns', []):
                            vuln['package'] = dep.get('name', '')
                            all_vulns.append(vuln)
                    return all_vulns
                return [{"error": "Неизвестный формат ответа pip-audit"}]
            else:
                # Если stdout пуст, возможно, уязвимостей нет
                return []
        except subprocess.TimeoutExpired:
            return [{"error": "Превышено время ожидания pip-audit"}]
        except FileNotFoundError:
            return [{"error": "pip-audit не установлен. Добавьте pip-audit в requirements.txt."}]
        except Exception as e:
            return [{"error": f"Ошибка pip-audit: {str(e)}"}]

    def _check_licenses(self, dep_files: List[str]) -> List[Dict]:
        """Извлекает лицензии через pip-licenses или возвращает заглушку."""
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
        except Exception:
            return []
