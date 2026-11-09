let stream, ctx, analyser, raf;
const $ = id => document.getElementById(id);

async function listDevices() {
  const devices = await navigator.mediaDevices.enumerateDevices();
  const sel = $('device');
  sel.innerHTML = '';
  const inputs = devices.filter(d => d.kind === 'audioinput');
  inputs.forEach((d, i) => {
    const o = document.createElement('option');
    o.value = d.deviceId;
    o.textContent = (d.label || `麦克风 ${i+1}`) + (d.deviceId === 'default' ? '（默认）' : '');
    sel.appendChild(o);
  });
  sel.disabled = false;
  return inputs;
}

async function start(deviceId) {
  stop();
  const constraints = { audio: deviceId ? { deviceId: { exact: deviceId } } : true };
  stream = await navigator.mediaDevices.getUserMedia(constraints);
  ctx = new (window.AudioContext || window.webkitAudioContext)();
  analyser = ctx.createAnalyser();
  analyser.fftSize = 1024;
  ctx.createMediaStreamSource(stream).connect(analyser);
  const track = stream.getAudioTracks()[0];
  $('status').className = 'status good';
  $('status').textContent = '正在监听：' + (track.label || '默认麦克风');
  const inputs = await listDevices();
  const current = inputs.find(d => d.deviceId === track.getSettings().deviceId);
  if (current) $('device').value = current.deviceId;
  const data = new Float32Array(analyser.fftSize);
  function draw() {
    analyser.getFloatTimeDomainData(data);
    let sum = 0;
    for (let i = 0; i < data.length; i++) sum += data[i] * data[i];
    const rms = Math.sqrt(sum / data.length);
    const pct = Math.min(100, rms * 500);
    $('level').style.width = pct + '%';
    $('level').style.background = rms > 0.02 ? '#22c55e' : rms > 0.005 ? '#eab308' : '#ef4444';
    if (rms < 0.002) {
      $('hint').className = 'muted bad';
      $('hint').textContent = '几乎没有声音：检查是否选错设备、耳机麦克风是否静音。';
    } else {
      $('hint').className = 'muted';
      $('hint').textContent = '有输入电平。说一句话，绿色条应明显跳动。';
    }
    raf = requestAnimationFrame(draw);
  }
  draw();
}

function stop() {
  if (raf) cancelAnimationFrame(raf);
  raf = null;
  if (stream) stream.getTracks().forEach(t => t.stop());
  stream = null;
  if (ctx) ctx.close().catch(() => {});
  ctx = null;
}

$('start').onclick = async () => {
  try {
    if (!window.isSecureContext) {
      $('status').className = 'status bad';
      $('status').textContent = '当前不是 HTTPS，浏览器不会给麦克风。';
      return;
    }
    await start();
  } catch (e) {
    $('status').className = 'status bad';
    $('status').textContent = '打开麦克风失败：' + (e.message || e);
  }
};

$('device').onchange = async () => {
  try { await start($('device').value); }
  catch (e) { $('status').className = 'status bad'; $('status').textContent = '切换设备失败：' + (e.message || e); }
};

if (!navigator.mediaDevices) {
  $('status').className = 'status bad';
  $('status').textContent = '浏览器没有 mediaDevices；请用 HTTPS 或 localhost。';
}
