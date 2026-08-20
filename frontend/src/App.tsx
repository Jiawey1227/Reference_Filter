import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  cancelJob,
  createJob,
  downloadUrl,
  getJob,
  getProvider,
  JobStatus,
  ProviderInfo,
  testApiKey
} from "./api";

const RUN_MODES = [
  { value: "full", label: "完整运行" },
  { value: "embedding_only", label: "仅 embedding" },
  { value: "llm_only", label: "仅 LLM" }
] as const;

export function App() {
  const [provider, setProvider] = useState<ProviderInfo | null>({
    provider: "Qwen / DashScope",
    base_url: "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    embedding_model: "text-embedding-v4",
    llm_model: "qwen3.6-flash",
    embedding_max_batch_size: 10
  });
  const [apiKey, setApiKey] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [runMode, setRunMode] = useState("full");
  const [batchSize, setBatchSize] = useState(100);
  const [delay, setDelay] = useState(0);
  const [llmMinScore, setLlmMinScore] = useState(0.25);
  const [llmMaxScore, setLlmMaxScore] = useState(0.35);
  const [topic, setTopic] = useState("");
  const [job, setJob] = useState<JobStatus | null>(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [testing, setTesting] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const isActive = job?.status === "queued" || job?.status === "running";

  useEffect(() => {
    getProvider().then(setProvider).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!job || !isActive) return;
    const timer = window.setInterval(() => {
      getJob(job.id).then(setJob).catch((err) => setError(err.message));
    }, 1200);
    return () => window.clearInterval(timer);
  }, [job, isActive]);

  const statusTone = useMemo(() => {
    if (!job) return "idle";
    if (job.status === "completed") return "success";
    if (job.status === "failed") return "danger";
    if (job.status === "cancelled") return "warning";
    return "active";
  }, [job]);

  async function handleTestKey() {
    setError("");
    setNotice("");
    setTesting(true);
    try {
      await testApiKey(apiKey);
      setNotice("连接测试成功");
    } catch (err) {
      setError(err instanceof Error ? err.message : "连接测试失败");
    } finally {
      setTesting(false);
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setNotice("");
    if (!file) {
      setError("请选择 Excel 文件");
      return;
    }
    const form = new FormData();
    form.append("file", file);
    form.append("api_key", apiKey);
    form.append("topic", topic);
    form.append("run_mode", runMode);
    form.append("batch_size", String(batchSize));
    form.append("delay", String(delay));
    form.append("llm_min_score", String(llmMinScore));
    form.append("llm_max_score", String(llmMaxScore));

    setSubmitting(true);
    try {
      const created = await createJob(form);
      setJob(created);
      setNotice("任务已创建");
    } catch (err) {
      setError(err instanceof Error ? err.message : "任务创建失败");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCancel() {
    if (!job) return;
    setError("");
    try {
      setJob(await cancelJob(job.id));
      setNotice("已请求取消任务");
    } catch (err) {
      setError(err instanceof Error ? err.message : "取消失败");
    }
  }

  return (
    <main className="app">
      <section className="workspace" aria-label="AI 文献评分工作台">
        <header className="topbar">
          <div>
            <h1>AI 文献评分工具</h1>
            <p>本地 Web 工作台，固定使用 Qwen / DashScope。</p>
          </div>
          <div className={`status-pill ${statusTone}`}>
            {job ? job.status : "ready"}
          </div>
        </header>

        <div className="layout">
          <form className="panel form-panel" onSubmit={handleSubmit}>
            <section className="field-group">
              <div className="section-head">
                <h2>运行配置</h2>
                <button type="button" className="secondary" onClick={handleTestKey} disabled={testing || isActive}>
                  {testing ? "测试中" : "测试连接"}
                </button>
              </div>

              <label>
                <span>DashScope API Key</span>
                <input
                  value={apiKey}
                  type="password"
                  autoComplete="off"
                  onChange={(event) => setApiKey(event.target.value)}
                  disabled={isActive}
                  required
                />
              </label>

              <label>
                <span>Excel 文件</span>
                <input
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                  disabled={isActive}
                  required
                />
              </label>

              <div className="mode-row" role="radiogroup" aria-label="运行模式">
                {RUN_MODES.map((mode) => (
                  <label className="mode-option" key={mode.value}>
                    <input
                      type="radio"
                      name="run-mode"
                      value={mode.value}
                      checked={runMode === mode.value}
                      onChange={() => setRunMode(mode.value)}
                      disabled={isActive}
                    />
                    <span>{mode.label}</span>
                  </label>
                ))}
              </div>
            </section>

            <section className="field-group two-col">
              <label>
                <span>批处理大小</span>
                <input
                  type="number"
                  min={1}
                  value={batchSize}
                  onChange={(event) => setBatchSize(Number(event.target.value))}
                  disabled={isActive}
                />
              </label>
              <label>
                <span>请求间隔 秒</span>
                <input
                  type="number"
                  min={0}
                  step={0.1}
                  value={delay}
                  onChange={(event) => setDelay(Number(event.target.value))}
                  disabled={isActive}
                />
              </label>
              <label>
                <span>LLM 最低分</span>
                <input
                  type="number"
                  step={0.01}
                  value={llmMinScore}
                  onChange={(event) => setLlmMinScore(Number(event.target.value))}
                  disabled={isActive}
                />
              </label>
              <label>
                <span>LLM 最高分</span>
                <input
                  type="number"
                  step={0.01}
                  value={llmMaxScore}
                  onChange={(event) => setLlmMaxScore(Number(event.target.value))}
                  disabled={isActive}
                />
              </label>
            </section>

            <section className="field-group">
              <label>
                <span>研究主题</span>
                <textarea
                  value={topic}
                  onChange={(event) => setTopic(event.target.value)}
                  disabled={isActive}
                  required
                  rows={7}
                />
              </label>
            </section>

            <div className="actions">
              <button type="submit" className="primary" disabled={submitting || isActive}>
                {submitting ? "创建中" : "开始处理"}
              </button>
              <button type="button" className="secondary" onClick={handleCancel} disabled={!isActive}>
                取消任务
              </button>
              {job?.download_ready && (
                <a className="download" href={downloadUrl(job.id)}>
                  下载结果
                </a>
              )}
            </div>
          </form>

          <aside className="panel insight-panel">
            <section className="provider-strip">
              <h2>固定模型</h2>
              <dl>
                <div>
                  <dt>Provider</dt>
                  <dd>{provider?.provider ?? "Qwen / DashScope"}</dd>
                </div>
                <div>
                  <dt>Embedding</dt>
                  <dd>{provider?.embedding_model ?? "text-embedding-v4"}</dd>
                </div>
                <div>
                  <dt>LLM</dt>
                  <dd>{provider?.llm_model ?? "qwen3.6-flash"}</dd>
                </div>
                <div>
                  <dt>Embedding batch</dt>
                  <dd>最多 {provider?.embedding_max_batch_size ?? 10} 条/请求</dd>
                </div>
              </dl>
            </section>

            <section className="progress-block">
              <h2>任务状态</h2>
              <div className="progress-track">
                <div className="progress-fill" style={{ width: `${job?.progress ?? 0}%` }} />
              </div>
              <div className="progress-meta">
                <span>{job?.message ?? "等待开始"}</span>
                <strong>{job ? `${job.progress}%` : "0%"}</strong>
              </div>
              {notice && <p className="notice">{notice}</p>}
              {(error || job?.error) && <p className="error">{error || job?.error}</p>}
            </section>

            <section className="log-block">
              <h2>日志</h2>
              <div className="logs" aria-live="polite">
                {(job?.logs.length ? job.logs : ["暂无日志"]).map((line, index) => (
                  <p key={`${line}-${index}`}>{line}</p>
                ))}
              </div>
            </section>
          </aside>
        </div>
      </section>
    </main>
  );
}
