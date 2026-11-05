import { api } from '../api'
import type { AvatarInfo, VoiceInfo } from '../types'
import { Badge, Card } from './ui'

export default function Assets({ avatars, voices, bgm, notify }: {
  avatars: AvatarInfo[]; voices: VoiceInfo[]; bgm: string[]; notify: (s: string) => void
}) {
  return (
    <div className="page">
      <div className="page-head"><div><div className="eyebrow">ASSETS / 03</div><h1 className="h1">资产库</h1><p className="sub">形象、音色与包装素材。当前 720p 形象可用，1080p 形象待拍。</p></div><div className="hero-actions"><button className="btn primary" onClick={() => notify('上传形象需要资产接口，v2 再做')}>⇪ 上传形象</button></div></div>
      <div className="asset-grid">
        {avatars.map(a => (
          <div className="card asset" key={a.id}>
            <div className="cover"><img src={api.avatarFrame(a.id)} alt={a.id} onError={e => { (e.currentTarget as HTMLImageElement).style.display = 'none' }} /></div>
            <h4>{a.id}</h4><p>{a.width}×{a.height} · {a.frames} frames</p>
            <div className="foot"><Badge tone="ok">可用</Badge><span className="hint" style={{ marginLeft: 'auto' }}>MuseTalk</span></div>
          </div>
        ))}
        <div className="card asset"><div className="cover placeholder">1080P / TODO</div><h4>avatar_v1</h4><p>1080×1920 · 待拍摄</p><div className="foot"><Badge tone="wait">待补素材</Badge><span className="hint" style={{ marginLeft: 'auto' }}>iPhone 4K</span></div></div>
      </div>
      <div className="grid-3" style={{ marginTop: 14 }}>
        <Card title="音色 / VOICES" meta="EDGETTS">
          <div className="card-body">
            {voices.map(v => <div className="voice-row" key={v.id}><b>{v.name}</b><Badge tone="ok">可用</Badge><span className="mono">{v.id}</span></div>)}
            <div className="voice-row"><b>CosyVoice2 · 克隆</b><Badge tone="wait">未接</Badge><span className="mono">P4 / 需 GPU</span></div>
          </div>
        </Card>
        <Card title="包装 / PACKS" meta="BGM · 字幕">
          <div className="card-body list">
            {bgm.map(b => <div className="list-row" key={b}><b>{b}</b><Badge tone="idle">BGM</Badge><span className="mono">12%</span></div>)}
            {!bgm.length && <div className="list-row"><span className="hint">data/bgm 下暂无音乐</span></div>}
            <div className="list-row"><b>默认字幕样式</b><Badge tone="ok">Noto CJK</Badge><span className="mono">44px</span></div>
            <div className="list-row"><b>封面模板 · 标题</b><Badge tone="ok">第一句</Badge><span className="mono">JPG</span></div>
          </div>
        </Card>
      </div>
    </div>
  )
}
