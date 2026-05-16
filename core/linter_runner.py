# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

import asyncio
import subprocess
import tempfile
import os
from typing import Dict, List, Tuple

class LinterRunner:
    """Запускает линтеры параллельно на переданных файлах с использованием asyncio."""

    async def _run_linter_async(self, cmd: List[str], cwd: str, timeout: int = 30) -> Tuple[str, str, str]:
        """
        Асинхронно запускает команду и возвращает (stdout, stderr, error_message).
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            stdout = stdout.decode('utf-8', errors='replace')
            stderr = stderr.decode('utf-8', errors='replace')
            return stdout, stderr, None
        except asyncio.TimeoutError:
            return "", "", f"Timeout after {timeout}s"
        except Exception as e:
            return "", "", str(e)

    def _parse_flake8_output(self, output: str, cwd: str) -> List[Tuple[str, str]]:
        """Парсит вывод flake8 в список (относительный_путь, сообщение)."""
        issues = []
        for line in output.splitlines():
            parts = line.split(':', 3)
            if len(parts) >= 4:
                full_path = parts[0]
                try:
                    rel_path = os.path.relpath(full_path, cwd)
                except ValueError:
                    rel_path = full_path
                msg = parts[3].strip()
                issues.append((rel_path, f"[flake8] {msg}"))
        return issues

    def _parse_bandit_output(self, output: str, cwd: str) -> List[Tuple[str, str]]:
        """Парсит вывод bandit."""
        issues = []
        for line in output.splitlines():
            if ':' in line:
                parts = line.split(':', 1)
                full_path = parts[0].strip()
                try:
                    rel_path = os.path.relpath(full_path, cwd)
                except ValueError:
                    rel_path = full_path
                msg = parts[1].strip()
                issues.append((rel_path, f"[bandit] {msg}"))
        return issues

    def _parse_eslint_output(self, output: str, cwd: str) -> List[Tuple[str, str]]:
        """Парсит вывод ESLint в формате --format=compact."""
        issues = []
        for line in output.splitlines():
            if ':' in line and 'warning' in line or 'error' in line:
                parts = line.split(':', 3)
                if len(parts) >= 4:
                    full_path = parts[0]
                    try:
                        rel_path = os.path.relpath(full_path, cwd)
                    except ValueError:
                        rel_path = full_path
                    msg = parts[3].strip()
                    issues.append((rel_path, f"[eslint] {msg}"))
        return issues

    async def run_all_async(self, files: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Асинхронно запускает линтеры параллельно.
        files: словарь {относительный_путь: содержимое}
        Возвращает: {путь: [список строк с ошибками]}
        """
        results: Dict[str, List[str]] = {}
        with tempfile.TemporaryDirectory() as tmpdir:
            # Сохраняем все файлы во временную папку
            for path, content in files.items():
                full_path = os.path.join(tmpdir, path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            # Определяем команды линтеров, которые хотим запустить параллельно
            lint_tasks = []
            # flake8 для Python
            if any(path.endswith('.py') for path in files):
                lint_tasks.append(self._run_linter_async(['flake8', '--max-line-length=120', tmpdir], tmpdir))
            # bandit для Python (безопасность)
            if any(path.endswith('.py') for path in files):
                lint_tasks.append(self._run_linter_async(['bandit', '-r', tmpdir, '-f', 'custom', '--msg-template', '{path}: {msg}'], tmpdir))
            # ESLint для JavaScript/TypeScript (если установлен глобально или локально)
            js_files = [p for p in files if p.endswith(('.js', '.ts', '.jsx', '.tsx'))]
            if js_files:
                try:
                    # проверяем доступность eslint
                    subprocess.run(['eslint', '--version'], capture_output=True, check=True)
                    lint_tasks.append(self._run_linter_async(['eslint', '--format=compact', tmpdir], tmpdir))
                except (subprocess.SubprocessError, FileNotFoundError):
                    pass  # eslint не установлен, пропускаем

            # Запускаем все задачи параллельно
            outputs = await asyncio.gather(*lint_tasks, return_exceptions=True)

            # Обрабатываем результаты
            for idx, out in enumerate(outputs):
                if isinstance(out, Exception):
                    continue  # или логировать
                stdout, stderr, err_msg = out
                if err_msg:
                    continue
                # Определяем, какой линтер вернул вывод
                if stdout:
                    # Пытаемся распарсить в зависимости от содержимого (простой эвристикой)
                    if 'flake8' in str(lint_tasks[idx]):
                        parsed = self._parse_flake8_output(stdout, tmpdir)
                    elif 'bandit' in str(lint_tasks[idx]):
                        parsed = self._parse_bandit_output(stdout, tmpdir)
                    elif 'eslint' in str(lint_tasks[idx]):
                        parsed = self._parse_eslint_output(stdout, tmpdir)
                    else:
                        parsed = []
                    for rel_path, msg in parsed:
                        if rel_path not in results:
                            results[rel_path] = []
                        results[rel_path].append(msg)

        return results

    def run_all(self, files: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Синхронная обёртка для вызова из существующего кода.
        Запускает асинхронную версию в цикле asyncio.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            # Если уже есть запущенный цикл, создаём новую задачу
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.run_all_async(files))
                return future.result()
        else:
            return asyncio.run(self.run_all_async(files))
