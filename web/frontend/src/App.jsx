import React, { useState } from "react";

const API_URL = "http://localhost:8000/analyze";

export default function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [mode, setMode] = useState("auto");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl, mode }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#050816",
        color: "#e5ecff",
        fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
        padding: "24px",
      }}
    >
      <h1 style={{ marginBottom: 8 }}>Repo Validator Agent</h1>
      <p style={{ marginTop: 0, color: "#9aa4c6" }}>
        Введите ссылку на GitHub-репозиторий и запустите анализ.
      </p>

      <form
        onSubmit={handleSubmit}
        style={{
          background: "#111827",
          borderRadius: 12,
          padding: 16,
          maxWidth: 640,
          marginBottom: 24,
          border: "1px solid #1f2937",
        }}
      >
        <div style={{ marginBottom: 12 }}>
          <label style={{ display: "block", marginBottom: 4, fontSize: 14 }}>
            GitHub URL
          </label>
          <input
            type="text"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            placeholder="https://github.com/user/repo"
            style={{
              width: "100%",
              padding: "8px 10px",
              borderRadius: 8,
              border: "1px solid #374151",
              background: "#020617",
              color: "#e5ecff",
              fontSize: 14,
            }}
          />
        </div>

        <div style={{ marginBottom: 12 }}>
          <label style={{ display: "block", marginBottom: 4, fontSize: 14 }}>
            Режим
          </label>
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            style={{
              padding: "6px 10px",
              borderRadius: 8,
              border: "1px solid #374151",
              background: "#020617",
              color: "#e5ecff",
              fontSize: 14,
            }}
          >
            <option value="auto">Авто (применять изменения)</option>
            <option value="step">Пока только анализ (в API всё равно auto)</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={!repoUrl || loading}
          style={{
            marginTop: 8,
            padding: "8px 16px",
            borderRadius: 999,
            border: "none",
            background: loading ? "#4b5563" : "#2563eb",
            color: "#e5ecff",
            fontWeight: 600,
            cursor: loading ? "default" : "pointer",
            fontSize: 14,
          }}
        >
          {loading ? "Анализ..." : "Запустить анализ"}
        </button>
      </form>

      {error && (
        <div
          style={{
            maxWidth: 640,
            marginBottom: 16,
            padding: 12,
            borderRadius: 8,
            background: "#3f1d2b",
            color: "#fecaca",
            fontSize: 14,
          }}
        >
          Ошибка: {error}
        </div>
      )}

      {result && (
        <div
          style={{
            maxWidth: 960,
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 16,
          }}
        >
          <div
            style={{
              background: "#111827",
              borderRadius: 12,
              padding: 16,
              border: "1px solid #1f2937",
            }}
          >
            <h2 style={{ marginTop: 0, marginBottom: 8 }}>Сводка</h2>
            <p style={{ margin: 0, fontSize: 14 }}>
              Режим: <b>{result.mode}</b>
            </p>
            <p style={{ margin: 0, fontSize: 14 }}>
              Файлов проанализировано: <b>{result.files_analyzed}</b>
            </p>
            <p style={{ margin: 0, fontSize: 14 }}>
              Файлов изменено: <b>{result.files_fixed}</b>
            </p>
            <p style={{ marginTop: 8, fontSize: 13, color: "#9aa4c6" }}>
              Отчёты и исправленные файлы: <br />
              <code>{result.report_dir}</code>
            </p>
          </div>

          <div
            style={{
              background: "#111827",
              borderRadius: 12,
              padding: 16,
              border: "1px solid #1f2937",
              maxHeight: "60vh",
              overflow: "auto",
            }}
          >
            <h2 style={{ marginTop: 0, marginBottom: 8 }}>Проблемы проекта</h2>
            {result.project_issues && result.project_issues.length > 0 ? (
              <ul style={{ margin: 0, paddingLeft: 18, fontSize: 14 }}>
                {result.project_issues.map((issue, idx) => (
                  <li key={idx}>{issue}</li>
                ))}
              </ul>
            ) : (
              <p style={{ fontSize: 14, color: "#9aa4c6" }}>
                Проектных проблем не найдено.
              </p>
            )}
          </div>

          <div
            style={{
              gridColumn: "1 / span 2",
              background: "#111827",
              borderRadius: 12,
              padding: 16,
              border: "1px solid #1f2937",
              maxHeight: "60vh",
              overflow: "auto",
            }}
          >
            <h2 style={{ marginTop: 0, marginBottom: 8 }}>Проблемы по файлам</h2>
            {Object.entries(result.file_issues).map(([path, issues]) =>
              issues && issues.length ? (
                <div
                  key={path}
                  style={{
                    marginBottom: 12,
                    padding: 8,
                    borderRadius: 8,
                    background: "#020617",
                  }}
                >
                  <div
                    style={{
                      fontFamily: "monospace",
                      fontSize: 13,
                      color: "#cbd5f5",
                      marginBottom: 4,
                    }}
                  >
                    {path}
                  </div>
                  <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13 }}>
                    {issues.map((issue, idx) => (
                      <li key={idx}>{issue}</li>
                    ))}
                  </ul>
                </div>
              ) : null
            )}
          </div>
        </div>
      )}
    </div>
  );
}
