import { startTransition, useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
import Hls from "hls.js";
import { api } from "./api";

const emptySourceForm = {
  name: "",
  source_url: "",
  stream_key: "",
  target_id: "",
  enabled: true,
  transcode_mode: "copy",
};

const emptyTargetForm = {
  name: "",
  rtmp_base_url: "",
  playback_vhost: "",
  is_default: false,
};

const statusLabels = {
  running: "运行中",
  starting: "启动中",
  stopped: "已停止",
  error: "异常",
};

function buildPreviewUrls(detail) {
  if (!detail) {
    return null;
  }

  const rtmpBase = `${detail.target.rtmp_base_url.replace(/\/$/, "")}/${detail.source.stream_key}`;
  const vhostQ = detail.target.playback_vhost
    ? `${rtmpBase.includes("?") ? "&" : "?"}vhost=${encodeURIComponent(detail.target.playback_vhost)}`
    : "";
  const rtmpUrl = `${rtmpBase}${vhostQ}`;
  const match = detail.target.rtmp_base_url.match(/^rtmp:\/\/([^/:]+)(?::(\d+))?(\/.*)?$/);
  if (!match) {
    return { rtmpUrl, flvUrl: "", hlsUrl: "" };
  }

  const path = (match[3] || "/live").replace(/\/$/, "");
  const vhostQuery = detail.target.playback_vhost
    ? `?vhost=${encodeURIComponent(detail.target.playback_vhost)}`
    : "";
  const proxyBasePath = `${api.baseUrl}/api/v1/preview/${detail.target.id}${path}`;
  return {
    rtmpUrl,
    flvUrl: `${proxyBasePath}/${detail.source.stream_key}.flv${vhostQuery}`,
    hlsUrl: `${proxyBasePath}/${detail.source.stream_key}.m3u8${vhostQuery}`,
  };
}

function StreamPreviewPlayer({ hlsUrl, title }) {
  const videoRef = useRef(null);
  const [playbackState, setPlaybackState] = useState("loading");
  const [playbackError, setPlaybackError] = useState("");
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !hlsUrl) {
      return undefined;
    }

    let hls = null;
    let mounted = true;

    const attemptPlay = async () => {
      try {
        await video.play();
        if (mounted) {
          setPlaybackState("playing");
        }
      } catch {
        // Autoplay can still be blocked by the browser; controls remain available.
        if (mounted) {
          setPlaybackState("paused");
        }
      }
    };

    const handlePlaying = () => mounted && setPlaybackState("playing");
    const handlePause = () => mounted && setPlaybackState("paused");
    const handleWaiting = () => mounted && setPlaybackState("buffering");
    const handleNativeVideoError = () => {
      if (!mounted) {
        return;
      }
      setPlaybackError("播放器发生错误，请重载后再试。");
    };

    video.addEventListener("playing", handlePlaying);
    video.addEventListener("pause", handlePause);
    video.addEventListener("waiting", handleWaiting);
    setPlaybackError("");
    setPlaybackState("loading");

    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.addEventListener("error", handleNativeVideoError);
      video.src = hlsUrl;
      void attemptPlay();
      return () => {
        mounted = false;
        video.removeEventListener("playing", handlePlaying);
        video.removeEventListener("pause", handlePause);
        video.removeEventListener("waiting", handleWaiting);
        video.removeEventListener("error", handleNativeVideoError);
        video.pause();
        video.removeAttribute("src");
        video.load();
      };
    }

    if (Hls.isSupported()) {
      // 跨端口访问 API 时，Worker 内 XHR 偶发 CORS/与 video error 竞态，关闭 worker；错误以 Hls 事件为准，勿绑原生 video error（易误报）
      hls = new Hls({ enableWorker: false, lowLatencyMode: true });
      hls.on(Hls.Events.ERROR, (_event, data) => {
        if (!mounted) {
          return;
        }
        if (!data?.fatal) {
          setPlaybackState("buffering");
          return;
        }

        if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {
          setPlaybackState("buffering");
          hls?.startLoad();
          return;
        }

        if (data.type === Hls.ErrorTypes.MEDIA_ERROR) {
          setPlaybackState("buffering");
          hls?.recoverMediaError();
          return;
        }

        setPlaybackState("error");
        setPlaybackError(data?.details || data?.type || "HLS 播放失败");
      });
      hls.loadSource(hlsUrl);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, attemptPlay);
      return () => {
        mounted = false;
        video.removeEventListener("playing", handlePlaying);
        video.removeEventListener("pause", handlePause);
        video.removeEventListener("waiting", handleWaiting);
        hls?.destroy();
      };
    }

    setPlaybackState("error");
    setPlaybackError("当前浏览器不支持 HLS 播放，请使用支持 MSE 的浏览器。");
    return () => {
      mounted = false;
      video.removeEventListener("playing", handlePlaying);
      video.removeEventListener("pause", handlePause);
      video.removeEventListener("waiting", handleWaiting);
    };
  }, [hlsUrl, reloadToken]);

  function handlePlay() {
    const video = videoRef.current;
    if (!video) {
      return;
    }
    void video.play();
  }

  function handlePause() {
    const video = videoRef.current;
    if (!video) {
      return;
    }
    video.pause();
  }

  function handleReload() {
    setPlaybackError("");
    setPlaybackState("loading");
    setReloadToken((current) => current + 1);
  }

  return (
    <div className="preview-player">
      <video ref={videoRef} controls muted playsInline autoPlay className="preview-video" />
      <div className="preview-player-meta">
        <strong>{title}</strong>
        <p>默认使用 HLS 播放；若无画面，请先检查 `playback_vhost` 和编码格式。</p>
      </div>
      <div className="preview-toolbar">
        <div className="preview-status">
          <span className={`status-dot ${playbackState}`} />
          <strong>
            {playbackState === "playing"
              ? "正在播放"
              : playbackState === "buffering"
                ? "缓冲中"
                : playbackState === "error"
                  ? "播放失败"
                  : playbackState === "paused"
                    ? "已暂停"
                    : "加载中"}
          </strong>
        </div>
        <div className="preview-controls">
          <button type="button" className="ghost-button small" onClick={handlePlay}>
            播放
          </button>
          <button type="button" className="ghost-button small" onClick={handlePause}>
            暂停
          </button>
          <button type="button" className="ghost-button small" onClick={handleReload}>
            重载
          </button>
        </div>
      </div>
      {playbackError ? <div className="preview-error">{playbackError}</div> : null}
    </div>
  );
}

function mergeSourceStatuses(sources, statuses) {
  return sources.map((source) => ({
    ...source,
    job: statuses[source.id] || {
      source_id: source.id,
      status: "stopped",
      pid: null,
      started_at: null,
      updated_at: source.updated_at,
      last_error: null,
      retry_count: 0,
    },
  }));
}

export default function App() {
  const [sources, setSources] = useState([]);
  const [targets, setTargets] = useState([]);
  const [settings, setSettings] = useState(null);
  const [detail, setDetail] = useState(null);
  const [selectedSourceId, setSelectedSourceId] = useState("");
  const [sourceForm, setSourceForm] = useState(emptySourceForm);
  const [targetForm, setTargetForm] = useState(emptyTargetForm);
  const [settingsForm, setSettingsForm] = useState({
    ffmpeg_loglevel: "info",
    ffmpeg_extra_args: "",
    max_retry_count: 3,
    retry_delay_seconds: 5,
  });
  const [filterText, setFilterText] = useState("");
  const deferredFilterText = useDeferredValue(filterText);
  const [statusFilter, setStatusFilter] = useState("all");
  const [isLoading, setIsLoading] = useState(true);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [banner, setBanner] = useState("");
  const [error, setError] = useState("");

  const previewUrls = useMemo(() => {
    if (!detail) {
      return null;
    }
    return buildPreviewUrls(detail);
  }, [
    detail?.source?.id,
    detail?.source?.stream_key,
    detail?.target?.id,
    detail?.target?.rtmp_base_url,
    detail?.target?.playback_vhost,
  ]);

  async function loadDashboard(preserveSelected = true) {
    setError("");
    if (!preserveSelected) {
      setIsLoading(true);
    }

    try {
      const [fetchedSources, fetchedTargets, fetchedSettings] = await Promise.all([
        api.listSources(),
        api.listTargets(),
        api.getSettings(),
      ]);
      const statuses = await Promise.all(
        fetchedSources.map(async (source) => [source.id, await api.getJobStatus(source.id)])
      );
      const mergedSources = mergeSourceStatuses(fetchedSources, Object.fromEntries(statuses));

      startTransition(() => {
        setSources(mergedSources);
        setTargets(fetchedTargets);
        setSettings(fetchedSettings);
        setSettingsForm({
          ffmpeg_loglevel: fetchedSettings.ffmpeg_loglevel,
          ffmpeg_extra_args: fetchedSettings.ffmpeg_extra_args,
          max_retry_count: fetchedSettings.max_retry_count,
          retry_delay_seconds: fetchedSettings.retry_delay_seconds,
        });

        if (!preserveSelected && mergedSources[0]) {
          setSelectedSourceId(mergedSources[0].id);
        } else if (selectedSourceId && !mergedSources.some((item) => item.id === selectedSourceId)) {
          setSelectedSourceId(mergedSources[0]?.id || "");
        }
      });
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setIsLoading(false);
    }
  }

  async function loadDetail(
    sourceId,
    { showLoading = true, syncForm = true } = {}
  ) {
    if (!sourceId) {
      setDetail(null);
      return;
    }
    if (showLoading) {
      setIsDetailLoading(true);
    }
    try {
      const data = await api.getSourceDetail(sourceId, 120);
      setDetail(data);
      if (syncForm) {
        setSourceForm({
          name: data.source.name,
          source_url: data.source.source_url,
          stream_key: data.source.stream_key,
          target_id: data.source.target_id || "",
          enabled: data.source.enabled,
          transcode_mode: data.source.transcode_mode,
        });
      }
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      if (showLoading) {
        setIsDetailLoading(false);
      }
    }
  }

  useEffect(() => {
    loadDashboard(false);
  }, []);

  useEffect(() => {
    void loadDetail(selectedSourceId);
  }, [selectedSourceId]);

  useEffect(() => {
    const timer = setInterval(() => {
      void loadDashboard(true);
      if (selectedSourceId) {
        // 仅刷新任务状态与日志，不打断表单编辑、不闪「正在加载」
        void loadDetail(selectedSourceId, { showLoading: false, syncForm: false });
      }
    }, 5000);

    return () => clearInterval(timer);
  }, [selectedSourceId]);

  const filteredSources = useMemo(() => {
    return sources.filter((source) => {
      const matchesText =
        !deferredFilterText ||
        source.name.toLowerCase().includes(deferredFilterText.toLowerCase()) ||
        source.stream_key.toLowerCase().includes(deferredFilterText.toLowerCase());
      const matchesStatus =
        statusFilter === "all" || source.job.status === statusFilter;
      return matchesText && matchesStatus;
    });
  }, [deferredFilterText, sources, statusFilter]);

  const overview = useMemo(() => {
    return {
      total: sources.length,
      running: sources.filter((item) => item.job.status === "running").length,
      error: sources.filter((item) => item.job.status === "error").length,
      stopped: sources.filter((item) => item.job.status === "stopped").length,
      defaultTarget: targets.find((item) => item.is_default)?.name || "未设置",
    };
  }, [sources, targets]);

  function showBanner(message) {
    setBanner(message);
    window.clearTimeout(showBanner.timer);
    showBanner.timer = window.setTimeout(() => setBanner(""), 2500);
  }

  async function handleCreateSource(event) {
    event.preventDefault();
    try {
      const payload = { ...emptySourceForm, ...sourceForm };
      if (!payload.target_id) {
        delete payload.target_id;
      }
      const created = await api.createSource(payload);
      await loadDashboard(true);
      setSelectedSourceId(created.id);
      showBanner("通道已创建");
    } catch (submitError) {
      setError(submitError.message);
    }
  }

  async function handleUpdateSource(event) {
    event.preventDefault();
    if (!selectedSourceId) {
      return;
    }
    try {
      const payload = { ...sourceForm };
      if (!payload.target_id) {
        delete payload.target_id;
      }
      await api.updateSource(selectedSourceId, payload);
      await loadDashboard(true);
      await loadDetail(selectedSourceId, { showLoading: false, syncForm: true });
      showBanner("通道配置已保存");
    } catch (submitError) {
      setError(submitError.message);
    }
  }

  async function handleCreateTarget(event) {
    event.preventDefault();
    try {
      await api.createTarget(targetForm);
      await loadDashboard(true);
      setTargetForm(emptyTargetForm);
      showBanner("SRS 目标已添加");
    } catch (submitError) {
      setError(submitError.message);
    }
  }

  async function handleSaveSettings(event) {
    event.preventDefault();
    try {
      await api.updateSettings({
        ...settingsForm,
        max_retry_count: Number(settingsForm.max_retry_count),
        retry_delay_seconds: Number(settingsForm.retry_delay_seconds),
      });
      await loadDashboard(true);
      showBanner("系统设置已更新");
    } catch (submitError) {
      setError(submitError.message);
    }
  }

  async function handleJobAction(action, sourceId) {
    try {
      if (action === "start") {
        await api.startJob(sourceId);
      } else if (action === "stop") {
        await api.stopJob(sourceId);
      } else {
        await api.restartJob(sourceId);
      }
      await loadDashboard(true);
      if (selectedSourceId === sourceId) {
        await loadDetail(sourceId, { showLoading: false, syncForm: true });
      }
      showBanner(`任务已${action === "restart" ? "重启" : action === "start" ? "启动" : "停止"}`);
    } catch (actionError) {
      setError(actionError.message);
    }
  }

  return (
    <div className="console-shell">
      <header className="masthead">
        <div>
          <p className="eyebrow">Local Relay Console</p>
          <h1>视频转接本地运维台</h1>
          <p className="subtitle">
            配置外来视频通道，绑定外推 SRS，查看实时状态和最近日志。
          </p>
        </div>
        <div className="toolbar">
          <span className="api-badge">API {api.baseUrl}</span>
          <button className="ghost-button" onClick={() => loadDashboard(true)}>
            立即刷新
          </button>
        </div>
      </header>

      {banner ? <div className="banner success">{banner}</div> : null}
      {error ? <div className="banner error">{error}</div> : null}

      <section className="overview-grid">
        <StatCard label="通道总数" value={overview.total} tone="slate" />
        <StatCard label="运行中" value={overview.running} tone="green" />
        <StatCard label="异常" value={overview.error} tone="amber" />
        <StatCard label="已停止" value={overview.stopped} tone="rose" />
        <StatCard label="默认目标" value={overview.defaultTarget} tone="teal" wide />
      </section>

      <main className="workspace-grid">
        <section className="panel channel-panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Channels</p>
              <h2>视频通道</h2>
            </div>
            <div className="filters">
              <input
                value={filterText}
                onChange={(event) => setFilterText(event.target.value)}
                placeholder="按名称或 stream_key 搜索"
              />
              <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                <option value="all">全部状态</option>
                <option value="running">运行中</option>
                <option value="error">异常</option>
                <option value="stopped">已停止</option>
              </select>
            </div>
          </div>

          <div className="channel-list">
            {isLoading ? <p className="muted-text">正在加载通道...</p> : null}
            {filteredSources.map((source) => (
              <button
                key={source.id}
                className={`channel-row ${selectedSourceId === source.id ? "selected" : ""}`}
                onClick={() => setSelectedSourceId(source.id)}
              >
                <div>
                  <strong>{source.name}</strong>
                  <p>{source.stream_key}</p>
                </div>
                <div className="channel-meta">
                  <StatusPill status={source.job.status} />
                  <small>重试 {source.job.retry_count}</small>
                </div>
              </button>
            ))}
            {!isLoading && filteredSources.length === 0 ? (
              <p className="muted-text">没有匹配的通道。</p>
            ) : null}
          </div>

          <form className="stack-form" onSubmit={handleCreateSource}>
            <div className="panel-header compact">
              <div>
                <p className="panel-kicker">Create</p>
                <h3>新增通道</h3>
              </div>
            </div>
            <label>
              名称
              <input
                value={sourceForm.name}
                onChange={(event) => setSourceForm((current) => ({ ...current, name: event.target.value }))}
                required
              />
            </label>
            <label>
              输入地址
              <input
                value={sourceForm.source_url}
                onChange={(event) =>
                  setSourceForm((current) => ({ ...current, source_url: event.target.value }))
                }
                placeholder="rtsp://user:pass@host:554/stream"
                required
              />
            </label>
            <div className="two-up">
              <label>
                Stream Key
                <input
                  value={sourceForm.stream_key}
                  onChange={(event) =>
                    setSourceForm((current) => ({ ...current, stream_key: event.target.value }))
                  }
                  required
                />
              </label>
              <label>
                转码模式
                <select
                  value={sourceForm.transcode_mode}
                  onChange={(event) =>
                    setSourceForm((current) => ({ ...current, transcode_mode: event.target.value }))
                  }
                >
                  <option value="copy">copy</option>
                  <option value="transcode">transcode</option>
                </select>
              </label>
            </div>
            <div className="two-up">
              <label>
                SRS 目标
                <select
                  value={sourceForm.target_id}
                  onChange={(event) =>
                    setSourceForm((current) => ({ ...current, target_id: event.target.value }))
                  }
                >
                  <option value="">默认目标</option>
                  {targets.map((target) => (
                    <option key={target.id} value={target.id}>
                      {target.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="toggle-field">
                <span>启用并随服务恢复</span>
                <input
                  type="checkbox"
                  checked={sourceForm.enabled}
                  onChange={(event) =>
                    setSourceForm((current) => ({ ...current, enabled: event.target.checked }))
                  }
                />
              </label>
            </div>
            <button type="submit" className="primary-button">
              新增通道
            </button>
          </form>
        </section>

        <section className="panel detail-panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Detail</p>
              <h2>{detail?.source.name || "通道详情"}</h2>
            </div>
            {detail ? <StatusPill status={detail.job.status} /> : null}
          </div>

          {!selectedSourceId ? <p className="muted-text">从左侧选择一条通道查看详情。</p> : null}
          {selectedSourceId && isDetailLoading ? <p className="muted-text">正在加载详情...</p> : null}

          {detail ? (
            <>
              <div className="detail-topline">
                <InfoBadge label="Stream Key" value={detail.source.stream_key} />
                <InfoBadge label="SRS 目标" value={detail.target.name} />
                <InfoBadge label="播放 vhost" value={detail.target.playback_vhost || "-"} />
                <InfoBadge label="最近更新时间" value={detail.job.updated_at} />
              </div>

              <div className="action-row">
                <button className="primary-button" onClick={() => handleJobAction("start", detail.source.id)}>
                  启动
                </button>
                <button className="ghost-button" onClick={() => handleJobAction("restart", detail.source.id)}>
                  重启
                </button>
                <button className="danger-button" onClick={() => handleJobAction("stop", detail.source.id)}>
                  停止
                </button>
              </div>

              <form className="stack-form" onSubmit={handleUpdateSource}>
                <div className="panel-header compact">
                  <div>
                    <p className="panel-kicker">Edit</p>
                    <h3>通道配置</h3>
                  </div>
                </div>
                <label>
                  名称
                  <input
                    value={sourceForm.name}
                    onChange={(event) => setSourceForm((current) => ({ ...current, name: event.target.value }))}
                  />
                </label>
                <label>
                  输入地址
                  <input
                    value={sourceForm.source_url}
                    onChange={(event) =>
                      setSourceForm((current) => ({ ...current, source_url: event.target.value }))
                    }
                  />
                </label>
                <div className="two-up">
                  <label>
                    Stream Key
                    <input
                      value={sourceForm.stream_key}
                      onChange={(event) =>
                        setSourceForm((current) => ({ ...current, stream_key: event.target.value }))
                      }
                    />
                  </label>
                  <label>
                    转码模式
                    <select
                      value={sourceForm.transcode_mode}
                      onChange={(event) =>
                        setSourceForm((current) => ({ ...current, transcode_mode: event.target.value }))
                      }
                    >
                      <option value="copy">copy</option>
                      <option value="transcode">transcode</option>
                    </select>
                  </label>
                </div>
                <div className="two-up">
                  <label>
                    SRS 目标
                    <select
                      value={sourceForm.target_id}
                      onChange={(event) =>
                        setSourceForm((current) => ({ ...current, target_id: event.target.value }))
                      }
                    >
                      <option value="">默认目标</option>
                      {targets.map((target) => (
                        <option key={target.id} value={target.id}>
                          {target.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="toggle-field">
                    <span>启用并自动恢复</span>
                    <input
                      type="checkbox"
                      checked={sourceForm.enabled}
                      onChange={(event) =>
                        setSourceForm((current) => ({ ...current, enabled: event.target.checked }))
                      }
                    />
                  </label>
                </div>
                <button type="submit" className="primary-button">
                  保存配置
                </button>
              </form>

              <div className="preview-panel">
                <div className="panel-header compact">
                  <div>
                    <p className="panel-kicker">Preview</p>
                    <h3>监视窗口</h3>
                  </div>
                </div>
                <div className="preview-window">
                  {detail.recent_logs && /Error opening output/i.test(detail.recent_logs) ? (
                    <div className="preview-push-warn" role="status">
                      最近日志显示 RTMP 推流未成功建立。在无有效源流时 HLS
                      预览会失败。请确认本机/容器到 SRS
                      的网络、端口与
                      vhost，并在修改目标后点击「重启」使推流参数生效。
                    </div>
                  ) : null}
                  <div className="preview-frame">
                    {previewUrls?.hlsUrl ? (
                      <StreamPreviewPlayer hlsUrl={previewUrls.hlsUrl} title={detail.source.name} />
                    ) : (
                      <div className="preview-empty">
                        <strong>{detail.source.name}</strong>
                        <p>当前没有可用的 HLS 预览地址。</p>
                        <StatusPill status={detail.job.status} />
                      </div>
                    )}
                  </div>
                  {previewUrls ? (
                    <div className="preview-links">
                      <PreviewLink label="HLS 播放" href={previewUrls.hlsUrl} />
                      <PreviewLink label="RTMP 推流" href={previewUrls.rtmpUrl} />
                      <PreviewLink label="HTTP-FLV 候选" href={previewUrls.flvUrl} />
                    </div>
                  ) : null}
                </div>
              </div>

              <div className="log-panel">
                <div className="panel-header compact">
                  <div>
                    <p className="panel-kicker">Logs</p>
                    <h3>最近日志</h3>
                  </div>
                </div>
                <pre>{detail.recent_logs || "当前没有日志输出。"}</pre>
              </div>
            </>
          ) : null}
        </section>

        <section className="panel settings-panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Settings</p>
              <h2>系统配置与 SRS 目标</h2>
            </div>
          </div>

          <form className="stack-form" onSubmit={handleSaveSettings}>
            <div className="panel-header compact">
              <div>
                <p className="panel-kicker">Runtime</p>
                <h3>系统配置</h3>
              </div>
            </div>
            <div className="two-up">
              <label>
                ffmpeg 日志级别
                <select
                  value={settingsForm.ffmpeg_loglevel}
                  onChange={(event) =>
                    setSettingsForm((current) => ({ ...current, ffmpeg_loglevel: event.target.value }))
                  }
                >
                  <option value="error">error</option>
                  <option value="warning">warning</option>
                  <option value="info">info</option>
                  <option value="debug">debug</option>
                </select>
              </label>
              <label>
                最大重试次数
                <input
                  type="number"
                  min="0"
                  max="20"
                  value={settingsForm.max_retry_count}
                  onChange={(event) =>
                    setSettingsForm((current) => ({ ...current, max_retry_count: event.target.value }))
                  }
                />
              </label>
            </div>
            <div className="two-up">
              <label>
                重试间隔秒数
                <input
                  type="number"
                  min="0"
                  max="300"
                  step="0.5"
                  value={settingsForm.retry_delay_seconds}
                  onChange={(event) =>
                    setSettingsForm((current) => ({ ...current, retry_delay_seconds: event.target.value }))
                  }
                />
              </label>
              <label>
                最近更新时间
                <input value={settings?.updated_at || ""} readOnly />
              </label>
            </div>
            <label>
              ffmpeg 额外参数
              <textarea
                rows="3"
                value={settingsForm.ffmpeg_extra_args}
                onChange={(event) =>
                  setSettingsForm((current) => ({ ...current, ffmpeg_extra_args: event.target.value }))
                }
              />
            </label>
            <button type="submit" className="primary-button">
              保存系统配置
            </button>
          </form>

          <div className="target-list">
            <div className="panel-header compact">
              <div>
                <p className="panel-kicker">Targets</p>
                <h3>SRS 目标列表</h3>
              </div>
            </div>
            {targets.map((target) => (
              <TargetCard key={target.id} target={target} onRefresh={loadDashboard} onError={setError} />
            ))}
          </div>

          <form className="stack-form" onSubmit={handleCreateTarget}>
            <div className="panel-header compact">
              <div>
                <p className="panel-kicker">Create</p>
                <h3>新增 SRS 目标</h3>
              </div>
            </div>
            <label>
              名称
              <input
                value={targetForm.name}
                onChange={(event) => setTargetForm((current) => ({ ...current, name: event.target.value }))}
                required
              />
            </label>
            <label>
              RTMP Base URL
              <input
                value={targetForm.rtmp_base_url}
                onChange={(event) =>
                  setTargetForm((current) => ({ ...current, rtmp_base_url: event.target.value }))
                }
                placeholder="rtmp://srs-host:1935/live"
                required
              />
            </label>
            <label>
              播放 vhost
              <input
                value={targetForm.playback_vhost}
                onChange={(event) =>
                  setTargetForm((current) => ({ ...current, playback_vhost: event.target.value }))
                }
                placeholder="vid-2162315"
              />
            </label>
            <label className="toggle-field">
              <span>设为默认目标</span>
              <input
                type="checkbox"
                checked={targetForm.is_default}
                onChange={(event) =>
                  setTargetForm((current) => ({ ...current, is_default: event.target.checked }))
                }
              />
            </label>
            <button type="submit" className="primary-button">
              新增目标
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}

function StatCard({ label, value, tone, wide = false }) {
  return (
    <article className={`stat-card ${tone} ${wide ? "wide" : ""}`}>
      <p>{label}</p>
      <strong>{value}</strong>
    </article>
  );
}

function StatusPill({ status }) {
  return <span className={`status-pill ${status}`}>{statusLabels[status] || status}</span>;
}

function InfoBadge({ label, value }) {
  return (
    <div className="info-badge">
      <span>{label}</span>
      <strong>{value || "-"}</strong>
    </div>
  );
}

function PreviewLink({ label, href }) {
  if (!href) {
    return null;
  }
  return (
    <a className="preview-link" href={href} target="_blank" rel="noreferrer">
      <span>{label}</span>
      <strong>{href}</strong>
    </a>
  );
}

function TargetCard({ target, onRefresh, onError }) {
  const [form, setForm] = useState({
    name: target.name,
    rtmp_base_url: target.rtmp_base_url,
    playback_vhost: target.playback_vhost || "",
    is_default: target.is_default,
  });

  useEffect(() => {
    setForm({
      name: target.name,
      rtmp_base_url: target.rtmp_base_url,
      playback_vhost: target.playback_vhost || "",
      is_default: target.is_default,
    });
  }, [target]);

  async function handleSubmit(event) {
    event.preventDefault();
    try {
      await api.updateTarget(target.id, form);
      await onRefresh(true);
    } catch (error) {
      onError(error.message);
    }
  }

  return (
    <form className="target-card" onSubmit={handleSubmit}>
      <div className="target-card-title">
        <strong>{target.name}</strong>
        {target.playback_vhost ? <span className="mini-tag">vhost {target.playback_vhost}</span> : null}
        {target.is_default ? <span className="mini-tag">默认</span> : null}
      </div>
      <label>
        名称
        <input value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} />
      </label>
      <label>
        RTMP Base URL
        <input
          value={form.rtmp_base_url}
          onChange={(event) => setForm((current) => ({ ...current, rtmp_base_url: event.target.value }))}
        />
      </label>
      <label>
        播放 vhost
        <input
          value={form.playback_vhost}
          onChange={(event) =>
            setForm((current) => ({ ...current, playback_vhost: event.target.value }))
          }
          placeholder="vid-2162315"
        />
      </label>
      <label className="toggle-field">
        <span>默认目标</span>
        <input
          type="checkbox"
          checked={form.is_default}
          onChange={(event) => setForm((current) => ({ ...current, is_default: event.target.checked }))}
        />
      </label>
      <button type="submit" className="ghost-button">
        保存目标
      </button>
    </form>
  );
}
