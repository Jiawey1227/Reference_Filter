import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  cancelJob,
  continueJob,
  credentialAction,
  createJob,
  downloadUrl,
  getJob,
  JobStatus,
  testApiKey
} from "./api";

const PROFILE_KEY = "author-screening-calibration-v1";
type Calibration = { topic: string; lower: number; upper: number };
function readCalibration(): Calibration | null {
  try {
    const value = JSON.parse(localStorage.getItem(PROFILE_KEY) || "null");
    return value && typeof value.topic === "string" && value.topic.trim() &&
      Number.isFinite(value.lower) && Number.isFinite(value.upper) &&
      value.lower >= -1 && value.upper <= 1 && value.lower < value.upper ? value : null;
  } catch { return null; }
}
const RUN_MODES = [
  { value: "embedding_only", label: "1. Generate Scores for Calibration" },
  { value: "llm_only", label: "2. Review Borderline Records" },
  { value: "full", label: "3. Screen a New List" }
] as const;

export function App() {
  const [apiKey, setApiKey] = useState("");
  const [savedKey, setSavedKey] = useState(false);
  const [savingKey, setSavingKey] = useState(false);

  useEffect(() => {
    credentialAction("status").then(result => setSavedKey(result.saved)).catch(err => setError(err.message));
  }, []);

  async function handleCredential(action: "save" | "delete") {
    setSavingKey(true);
    setError("");
    try {
      const result = await credentialAction(action, apiKey);
      setSavedKey(result.saved);
      setApiKey("");
      setNotice(result.saved ? "API key saved in the system credential store." : "Saved API key removed.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Credential operation failed");
    } finally { setSavingKey(false); }
  }
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [calibration, setCalibration] = useState<Calibration | null>(readCalibration);
  const [runMode, setRunMode] = useState(calibration ? "full" : "embedding_only");
  const [llmMinScore, setLlmMinScore] = useState(calibration?.lower ?? 0.25);
  const [llmMaxScore, setLlmMaxScore] = useState(calibration?.upper ?? 0.35);
  const [affiliationEnabled, setAffiliationEnabled] = useState(false);
  const [affiliationKeywords, setAffiliationKeywords] = useState("");
  const [topic, setTopic] = useState(calibration?.topic ?? "");
  const [job, setJob] = useState<JobStatus | null>(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [testing, setTesting] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [submittedMode, setSubmittedMode] = useState("");
  const [scoredTopic, setScoredTopic] = useState("");

  function saveCalibration() {
    if (!topic.trim() || !Number.isFinite(llmMinScore) || !Number.isFinite(llmMaxScore) || llmMinScore < -1 || llmMaxScore > 1 || llmMinScore >= llmMaxScore) {
      setError("Enter a scope and valid lower / upper thresholds before confirming.");
      return;
    }
    try {
      const value = {topic, lower: llmMinScore, upper: llmMaxScore};
      localStorage.setItem(PROFILE_KEY, JSON.stringify(value));
      setCalibration(value);
      setNotice("Calibration saved on this browser. Future sessions will reuse this scope and thresholds.");
      setError("");
    } catch { setError("Could not save calibration in this browser."); }
  }

  async function continueToReview() {
    if (!job || submitting) return;
    if (!Number.isFinite(llmMinScore) || !Number.isFinite(llmMaxScore) || llmMinScore < -1 || llmMaxScore > 1 || llmMinScore >= llmMaxScore) {
      setError("Enter valid thresholds between -1 and 1, with lower below upper.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const next = await continueJob(job.id, llmMinScore, llmMaxScore);
      setJob(next);
      setRunMode("llm_only");
      setSubmittedMode("llm_only");
      setTopic(scoredTopic);
      const value = {topic: scoredTopic, lower: llmMinScore, upper: llmMaxScore};
      try {
        localStorage.setItem(PROFILE_KEY, JSON.stringify(value));
        setCalibration(value);
        setNotice("AI review started using the previous scores. Thresholds saved for this scope.");
      } catch { setNotice("AI review started. Browser storage is unavailable; thresholds were not saved."); }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start AI review");
    } finally { setSubmitting(false); }
  }

  const isActive = job?.status === "queued" || job?.status === "running";

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
      setNotice("Connection successful");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connection test failed");
    } finally {
      setTesting(false);
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setNotice("");
    if (runMode === "llm_only" && submittedMode === "embedding_only" && job?.download_ready) {
      await continueToReview();
      return;
    }
    if (!file) {
      setError("Please select an Excel file");
      return;
    }
    if (!Number.isFinite(llmMinScore) || !Number.isFinite(llmMaxScore) || llmMinScore < -1 || llmMaxScore > 1 || llmMinScore >= llmMaxScore) {
      setError("Thresholds must be between -1 and 1, with the lower threshold below the upper threshold");
      return;
    }
    if (affiliationEnabled && !affiliationKeywords.trim()) {
      setError("Enter affiliation keywords, one per line");
      return;
    }
    const form = new FormData();
    form.append("file", file);
    form.append("api_key", apiKey);
    form.append("topic", topic);
    form.append("affiliation_enabled", String(affiliationEnabled));
    form.append("affiliation_keywords", affiliationKeywords);
    form.append("run_mode", runMode);
    form.append("llm_min_score", String(llmMinScore));
    form.append("llm_max_score", String(llmMaxScore));

    setSubmitting(true);
    try {
      const created = await createJob(form);
      setJob(created);
      setScoredTopic(topic);
      setSubmittedMode(runMode);
      setNotice("Task created");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create task");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCancel() {
    if (!job) return;
    setError("");
    try {
      setJob(await cancelJob(job.id));
      setNotice("Cancellation requested");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not cancel task");
    }
  }

  return (
    <main className="app">
      <section className="workspace" aria-label="Author Screening Workspace">
        <header className="topbar">
          <div>
            <h1>Author Scope Screening</h1>
            <p>Upload an author list to screen research records against your scope.</p>
          </div>
          <div className={`status-pill ${statusTone}`}>
            {job ? job.status : "ready"}
          </div>
        </header>

        <div className="layout">
          <form id="screening-form" className="panel form-panel" onSubmit={handleSubmit}>
            <section className="field-group">
              <div className="section-head">
                <h2>Setup</h2>
                <button type="button" className="secondary" onClick={handleTestKey} disabled={testing || isActive}>
                  {testing ? "Testing..." : "Test Connection"}
                </button>
              </div>

              <label>
                <span>Alibaba Cloud Model Studio API Key</span>
                <input
                  value={apiKey}
                  type="password"
                  autoComplete="off"
                  placeholder={savedKey ? "Using saved API key — enter a new key to replace it" : "Enter your API key"}
                  onChange={(event) => setApiKey(event.target.value)}
                  disabled={isActive || savingKey}
                  required={!savedKey}
                />
              </label>

              <div className="actions">
                <button type="button" className="secondary" disabled={isActive || savingKey || !apiKey.trim()} onClick={() => handleCredential("save")}>{savingKey ? "Please wait..." : "Save API Key"}</button>
                <button type="button" className="secondary" disabled={isActive || savingKey || !savedKey} onClick={() => handleCredential("delete")}>Forget Saved Key</button>
              </div>
              <p>{savedKey ? "A saved key is available. Leave the field empty to use it." : "Saving is optional. Saved keys stay in this computer’s system credential store (macOS Keychain), not browser storage."}</p>

              <details>
                <summary>How do I get an API key?</summary>
                <ol>
                  <li>Sign in to Alibaba Cloud, complete any required account verification, and activate Model Studio.</li>
                  <li>Open the Model Studio console and select China (Beijing).</li>
                  <li>Create a pay-as-you-go API key on the API Key management page and copy it securely.</li>
                  <li>Paste it into the field above and click Test Connection.</li>
                </ol>
                <p>Use a Model Studio API key, not an Alibaba Cloud AccessKey or Coding Plan key. API usage may incur charges on your account. Keep your key private.</p>
                <a href="https://www.alibabacloud.com/help/en/model-studio/get-api-key" target="_blank" rel="noreferrer">Read the official guide</a>
              </details>

              <div className="file-field">
                <span id="excel-file-label">Excel File</span>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".xlsx,.xls"
                  hidden
                  aria-label="Choose an Excel file"
                  onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                  disabled={isActive}
                />
                <div className="file-picker">
                  <button type="button" className="secondary" disabled={isActive}
                    aria-describedby="excel-file-name" onClick={() => fileInputRef.current?.click()}>
                    Browse Files
                  </button>
                  <span id="excel-file-name" className="file-name" aria-live="polite">
                    {file?.name ?? "No file selected"}
                  </span>
                </div>
              </div>

              <p>Email and Article are required. Email identifies the scholar; Name is optional. Keywords and Abstract provide research context; Affiliation supports optional keyword highlighting. Country, H Index, and citations do not affect screening.</p>
              <div className="mode-row" role="radiogroup" aria-label="Run Mode">
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
                <span>Out-of-scope Threshold (Lower)</span>
                <input
                  type="number"
                  step="any"
                  min={-1}
                  max={1}
                  value={llmMinScore}
                  onChange={(event) => setLlmMinScore(Number(event.target.value))}
                  disabled={isActive}
                />
              </label>
              <label>
                <span>In-scope Threshold (Upper)</span>
                <input
                  type="number"
                  step="any"
                  min={-1}
                  max={1}
                  value={llmMaxScore}
                  onChange={(event) => setLlmMaxScore(Number(event.target.value))}
                  disabled={isActive}
                />
              </label>
            </section>

            <section className="field-group">
              <label>
                <span>Target Research Scope</span>
                <textarea
                  value={topic}
                  onChange={(event) => setTopic(event.target.value)}
                  disabled={isActive}
                  required
                  rows={7}
                />
              </label>
            </section>

            <section className="field-group">
              <p>Scores at or below the lower threshold are out of scope; scores at or above the upper threshold are in scope. Records between the thresholds receive AI review. Scores are not probabilities; calibrate thresholds using reviewed samples. Generate Scores Only does not produce a final scope decision.</p>
              <label className="mode-option">
                <input type="checkbox" checked={affiliationEnabled} onChange={(event) => setAffiliationEnabled(event.target.checked)} disabled={isActive} />
                <span>Highlight Matching Affiliations</span>
              </label>
              {affiliationEnabled && <label>
                <span>Affiliation Keywords — One per Line</span>
                <textarea rows={5} value={affiliationKeywords} onChange={(event) => setAffiliationKeywords(event.target.value)} disabled={isActive} required placeholder={"cardiology\ncardiovascular\nvascular"} />
                <small>Matching Affiliation cells are highlighted green in the Excel output. Any keyword can match, ignoring case; no automatic translation. Unmatched or missing affiliations remain uncolored and do not affect research decisions.</small>
              </label>}
            </section>

          </form>

          <aside className="panel insight-panel">
            <section className="progress-block">
              <h2>Task Status</h2>
              <div className="progress-track">
                <div className="progress-fill" style={{ width: `${job?.progress ?? 0}%` }} />
              </div>
              <div className="progress-meta">
                <span>{job?.message ?? "Ready to start"}</span>
                <strong>{job ? `${job.progress}%` : "0%"}</strong>
              </div>
              {notice && <p className="notice">{notice}</p>}
              {(error || job?.error) && <p className="error">{error || job?.error}</p>}
            </section>

            <section className="log-block">
              <h2>Activity Log</h2>
              <div className="logs" aria-live="polite">
                {(job?.logs.length ? job.logs : ["No activity yet"]).map((line, index) => (
                  <p key={`${line}-${index}`}>{line}</p>
                ))}
              </div>
            </section>
            <div className="actions">
              <button type="button" className="secondary" disabled={isActive} onClick={saveCalibration}>Confirm &amp; Save Thresholds</button>
              <button type="submit" form="screening-form" className="primary" disabled={submitting || isActive}>
                {submitting ? "Creating..." : "Start Processing"}
              </button>
              <button type="button" className="secondary" onClick={handleCancel} disabled={!isActive}>
                Cancel Task
              </button>
              {job?.download_ready && (
                <a className="download" href={downloadUrl(job.id)}>
                  Download Results
                </a>
              )}
              {job?.download_ready && submittedMode === "embedding_only" && <button type="button" className="primary" disabled={submitting || isActive} onClick={continueToReview}>{submitting ? "Starting..." : "Continue to AI Review"}</button>}
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}
