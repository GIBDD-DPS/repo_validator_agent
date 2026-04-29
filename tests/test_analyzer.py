from core.file_analyzer import FileAnalyzer


def test_empty_file():
    analyzer = FileAnalyzer()
    issues = analyzer.analyze_file("test.py", "")
    assert "Файл пустой" in issues[0]


def test_todo_detection():
    analyzer = FileAnalyzer()
    issues = analyzer.analyze_file("test.py", "TODO: fix this")
    assert any("TODO" in issue for issue in issues)
