// =====================================================================
// h3-recovery.js — H3 任务找回插件（无限画布节点）
// 功能：展示 H3Queue 队列中的任务（排队/生成中/已完成/失败），
//       已完成任务内嵌视频预览 + 复制链接；页面刷新/关闭后结果不丢。
// 数据源：http://140.207.205.59:30101 （h3queue_server.py）
// =====================================================================

const RT = () => {
  const t = globalThis.InfiniteCanvasRuntime;
  if (!t) throw new Error("[h3-recovery] 无限画布运行时未就绪，请在画布宿主中加载本插件");
  return t;
};
const R = () => RT().React;
const useS = (...a) => R().useState(...a);
const useE = (...a) => R().useEffect(...a);
const FRAG = Symbol.for("infinite-canvas.jsx.fragment");
function h(type, props, ...rest) {
  const a = R();
  const l = type === FRAG ? a.Fragment : type;
  const s = { ...props ?? {} };
  if (rest.length === 1) s.children = rest[0];
  else if (rest.length > 1) s.children = rest;
  return a.createElement(l, s);
}

const H3Q = "http://140.207.205.59:30101";
const C = (v, d) => v || d; // 主题色兜底

// 事件拦截：避免画布把节点内交互当成拖拽/缩放
const EV = {
  onMouseDown: (e) => e.stopPropagation(),
  onPointerDown: (e) => e.stopPropagation(),
  onKeyDown: (e) => e.stopPropagation(),
  onWheel: (e) => e.stopPropagation(),
};

async function api(path, opts) {
  try {
    const r = await fetch(H3Q + path, opts);
    if (!r.ok) return null;
    return await r.json();
  } catch (e) { return null; }
}

function fmtTime(ts) {
  if (!ts) return "-";
  const d = new Date(ts * 1000);
  const p = (n) => String(n).padStart(2, "0");
  return p(d.getMonth() + 1) + "-" + p(d.getDate()) + " " + p(d.getHours()) + ":" + p(d.getMinutes());
}
function fmtDur(sec) {
  if (!(sec > 0)) return "";
  if (sec < 60) return Math.round(sec) + "秒";
  if (sec < 3600) return Math.floor(sec / 60) + "分" + Math.round(sec % 60) + "秒";
  return Math.floor(sec / 3600) + "时" + Math.round((sec % 3600) / 60) + "分";
}
function stateInfo(st) {
  if (st === "done") return { text: "已完成", color: "#22c55e" };
  if (st === "failed") return { text: "失败", color: "#ef4444" };
  if (st === "running") return { text: "生成中", color: "#f59e0b" };
  if (st === "queued") return { text: "排队中", color: "#3b82f6" };
  return { text: "已登记", color: "#8b5cf6" };
}

// ---------- 单张任务卡片 ----------
function TaskCard({ job, th, onAck, onCopy, copied }) {
  const st = stateInfo(job.state);
  const isDone = job.state === "done";
  const elapsed = job.updatedAt ? fmtDur(Date.now() / 1000 - job.updatedAt) : "";
  const url = job.resultUrl || (isDone ? "" : "");
  const prompt = String(job.prompt || "").slice(0, 90) + (String(job.prompt || "").length > 90 ? "…" : "");
  const kids = [];
  // 头部：状态 + 模型 + 时间
  kids.push(h("div", {
    key: "head", style: { display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" },
    children: [
      h("span", { key: "st", style: { background: st.color + "22", color: st.color, borderRadius: 4, padding: "1px 6px", fontSize: 11, fontWeight: 600 } }, st.text),
      h("span", { key: "m", style: { fontSize: 11, color: C(th.text, "#e5e7eb"), fontWeight: 600 } }, job.model || "未知模型"),
      h("span", { key: "t", style: { fontSize: 10, color: C(th.muted, "#9ca3af"), marginLeft: "auto" } },
        fmtTime(job.createdAt) + (elapsed && (job.state === "running" || job.state === "queued") ? " · 已等待" + elapsed : "")),
    ],
  }));
  // 提示词
  if (prompt) kids.push(h("div", { key: "p", style: { fontSize: 11, color: C(th.muted, "#9ca3af"), marginTop: 4, lineHeight: 1.5, wordBreak: "break-all" } }, prompt));
  // 失败原因
  if (job.state === "failed" && job.error) {
    kids.push(h("div", { key: "e", style: { fontSize: 11, color: "#f87171", marginTop: 4, lineHeight: 1.5, wordBreak: "break-all" } }, String(job.error).slice(0, 200)));
  }
  // 已完成：视频预览
  if (isDone && url) {
    kids.push(h("video", {
      key: "v", src: url, controls: true, preload: "metadata",
      style: { width: "100%", marginTop: 6, borderRadius: 6, background: "#000", maxHeight: 220, display: "block" },
    }));
  }
  // 已完成：链接 + 复制
  if (isDone && url) {
    kids.push(h("div", {
      key: "u", style: { display: "flex", gap: 6, alignItems: "center", marginTop: 6 },
      children: [
        h("input", { key: "i", readOnly: true, value: url, onFocus: (e) => e.target.select(),
          style: { flex: 1, minWidth: 0, fontSize: 10, padding: "3px 6px", borderRadius: 4, border: "1px solid " + C(th.faint, "#374151"), background: "transparent", color: C(th.muted, "#9ca3af") } }),
        h("button", { key: "c", onClick: () => onCopy(url), ...EV,
          style: { fontSize: 11, padding: "3px 10px", borderRadius: 4, border: "1px solid " + C(th.stroke, "#4b5563"), background: "transparent", color: C(th.text, "#e5e7eb"), cursor: "pointer" } },
          copied ? "已复制" : "复制"),
      ],
    }));
  }
  // 底部操作：不再显示
  kids.push(h("div", {
    key: "f", style: { display: "flex", justifyContent: "flex-end", marginTop: 6 },
    children: [h("button", { key: "a", onClick: () => onAck(job.taskId), ...EV,
      style: { fontSize: 11, padding: "2px 8px", borderRadius: 4, border: "none", background: "transparent", color: C(th.muted, "#9ca3af"), cursor: "pointer" } },
      isDone || job.state === "failed" ? "✓ 不再显示" : "隐藏")],
  }));
  return h("div", { style: { background: C(th.panel, "rgba(255,255,255,.05)"), border: "1px solid " + C(th.faint, "#374151"), borderRadius: 8, padding: 8, marginBottom: 8 }, children: kids });
}

// ---------- 节点主体 ----------
function RecoveryContent({ ctx }) {
  const th = ctx.theme.node;
  const [tasks, setTasks] = useS([]);
  const [ping, setPing] = useS(null);
  const [err, setErr] = useS("");
  const [busy, setBusy] = useS(false);
  const [filter, setFilter] = useS("all");
  const [copied, setCopied] = useS("");
  const load = async () => {
    setBusy(true);
    const p = await api("/h3q/ping");
    setPing(p);
    const d = await api("/h3q/pending?limit=30");
    if (d && d.ok) { setTasks(d.tasks || []); setErr(""); }
    else setErr("无法连接队列服务 " + H3Q);
    setBusy(false);
  };
  useE(() => {
    load();
    const iv = setInterval(load, 10000);
    return () => clearInterval(iv);
  }, []);
  const ack = async (id) => {
    await api("/h3q/ack", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ taskId: id }) });
    load();
  };
  const copy = async (txt) => {
    let ok = false;
    try { await navigator.clipboard.writeText(txt); ok = true; } catch (e) {}
    if (!ok) {
      try {
        const ta = document.createElement("textarea");
        ta.value = txt; ta.style.position = "fixed"; ta.style.opacity = "0";
        document.body.appendChild(ta); ta.select();
        ok = document.execCommand("copy");
        document.body.removeChild(ta);
      } catch (e) {}
    }
    if (ok) { setCopied(txt); setTimeout(() => setCopied(""), 1500); }
  };
  const shown = tasks.filter((j) => {
    if (filter === "all") return true;
    if (filter === "active") return j.state === "queued" || j.state === "running" || j.state === "submitted";
    return j.state === filter;
  });
  const FB = (k, label, v) => h("button", { key: k, onClick: () => setFilter(v), ...EV,
    style: { fontSize: 11, padding: "2px 10px", borderRadius: 10, cursor: "pointer",
      border: "1px solid " + (filter === v ? C(th.activeStroke, "#22c55e") : C(th.faint, "#374151")),
      background: filter === v ? C(th.activeStroke, "#22c55e") + "22" : "transparent",
      color: filter === v ? C(th.activeStroke, "#22c55e") : C(th.muted, "#9ca3af") } }, label);
  const live = ping ? ping.active : null;
  return h("div", {
    "data-canvas-no-zoom": "true", ...EV,
    style: { height: "100%", display: "flex", flexDirection: "column", padding: 10, boxSizing: "border-box", color: C(th.text, "#e5e7eb"), background: C(th.fill, "transparent"), borderRadius: 8, fontSize: 12 },
    children: [
      // 标题行
      h("div", { key: "h", style: { display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }, children: [
        h("span", { key: "t", style: { fontWeight: 700, fontSize: 13 } }, "H3 任务找回"),
        h("span", { key: "s", style: { fontSize: 10, padding: "1px 8px", borderRadius: 8,
          background: live == null ? "#ef444422" : "#22c55e22", color: live == null ? "#ef4444" : "#22c55e" } },
          live == null ? "服务离线" : "活动任务 " + live),
        h("button", { key: "r", onClick: () => load(), ...EV, disabled: busy,
          style: { marginLeft: "auto", fontSize: 11, padding: "2px 10px", borderRadius: 4, cursor: "pointer",
            border: "1px solid " + C(th.stroke, "#4b5563"), background: "transparent", color: C(th.text, "#e5e7eb") } },
          busy ? "刷新中…" : "刷新"),
      ] }),
      // 过滤
      h("div", { key: "f", style: { display: "flex", gap: 6, marginBottom: 8 }, children: [
        FB("a", "全部", "all"), FB("b", "进行中", "active"), FB("c", "已完成", "done"), FB("d", "失败", "failed"),
      ] }),
      // 错误提示
      err ? h("div", { key: "e", style: { color: "#f87171", fontSize: 11, marginBottom: 6 } }, err) : null,
      // 列表
      h("div", { key: "l", "data-canvas-no-zoom": "true", ...EV,
        style: { flex: 1, overflowY: "auto", minHeight: 0, paddingRight: 2 },
        children: shown.length === 0
          ? h("div", { style: { color: C(th.placeholder, "#6b7280"), fontSize: 11, textAlign: "center", padding: "24px 0", whiteSpace: "pre-line", lineHeight: 1.8 } },
              tasks.length === 0 ? "暂无任务\n生成视频后会自动出现在这里\n刷新页面也不丢失" : "当前筛选下没有任务")
          : shown.map((j) => h(TaskCard, { key: j.taskId, job: j, th, onAck: ack, onCopy: copy, copied: copied === (j.resultUrl || j.taskId) })),
      }),
    ],
  });
}

// ---------- 节点与插件定义 ----------
const H3RecoveryNode = {
  type: "h3-recovery:queue",
  title: "H3任务找回",
  icon: "🔎",
  description: "H3 队列任务看板：排队/生成中/已完成/失败，结果预览与复制链接，页面刷新后可找回",
  defaultSize: { width: 440, height: 500 },
  defaultMetadata: {},
  minimapColor: "#22c55e",
  Content: RecoveryContent,
};

const plugin = {
  id: "h3-recovery",
  name: "H3任务找回",
  version: "1.0.0",
  description: "H3 视频生成队列任务看板，生成结果不再因页面刷新/关闭而丢失",
  minAppVersion: "0.8.1",
  nodes: [H3RecoveryNode],
};
export default plugin;
