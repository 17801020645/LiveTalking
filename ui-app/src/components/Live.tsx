import { useEffect, useRef, useState } from 'react'
import { api, offer } from '../api'
import type { AvatarInfo, LiveStatus, VoiceInfo } from '../types'
import { AvatarImg } from './Overview'
import { Badge, Card } from './ui'

type ChatMsg = { who: string; text: string; me?: boolean }

export default function Live({ live, avatars, voices, notify }: {
  live: LiveStatus; avatars: AvatarInfo[]; voices: VoiceInfo[]; notify: (s: string) => void
}) {
  const [avatar, setAvatar] = useState('')
  const [voice, setVoice] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [connected, setConnected] = useState(false)
  const [videoReady, setVideoReady] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [input, setInput] = useState('')
  const [chat, setChat] = useState<ChatMsg[]>([
    { who: '数字人 · 小陈', text: '点击“连接”后，可以输入文本或按住说话。' },
  ])
  const [talkStatus, setTalkStatus] = useState('')
  const [recording, setRecording] = useState(false)
  const [videoRecording, setVideoRecording] = useState(false)
  const [recordReady, setRecordReady] = useState(false)
  const pcRef = useRef<RTCPeerConnection | null>(null)
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<number | null>(null)

  useEffect(() => {
    if (!avatar) {
      const preferred = avatars.find(a => a.id === 'avatar_ck') || avatars[0]
      if (preferred) setAvatar(preferred.id)
    }
    if (!voice && voices[0]) setVoice(voices[0].id)
  }, [avatars, voices, avatar, voice])

  useEffect(() => () => { cleanup() }, [])

  useEffect(() => {
    if (!sessionId) return
    const onUnload = () => {
      try {
        const blob = new Blob([JSON.stringify({ sessionid: sessionId })], { type: 'application/json' })
        navigator.sendBeacon('/api/live/close', blob)
      } catch { /* ignore */ }
    }
    window.addEventListener('beforeunload', onUnload)
    return () => window.removeEventListener('beforeunload', onUnload)
  }, [sessionId])

  function cleanup() {
    if (timerRef.current) window.clearTimeout(timerRef.current)
    if (recorderRef.current) { try { recorderRef.current.stop() } catch { /* */ } }
    if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop())
    if (pcRef.current) { pcRef.current.close(); pcRef.current = null }
    streamRef.current = null
    recorderRef.current = null
    setRecording(false)
  }

  async function waitIce(pc: RTCPeerConnection) {
    if (pc.iceGatheringState === 'complete') return
    await new Promise<void>(resolve => {
      const done = () => { pc.removeEventListener('icegatheringstatechange', check); resolve() }
      const check = () => { if (pc.iceGatheringState === 'complete') done() }
      pc.addEventListener('icegatheringstatechange', check)
      window.setTimeout(done, 3000)
    })
  }

  async function connect() {
    if (sessionId || connecting) return
    if (live.active >= live.max) return notify(`已达到 ${live.max} 路上限`)
    setConnecting(true)
    try {
      const pc = new RTCPeerConnection()
      pcRef.current = pc
      pc.addTransceiver('video', { direction: 'recvonly' })
      pc.addTransceiver('audio', { direction: 'recvonly' })
      pc.addEventListener('track', evt => {
        const stream = evt.streams[0]
        if (evt.track.kind === 'video' && videoRef.current) videoRef.current.srcObject = stream
        if (evt.track.kind === 'audio' && audioRef.current) audioRef.current.srcObject = stream
      })
      pc.addEventListener('connectionstatechange', () => {
        if (pc.connectionState === 'connected') { setConnected(true); setConnecting(false); setVideoReady(false) }
        if (pc.connectionState === 'disconnected' || pc.connectionState === 'failed') {
          setConnected(false); setVideoReady(false); setSessionId(null); setConnecting(false)
          notify('WebRTC 连接已断开，请重连')
        }
      })
      const local = await pc.createOffer()
      await pc.setLocalDescription(local)
      await waitIce(pc)
      const answer = await offer(pc.localDescription!.sdp, pc.localDescription!.type, avatar, voice)
      await pc.setRemoteDescription({ type: 'answer', sdp: answer.sdp })
      setSessionId(answer.sessionid)
      notify(`会话已建立：${answer.sessionid.slice(0, 8)}…`)
    } catch (e: any) {
      setConnecting(false)
      cleanup()
      notify(`连接失败：${e.message || e}`)
    }
  }

  async function disconnect() {
    if (sessionId) {
      try { await api.closeLive(sessionId) } catch { /* cleanup best effort */ }
    }
    cleanup()
    setSessionId(null)
    setConnected(false)
    setVideoReady(false)
    if (videoRef.current) videoRef.current.srcObject = null
    if (audioRef.current) audioRef.current.srcObject = null
    setTalkStatus('')
    notify('会话已结束')
  }

  async function sendText(textOverride?: string, fromTalk = false) {
    const text = (textOverride ?? input).trim()
    if (!text) return
    if (!sessionId) return notify('请先连接 WebRTC')
    try {
      await api.human({ text, type: 'chat', interrupt: true, sessionid: sessionId })
      setChat(c => [...c, { who: fromTalk ? '你 · 按住说话' : '你', text, me: true }, { who: '数字人 · 小陈', text: '正在播报…' }])
      setInput('')
    } catch (e: any) { notify(`发送失败：${e.message || e}`) }
  }

  async function interrupt() {
    if (!sessionId) return notify('请先连接')
    try { await api.interrupt(sessionId); notify('已打断当前播报') }
    catch (e: any) { notify(`打断失败：${e.message || e}`) }
  }

  async function toggleRecord() {
    if (!sessionId) return notify('请先连接 WebRTC')
    const type = videoRecording ? 'end_record' : 'start_record'
    try {
      await api.record(sessionId, type)
      setVideoRecording(!videoRecording)
      if (!videoRecording) { setRecordReady(false); notify('开始录制') }
      else { setRecordReady(true); notify('录制已结束，可下载') }
    } catch (e: any) { notify(`录制失败：${e.message || e}`) }
  }

  async function startTalk() {
    if (!sessionId) return notify('请先连接 WebRTC')
    if (!window.isSecureContext) return setTalkStatus('需要 HTTPS 或 localhost 才能使用麦克风')
    if (!navigator.mediaDevices?.getUserMedia) return setTalkStatus('当前浏览器不支持麦克风')
    if (!window.MediaRecorder) return setTalkStatus('当前浏览器不支持录音')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      chunksRef.current = []
      const mime = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ? 'audio/webm;codecs=opus' : ''
      const rec = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined)
      rec.ondataavailable = ev => { if (ev.data?.size) chunksRef.current.push(ev.data) }
      rec.start()
      recorderRef.current = rec
      setRecording(true)
      setTalkStatus('录音中…')
      timerRef.current = window.setTimeout(() => stopTalk(), 30000)
    } catch (e: any) { setTalkStatus(`麦克风不可用：${e.message || e}`) }
  }

  function stopTalk() {
    if (!recorderRef.current) return
    const rec = recorderRef.current
    recorderRef.current = null
    if (timerRef.current) window.clearTimeout(timerRef.current)
    setRecording(false)
    const done = new Promise<void>(resolve => { rec.onstop = () => resolve() })
    rec.stop()
    done.then(async () => {
      if (streamRef.current) { streamRef.current.getTracks().forEach(t => t.stop()); streamRef.current = null }
      if (!chunksRef.current.length) { setTalkStatus('没录到声音，请重试'); return }
      const blob = new Blob(chunksRef.current, { type: chunksRef.current[0].type || 'audio/webm' })
      chunksRef.current = []
      setTalkStatus('识别中…')
      try {
        const r = await api.asr(blob)
        const text = (r.text || '').trim()
        if (!text) {
          setTalkStatus(r.peak < 0.005 ? '录音是静音，请检查麦克风' : '没有识别到文字，请再说一次')
          return
        }
        setTalkStatus(`识别：${text}`)
        await sendText(text, true)
      } catch (e: any) { setTalkStatus(`识别失败：${e.message || e}`) }
    })
  }

  const activeSessions = live.sessions
  const maxed = live.active >= live.max || activeSessions.length >= live.max

  return (
    <div className="page">
      <div className="page-head">
        <div><div className="eyebrow">REALTIME / 02</div><h1 className="h1">实时会话</h1><p className="sub">2 路上限。文本或按住说话，数字人实时回应；第 3 路会明确提示已满。</p></div>
        <div className="hero-actions"><button className="btn" onClick={() => notify('排队设置 v2 再做')}>排队设置</button><button className="btn primary" onClick={connect} disabled={connecting || !!sessionId || maxed}>{connecting ? '连接中…' : sessionId ? '已连接' : maxed ? '已满' : '◉ 连接会话'}</button></div>
      </div>

      <div className="live-grid">
        <Card title="预览 / SESSION" meta={sessionId ? `${sessionId.slice(0, 8)}… · ${connected ? 'LIVE' : 'CONNECTING'}` : '未连接'} actions={<Badge tone={connected ? 'live' : 'idle'}>{connected ? '● LIVE' : 'IDLE'}</Badge>}>
          <div className="card-body">
            <div className="preview">
              {!connected && <div className="preview-empty"><AvatarImg id={avatar} alt="数字人预览" /><span>点击“连接会话”启动 WebRTC</span></div>}
              <video ref={videoRef} autoPlay playsInline muted={false} onLoadedMetadata={() => setVideoReady(true)} style={{ opacity: videoReady ? 1 : 0 }} />
              <audio ref={audioRef} autoPlay />
              <div className="scan" />
              <div className="hud"><Badge tone={connected ? 'live' : 'idle'}>{connected ? '● LIVE' : 'IDLE'}</Badge><Badge tone="idle">25 FPS</Badge><Badge tone="idle">WebRTC</Badge></div>
              <div className="bottom"><span>GPU {((live.gpu.used_mb || 0) / 1024).toFixed(1)}G</span><span>LAN</span><div className={`progress ${videoReady ? '' : 'wait'}`}><i style={{ width: videoReady ? '100%' : connected ? '60%' : '0%' }} /></div><span>{videoReady ? '已连接' : connected ? '连接中' : '—'}</span></div>
            </div>
            <div className="preview-actions">
              <button className="btn" disabled={!sessionId} onClick={interrupt}>■ 打断</button>
              <button className={`btn ${videoRecording ? 'danger' : ''}`} disabled={!sessionId} onClick={toggleRecord}>{videoRecording ? '■ 停止录制' : '● 录制'}</button>
              {recordReady && sessionId && <a className="btn" href={`/record/${sessionId}`} target="_blank" rel="noreferrer">下载录像</a>}
              <button className="btn danger" disabled={!sessionId} onClick={disconnect}>结束会话</button>
              <div className="row-2" style={{ marginLeft: 'auto' }}>
                <select value={avatar} onChange={e => setAvatar(e.target.value)} disabled={!!sessionId}>{avatars.map(a => <option key={a.id} value={a.id}>{a.id}</option>)}</select>
                <select value={voice} onChange={e => setVoice(e.target.value)} disabled={!!sessionId}>{voices.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}</select>
              </div>
            </div>
          </div>
        </Card>

        <Card title="对话 / TRANSCRIPT" meta="ASR + LLM">
          <div className="card-body">
            <div className="chat">
              {chat.map((m, i) => (
                <div key={i} className={`msg ${m.me ? 'me' : ''}`}><span className="who">{m.who}</span>{m.text}</div>
              ))}
            </div>
            <div className="composer-live">
              <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') sendText() }} placeholder="输入文本，或按住说话…" disabled={!sessionId} />
              <button className="icon-btn" title="发送" onClick={() => sendText()} disabled={!sessionId}>➤</button>
              <button className={`icon-btn ${recording ? 'recording' : ''}`} title="按住说话"
                onPointerDown={e => { e.preventDefault(); startTalk() }} onPointerUp={e => { e.preventDefault(); stopTalk() }}
                onPointerLeave={e => { e.preventDefault(); stopTalk() }} onPointerCancel={() => stopTalk()} disabled={!sessionId}>◉</button>
            </div>
            <div className={`hint ${talkStatus.includes('失败') || talkStatus.includes('静音') ? 'bad-text' : ''}`} style={{ marginTop: 8 }}>{talkStatus || 'ASR 约 100ms（CPU）· 失败会区分“静音”和“未识别”'}</div>
          </div>
        </Card>
      </div>

      <Card title="会话列表" meta={`MAX ${live.max} · 第 ${live.max + 1} 路拒绝`}>
        <div className="card-body tight">
          <table className="table session-table">
            <thead><tr><th>会话</th><th>形象</th><th>输入</th><th>状态</th><th>操作</th></tr></thead>
            <tbody>
              {activeSessions.length === 0 && <tr><td colSpan={5}><div className="empty">暂无会话</div></td></tr>}
              {activeSessions.map((s, i) => (
                <tr key={s.id}><td className="name">{s.id.slice(0, 8)}…</td><td className="mono">{avatar}</td><td>{i === 0 ? '文本 + ASR' : '按住说话'}</td><td><Badge tone="live">LIVE</Badge></td><td><button className="btn ghost mini-btn" onClick={() => notify('当前控制台只操作本标签页的会话')}>查看</button></td></tr>
              ))}
              <tr><td className="name dim">sess_third</td><td className="mono">—</td><td>—</td><td><Badge tone="wait">已满 / 排队</Badge></td><td><button className="btn ghost mini-btn" onClick={() => notify(`第 ${live.max + 1} 路会收到明确提示`)}>说明</button></td></tr>
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
