import { useState, useRef, useEffect } from "react";

// ─── palette & font via injected style ───────────────────────────────────────
const GLOBAL_STYLE = `
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:ital,wght@0,400;0,500;1,400&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:       #0a0b0f;
    --surface:  #111318;
    --border:   #1e2130;
    --accent:   #7c6af7;
    --accent2:  #3ecfcf;
    --warn:     #f76c6c;
    --text:     #e8e9f0;
    --muted:    #6b6e85;
    --code-bg:  #0e1016;
  }

  body { background: var(--bg); color: var(--text);
         font-family: 'Syne', sans-serif; }

  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0);    }
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;

// ─── tiny helpers ─────────────────────────────────────────────────────────────
const Badge = ({ label, color = "var(--accent)" }) => (
  <span style={{
    background: color + "22", color, border: `1px solid ${color}44`,
    borderRadius: 4, fontSize: 11, fontWeight: 700, padding: "2px 8px",
    fontFamily: "'DM Mono', monospace", letterSpacing: "0.06em",
    textTransform: "uppercase",
  }}>{label}</span>
);

const Spinner = () => (
  <span style={{
    display: "inline-block", width: 16, height: 16,
    border: "2px solid var(--border)", borderTopColor: "var(--accent)",
    borderRadius: "50%", animation: "spin 0.7s linear infinite",
  }} />
);

const FILE_TYPE_COLOR = {
  PDF: "#f7b86c", VIDEO: "#6cf7a8", AUDIO: "#f76c6c", TEXT: "var(--accent2)",
};

// ─── sidebar entry ────────────────────────────────────────────────────────────
function SourceEntry({ src, active, onClick }) {
  const icons = { PDF: "📄", VIDEO: "🎬", AUDIO: "🎵", TEXT: "📝" };
  return (
    <button onClick={onClick} style={{
      width: "100%", textAlign: "left", padding: "10px 14px",
      background: active ? "var(--accent)18" : "transparent",
      border: "none", borderRadius: 8,
      borderLeft: active ? "2px solid var(--accent)" : "2px solid transparent",
      cursor: "pointer", transition: "all 0.15s",
      display: "flex", alignItems: "center", gap: 10,
    }}>
      <span style={{ fontSize: 16 }}>{icons[src.type] || "📁"}</span>
      <span style={{
        flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
        fontSize: 13, color: active ? "var(--text)" : "var(--muted)",
        fontWeight: active ? 700 : 400,
      }}>{src.name}</span>
      <Badge label={src.type} color={FILE_TYPE_COLOR[src.type]} />
    </button>
  );
}

// ─── drop zone ────────────────────────────────────────────────────────────────
function DropZone({ onFiles }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef();

  const handle = (files) => {
    if (!files?.length) return;
    
    const accepted = [];
    const allowedExtensions = ["mp4","mov","avi","mkv","mp3","wav","m4a","pdf","txt","md","docx"];

    Array.from(files).forEach(f => {
      const ext = f.name.split(".").pop().trim().toLowerCase();
      console.log(`[DropZone Verification] Reading file: "${f.name}" | Extracted Extension: "${ext}"`);
      
      if (allowedExtensions.includes(ext)) {
        accepted.push(f);
      } else {
        console.warn(`[DropZone Ignored] File "${f.name}" rejected. Extension "${ext}" is not in the allowed list.`);
      }
    });

    if (accepted.length === 0) {
      console.error("❌ [Pipeline Aborted] No acceptable source files remain after verification filters.");
      alert("Unsupported file format layout detected. Please verify your file name extension format standard.");
      return;
    }

    onFiles(accepted);
  };

  return (
    <div
      onClick={() => inputRef.current.click()}
      onDragOver={e => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={e => { e.preventDefault(); setDragging(false); handle(e.dataTransfer.files); }}
      style={{
        border: `1.5px dashed ${dragging ? "var(--accent)" : "var(--border)"}`,
        borderRadius: 12, padding: "28px 20px", textAlign: "center",
        cursor: "pointer", transition: "all 0.2s",
        background: dragging ? "var(--accent)0a" : "transparent",
      }}
    >
      <div style={{ fontSize: 28, marginBottom: 8 }}>⬆</div>
      <div style={{ fontSize: 13, color: "var(--muted)" }}>
        Drop files or <span style={{ color: "var(--accent)" }}>browse</span>
      </div>
      <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 4 }}>
        .mp4 · .mp3 · .pdf · .docx · .txt
      </div>
      <input ref={inputRef} type="file" multiple style={{ display: "none" }}
        accept=".mp4,.mov,.avi,.mkv,.mp3,.wav,.m4a,.pdf,.txt,.md,.docx"
        onChange={e => handle(e.target.files)} />
    </div>
  );
}

// ─── chunk card ───────────────────────────────────────────────────────────────
function ChunkCard({ chunk, delay }) {
  return (
    <div style={{
      background: "var(--surface)", border: "1px solid var(--border)",
      borderRadius: 10, padding: "14px 16px", marginBottom: 10,
      animation: `fadeUp 0.3s ease both`, animationDelay: `${delay}ms`,
    }}>
      <div style={{
        display: "flex", alignItems: "center", gap: 8, marginBottom: 8,
      }}>
        <span style={{ fontFamily: "'DM Mono',monospace", fontSize: 11,
          color: "var(--accent)", background: "var(--accent)18",
          padding: "2px 8px", borderRadius: 4 }}>
          chunk_id: {chunk.id.slice(0, 8)}…
        </span>
        {chunk.similarity && (
          <span style={{ fontFamily: "'DM Mono',monospace", fontSize: 11,
            color: "var(--accent2)", background: "var(--accent2)18",
            padding: "2px 8px", borderRadius: 4 }}>
            sim: {chunk.similarity}
          </span>
        )}
        {chunk.hasImage && (
          <span style={{ fontSize: 11, color: "var(--muted)" }}>🖼 keyframe</span>
        )}
      </div>
      <div style={{ fontSize: 13, color: "var(--muted)", lineHeight: 1.6,
        fontFamily: "'DM Mono',monospace" }}>
        {chunk.text}
      </div>
      {chunk.timeRange && (
        <div style={{ marginTop: 6, fontSize: 11, color: "var(--muted)" }}>
          ⏱ {chunk.timeRange}
        </div>
      )}
    </div>
  );
}

// ─── markdown renderer ───────────────────────────────────────────────────────
function MarkdownView({ content }) {
  const lines = content.split("\n");
  const elements = [];
  let inCode = false;
  let codeLines = [];
  let codeKey = 0;

  const flush = () => {
    if (codeLines.length) {
      elements.push(
        <pre key={`code-${codeKey++}`} style={{
          background: "var(--code-bg)", border: "1px solid var(--border)",
          borderRadius: 8, padding: "12px 16px", overflowX: "auto",
          fontFamily: "'DM Mono',monospace", fontSize: 12.5, color: "#a8d8b0",
          marginBottom: 12, lineHeight: 1.6,
        }}>{codeLines.join("\n")}</pre>
      );
      codeLines = [];
    }
  };

  lines.forEach((line, i) => {
    if (line.startsWith("```")) {
      if (inCode) { flush(); inCode = false; }
      else inCode = true;
      return;
    }
    if (inCode) { codeLines.push(line); return; }

    const imgMatch = line.match(/!\[([^\]]*)\]\(([^)]+)\)/);
    if (imgMatch) {
      // Resolve paths so they hook cleanly into our backend port 8000 mount route
      const cleanImgPath = imgMatch[2].startsWith(".") ? imgMatch[2].slice(1) : imgMatch[2];
      elements.push(
        <div key={i} style={{
          background: "var(--surface)", border: "1px solid var(--border)",
          borderRadius: 8, padding: "12px 16px", marginBottom: 14,
        }}>
          <div style={{ fontSize: 12, color: "var(--accent2)", fontWeight: 700, marginBottom: 8 }}>
            🖼 {imgMatch[1] || "Extracted Keyframe Diagram Reference"}
          </div>
          <img 
            src={cleanImgPath} 
            alt={imgMatch[1]} 
            style={{ width: "100%", borderRadius: 6, border: "1px solid var(--border)", background: "#000" }} 
          />
        </div>
      );
      return;
    }

    if (line.startsWith("### ")) {
      elements.push(<h3 key={i} style={{ fontSize: 15, fontWeight: 700, color: "var(--accent2)", marginBottom: 6, marginTop: 16 }}>{line.slice(4)}</h3>);
    } else if (line.startsWith("## ")) {
      elements.push(<h2 key={i} style={{ fontSize: 17, fontWeight: 800, color: "var(--text)", marginBottom: 8, marginTop: 20 }}>{line.slice(3)}</h2>);
    } else if (line.startsWith("# ")) {
      elements.push(<h1 key={i} style={{ fontSize: 22, fontWeight: 800, marginBottom: 10, marginTop: 24, color: "var(--text)" }}>{line.slice(2)}</h1>);
    } else if (line.startsWith("> ")) {
      elements.push(
        <blockquote key={i} style={{
          borderLeft: "3px solid var(--accent)", paddingLeft: 14,
          color: "var(--muted)", fontSize: 14, marginBottom: 8, fontStyle: "italic",
        }}>{line.slice(2)}</blockquote>
      );
    } else if (line.startsWith("- ")) {
      elements.push(
        <div key={i} style={{ display: "flex", gap: 8, marginBottom: 4, fontSize: 14, lineHeight: 1.6 }}>
          <span style={{ color: "var(--accent)", marginTop: 2 }}>▸</span>
          <span>{line.slice(2)}</span>
        </div>
      );
    } else if (line.trim() === "") {
      elements.push(<div key={i} style={{ height: 8 }} />);
    } else {
      elements.push(
        <p key={i} style={{ fontSize: 14, lineHeight: 1.7, marginBottom: 6, color: "var(--text)" }}>
          {line}
        </p>
      );
    }
  });
  flush();
  return <div>{elements}</div>;
}

// ─── pipeline status step ────────────────────────────────────────────────────
function PipelineStep({ label, status, detail }) {
  const statusIcon = { done: "✓", active: <Spinner />, pending: "○", error: "✕" };
  const statusColor = { done: "var(--accent2)", active: "var(--accent)", pending: "var(--muted)", error: "var(--warn)" };
  return (
    <div style={{
      display: "flex", alignItems: "flex-start", gap: 12, padding: "8px 0",
      borderBottom: "1px solid var(--border)",
    }}>
      <div style={{
        width: 24, height: 24, borderRadius: "50%",
        background: statusColor[status] + "22",
        border: `1.5px solid ${statusColor[status]}`,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 11, color: statusColor[status], flexShrink: 0, marginTop: 1,
      }}>
        {statusIcon[status]}
      </div>
      <div>
        <div style={{ fontSize: 13, fontWeight: 600, color: statusColor[status] }}>{label}</div>
        {detail && <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 2, fontFamily: "'DM Mono',monospace" }}>{detail}</div>}
      </div>
    </div>
  );
}

// ─── main app ─────────────────────────────────────────────────────────────────
export default function App() {
  const [sources, setSources] = useState([
    { id: "s1", name: "ML_Lecture_Week3.mp4", type: "VIDEO", chunks: 14, status: "indexed" },
    { id: "s2", name: "Research_Paper_Transformers.pdf", type: "PDF", chunks: 32, status: "indexed" },
    { id: "s3", name: "Lecture_Audio_Ch5.mp3", type: "AUDIO", chunks: 8, status: "indexed" },
  ]);
  const [activeSource, setActiveSource] = useState("s1");
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState("notes");
  const [loading, setLoading] = useState(false);
  const [output, setOutput] = useState("");
  const [activeTab, setActiveTab] = useState("generate");
  const [pipeline, setPipeline] = useState([]);
  const [chunks, setChunks] = useState([]);
  const [ingesting, setIngesting] = useState(false);

  // Load contextual shards mapped from the dynamic database layer
  useEffect(() => {
    const mockChunks = Array.from({ length: 6 }, (_, i) => ({
      id: `chunk-${activeSource}-${i}`,
      text: [
        "The attention mechanism allows the model to focus on different parts of the input sequence, enabling long-range dependencies.",
        "Multi-head attention splits the representation into multiple heads, each learning different relational aspects of the data.",
        "Positional encodings inject sequence order information, compensating for the permutation-invariant nature of self-attention.",
        "The feed-forward sublayer applies two linear transformations with a ReLU activation, acting as a per-position MLP.",
        "Layer normalization stabilizes training by normalizing activations across the feature dimension rather than the batch.",
        "Residual connections allow gradients to flow unimpeded through deep stacks, preventing vanishing gradient issues.",
      ][i],
      hasImage: [false, true, false, false, true, false][i],
      timeRange: activeSource === "s1" ? `${i * 4}s – ${i * 4 + 4}s` : null,
      similarity: null,
    }));
    setChunks(mockChunks);
  }, [activeSource]);

  // FIXED: Direct absolute routing to port 8000 to bypass Windows localhost loop issues
  const runGenerate = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setOutput("");
    setActiveTab("generate");

    try {
      console.log("[Network Dispatch] Requesting RAG generation from absolute server gateway...");
      const response = await fetch("http://127.0.0.1:8000/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query, mode: mode }),
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP bad gateway response: ${response.status}`);
      }

      const data = await response.json();
      setOutput(data.result);
      
      if (data.chunks) {
        setChunks(data.chunks);
      }
    } catch (err) {
      console.error("🚨 [Generate Failed] Network exception caught:", err);
      setOutput(`> ✕ **Backend Pipeline Connection Error:** ${err.message}\nMake sure your ASGI Uvicorn server is running on port 8000.`);
    } finally {
      setLoading(false);
    }
  };

  // FIXED: Direct absolute routing link for multi-part document drops
  const handleFiles = async (files) => {
    if (!files.length) return;
    setIngesting(true);
    setActiveTab("pipeline");

    const ext = files[0].name.split(".").pop().toLowerCase();
    const typeMap = { mp4:"VIDEO", mov:"VIDEO", avi:"VIDEO", mkv:"VIDEO",
                      mp3:"AUDIO", wav:"AUDIO", m4a:"AUDIO",
                      pdf:"PDF", txt:"TEXT", md:"TEXT", docx:"TEXT" };
    const ftype = typeMap[ext] || "TEXT";

    const stepTemplates = [
      { label: "File validation & SourceID generation", detail: files[0].name },
      { label: "Temporal downsampling (1 FPS gate)", detail: ftype === "VIDEO" ? "cv2.VideoCapture → modulo filter" : "N/A – text path" },
      { label: "Grid-based motion analysis", detail: ftype === "VIDEO" ? "3×3 absdiff, threshold 15.0" : "skipped" },
      { label: "pHash clustering (Hamming ≤ 4)", detail: ftype === "VIDEO" ? "ImageDeduplicator" : "skipped" },
      { label: "Laplacian sharpness selection", detail: ftype === "VIDEO" ? "cv2.Laplacian.var()" : "skipped" },
      { label: "Gemini Embedding 2 (3,072-dim)", detail: "multimodal vector generation" },
      { label: "ChromaDB upsert", detail: "cosine similarity index" },
      { label: "SQLite metadata commit", detail: "sources + chunks + visual_aids" },
    ];
    setPipeline(stepTemplates.map(s => ({ ...s, status: "pending" })));

    const formData = new FormData();
    formData.append("file", files[0]);

    // Track steps sequentially via animated ticks while processing tasks
    let animationInterval = setInterval(() => {
      setPipeline(prev => {
        const activeIdx = prev.findIndex(s => s.status === "active" || s.status === "pending");
        if (activeIdx === -1) return prev;
        return prev.map((s, idx) => ({
          ...s,
          status: idx < activeIdx ? "done" : idx === activeIdx ? "active" : "pending"
        }));
      });
    }, 600);

    try {
      console.log(`[Network Dispatch] Shipping multi-part payload for "${files[0].name}" directly to port 8000...`);
      const response = await fetch("http://127.0.0.1:8000/api/ingest", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error(`File ingestion transaction failed with status code ${response.status}`);
      const resultData = await response.json();

      console.log("[Network Success] Ingestion response compiled:", resultData);
      clearInterval(animationInterval);
      setPipeline(stepTemplates.map(s => ({ ...s, status: "done" })));

      const newSrc = {
        id: resultData.source_id || `s${Date.now()}`,
        name: files[0].name,
        type: ftype,
        chunks: resultData.chunks || 0,
        status: "indexed",
      };
      setSources(prev => [newSrc, ...prev]);
      setActiveSource(newSrc.id);
    } catch (err) {
      clearInterval(animationInterval);
      console.error("🚨 [Ingest Failed] Fetch pipeline exception caught:", err);
      setPipeline(prev => prev.map(s => s.status === "active" ? { ...s, status: "error", detail: err.message } : s));
    } finally {
      setIngesting(false);
    }
  };

  const activeSrc = sources.find(s => s.id === activeSource);

  return (
    <>
      <style>{GLOBAL_STYLE}</style>
      <div style={{ display: "flex", height: "100vh", overflow: "hidden" }}>

        {/* ── Sidebar ──────────────────────────────────────────── */}
        <aside style={{
          width: 260, background: "var(--surface)",
          borderRight: "1px solid var(--border)",
          display: "flex", flexDirection: "column",
          flexShrink: 0,
        }}>
          <div style={{
            padding: "20px 18px 14px",
            borderBottom: "1px solid var(--border)",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{
                width: 32, height: 32, borderRadius: 8,
                background: "linear-gradient(135deg, var(--accent), var(--accent2))",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 16,
              }}>◈</div>
              <div>
                <div style={{ fontWeight: 800, fontSize: 15, letterSpacing: "-0.02em" }}>
                  NoteForge
                </div>
                <div style={{ fontSize: 11, color: "var(--muted)" }}>knowledge pipeline</div>
              </div>
            </div>
          </div>

          <div style={{ padding: "14px 14px 10px" }}>
            <DropZone onFiles={handleFiles} />
          </div>

          <div style={{
            flex: 1, overflowY: "auto", padding: "0 10px 10px",
          }}>
            <div style={{
              fontSize: 10, fontWeight: 700, color: "var(--muted)",
              letterSpacing: "0.1em", textTransform: "uppercase",
              padding: "10px 6px 6px",
            }}>Knowledge Base · {sources.length}</div>
            {sources.map(s => (
              <SourceEntry key={s.id} src={s}
                active={s.id === activeSource}
                onClick={() => { setActiveSource(s.id); setOutput(""); setActiveTab("chunks"); }} />
            ))}
          </div>

          <div style={{
            padding: "12px 16px", borderTop: "1px solid var(--border)",
            display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10,
          }}>
            {[
              ["Chunks", sources.reduce((a, s) => a + s.chunks, 0)],
              ["Sources", sources.length],
            ].map(([label, val]) => (
              <div key={label} style={{
                background: "var(--bg)", borderRadius: 8, padding: "8px 10px",
              }}>
                <div style={{ fontSize: 18, fontWeight: 800 }}>{val}</div>
                <div style={{ fontSize: 10, color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>{label}</div>
              </div>
            ))}
          </div>
        </aside>

        {/* ── Main ─────────────────────────────────────────────── */}
        <main style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>

          <div style={{
            padding: "14px 24px", borderBottom: "1px solid var(--border)",
            display: "flex", alignItems: "center", gap: 16, background: "var(--surface)",
          }}>
            {activeSrc && (
              <>
                <span style={{ fontSize: 18 }}>{
                  { PDF: "📄", VIDEO: "🎬", AUDIO: "🎵", TEXT: "📝" }[activeSrc.type]
                }</span>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 14 }}>{activeSrc.name}</div>
                  <div style={{ fontSize: 11, color: "var(--muted)" }}>
                    {activeSrc.chunks} chunks · {activeSrc.status}
                  </div>
                </div>
                <Badge label={activeSrc.type} color={FILE_TYPE_COLOR[activeSrc.type]} />
              </>
            )}
            <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
              {["generate", "chunks", "pipeline"].map(tab => (
                <button key={tab} onClick={() => setActiveTab(tab)} style={{
                  padding: "6px 14px", borderRadius: 6, cursor: "pointer",
                  border: "1px solid var(--border)",
                  background: activeTab === tab ? "var(--accent)22" : "transparent",
                  color: activeTab === tab ? "var(--accent)" : "var(--muted)",
                  fontSize: 12, fontWeight: 600, fontFamily: "'Syne',sans-serif",
                  textTransform: "capitalize",
                }}>
                  {tab}
                </button>
              ))}
            </div>
          </div>

          <div style={{ flex: 1, overflowY: "auto", padding: 24 }}>

            {activeTab === "generate" && (
              <div style={{ maxWidth: 780, margin: "0 auto", animation: "fadeUp 0.3s ease" }}>
                <div style={{
                  background: "var(--surface)", border: "1px solid var(--border)",
                  borderRadius: 12, padding: 16, marginBottom: 20,
                }}>
                  <div style={{ display: "flex", gap: 10, marginBottom: 12 }}>
                    {["notes", "quiz"].map(m => (
                      <button key={m} onClick={() => setMode(m)} style={{
                        padding: "5px 16px", borderRadius: 6, cursor: "pointer",
                        border: "1px solid var(--border)",
                        background: mode === m ? "var(--accent)" : "transparent",
                        color: mode === m ? "#fff" : "var(--muted)",
                        fontSize: 12, fontWeight: 700, fontFamily: "'Syne',sans-serif",
                        textTransform: "capitalize", transition: "all 0.15s",
                      }}>{mode === m && "◈ "}{m}</button>
                    ))}
                  </div>
                  <div style={{ display: "flex", gap: 10 }}>
                    <input
                      value={query}
                      onChange={e => setQuery(e.target.value)}
                      onKeyDown={e => e.key === "Enter" && runGenerate()}
                      placeholder="Ask about your documents…"
                      style={{
                        flex: 1, background: "var(--bg)",
                        border: "1px solid var(--border)", borderRadius: 8,
                        padding: "10px 14px", color: "var(--text)",
                        fontSize: 14, fontFamily: "'Syne',sans-serif",
                        outline: "none",
                      }}
                    />
                    <button onClick={runGenerate} disabled={loading || !query.trim()} style={{
                      padding: "10px 20px", borderRadius: 8, cursor: loading ? "default" : "pointer",
                      border: "none", background: "var(--accent)",
                      color: "#fff", fontSize: 13, fontWeight: 700,
                      fontFamily: "'Syne',sans-serif",
                      opacity: loading || !query.trim() ? 0.5 : 1,
                      display: "flex", alignItems: "center", gap: 8, transition: "opacity 0.15s",
                    }}>
                      {loading ? <Spinner /> : "▶"} {mode === "quiz" ? "Quiz" : "Notes"}
                    </button>
                  </div>
                  {loading && (
                    <div style={{
                      marginTop: 10, fontSize: 11, color: "var(--accent)",
                      display: "flex", alignItems: "center", gap: 6,
                      fontFamily: "'DM Mono',monospace",
                    }}>
                      <span style={{ animation: "pulse 1s infinite" }}>●</span>
                      Embedding query → Chroma cosine search → LLM synthesis…
                    </div>
                  )}
                </div>

                {output && (
                  <div style={{
                    background: "var(--surface)", border: "1px solid var(--border)",
                    borderRadius: 12, padding: "20px 24px",
                    animation: "fadeUp 0.3s ease",
                  }}>
                    <MarkdownView content={output} />
                    {loading && (
                      <span style={{
                        display: "inline-block", width: 2, height: 16,
                        background: "var(--accent)", animation: "pulse 0.8s infinite",
                        verticalAlign: "middle",
                      }} />
                    )}
                  </div>
                )}
              </div>
            )}

            {activeTab === "chunks" && (
              <div style={{ maxWidth: 720, margin: "0 auto", animation: "fadeUp 0.3s ease" }}>
                <div style={{
                  fontSize: 11, color: "var(--muted)", marginBottom: 16,
                  fontFamily: "'DM Mono',monospace",
                  background: "var(--surface)", border: "1px solid var(--border)",
                  borderRadius: 8, padding: "10px 14px",
                }}>
                  <span style={{ color: "var(--accent)" }}>SELECT</span> * <span style={{ color: "var(--accent)" }}>FROM</span> chunks{" "}
                  <span style={{ color: "var(--accent)" }}>WHERE</span> source_id = <span style={{ color: "var(--accent2)" }}>'{activeSource}'</span>{" "}
                  <span style={{ color: "var(--accent)" }}>ORDER BY</span> start_seconds
                </div>
                {chunks.map((c, i) => (
                  <ChunkCard key={c.id} chunk={c} delay={i * 60} />
                ))}
              </div>
            )}

            {activeTab === "pipeline" && (
              <div style={{ maxWidth: 600, margin: "0 auto", animation: "fadeUp 0.3s ease" }}>
                <div style={{
                  background: "var(--surface)", border: "1px solid var(--border)",
                  borderRadius: 12, padding: "20px 24px",
                }}>
                  <div style={{ fontWeight: 800, fontSize: 15, marginBottom: 4 }}>Ingestion Pipeline</div>
                  <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 20 }}>
                    Drop a file to watch the pipeline execute
                  </div>
                  {pipeline.length === 0 ? (
                    <div style={{ color: "var(--muted)", fontSize: 13, textAlign: "center", padding: "30px 0" }}>
                      No active ingestion. Upload a file to begin.
                    </div>
                  ) : (
                    pipeline.map((step, i) => (
                      <PipelineStep key={i} label={step.label}
                        status={step.status} detail={step.detail} />
                    ))
                  )}
                  {pipeline.length > 0 && pipeline.every(s => s.status === "done") && (
                    <div style={{
                      marginTop: 16, padding: "10px 16px",
                      background: "var(--accent2)15", border: "1px solid var(--accent2)33",
                      borderRadius: 8, fontSize: 13, color: "var(--accent2)", fontWeight: 600,
                      animation: "fadeUp 0.3s ease",
                    }}>
                      ✓ Ingestion complete — source indexed and ready to query
                    </div>
                  )}
                </div>

                <div style={{
                  marginTop: 20, background: "var(--surface)",
                  border: "1px solid var(--border)", borderRadius: 12, padding: "20px 24px",
                }}>
                  <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 16 }}>
                    System Architecture
                  </div>
                  {[
                    { phase: "Phase 1", label: "Data Ingestion", tag: "CPU LOCAL", color: "#f7b86c",
                      detail: "VideoProcessor (1 FPS, 480×270) → Grid Motion Detector → ImageDeduplicator (pHash + Laplacian)" },
                    { phase: "Phase 2", label: "Vector Indexing", tag: "HYBRID", color: "var(--accent)",
                      detail: "Gemini Embedding 2 API → 3,072-dim vectors → ChromaDB (cosine) + SQLite metadata" },
                    { phase: "Phase 3", label: "Generative Interface", tag: "CLOUD", color: "var(--accent2)",
                      detail: "Chroma semantic search → RAG context assembly → Groq / OpenRouter → Markdown output" },
                  ].map(p => (
                    <div key={p.phase} style={{
                      display: "flex", gap: 14, padding: "12px 0",
                      borderBottom: "1px solid var(--border)",
                    }}>
                      <div style={{
                        width: 6, borderRadius: 3, flexShrink: 0,
                        background: p.color,
                      }} />
                      <div style={{ flex: 1 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                          <span style={{ fontSize: 11, color: "var(--muted)", fontFamily: "'DM Mono',monospace" }}>{p.phase}</span>
                          <span style={{ fontSize: 13, fontWeight: 700 }}>{p.label}</span>
                          <Badge label={p.tag} color={p.color} />
                        </div>
                        <div style={{ fontSize: 12, color: "var(--muted)", lineHeight: 1.6 }}>{p.detail}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </>
  );
}