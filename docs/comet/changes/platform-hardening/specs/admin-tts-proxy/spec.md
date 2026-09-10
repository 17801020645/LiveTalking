# 管理员 TTS 代理

## 能力

管理员在 `/app/admin/tts` 管理 Omni 音色与试听。浏览器只访问 8010；8010 把请求转发到本机 Omni（默认 `http://127.0.0.1:8091`）。局域网用户不必对 8091 开口，也不必在页面上填写 8091 地址。

数字人默认 TTS 仍为 `edgetts`。本规格不启动、不安装 Omni。

## 上游

- 上游基址取配置 `TTS_SERVER`；为空则用 `http://127.0.0.1:8091`。
- 也可用环境变量 `LIVETALKING_TTS_UPSTREAM` 覆盖（便于测试指向假上游）。
- 8010 作为服务端客户端访问上游；浏览器看不到 8091。

## 代理接口

均在 `/api/v1/` 下，须登录且 `role=admin`。未登录 401，普通用户 403。

| 管理员接口 | 上游 |
| --- | --- |
| `GET /api/v1/admin/tts/voices` | `GET {upstream}/v1/audio/voices` |
| `POST /api/v1/admin/tts/voices` multipart | `POST {upstream}/v1/audio/voices` |
| `DELETE /api/v1/admin/tts/voices/{name}` | `DELETE {upstream}/v1/audio/voices/{name}` |
| `POST /api/v1/admin/tts/speech` JSON | `POST {upstream}/v1/audio/speech` |

合成成功时把上游音频字节原样返回（合适的 `Content-Type`）。JSON 列表原样或包一层 `data`，前端能渲染音色名即可。

上游连接失败、超时或 5xx：代理返回 502 或 503，正文说明「TTS 上游不可用」，不得无限挂起。超时上限应短于浏览器默认等待（建议不超过 30s 连接/读超时，合成可略长但必须有上限）。

不把上游错误堆栈或内部路径泄漏给未登录调用方；管理员可见简短失败原因。

## 管理员界面

`/app/admin/tts` 不再只是链到 `/tts/` 的占位。已登录管理员可以：

- 看到连接状态（上游可达或不可达）
- 刷新音色列表
- 选择音色、输入文本、合成并播放或下载
- 上传克隆音频（multipart，字段与 Omni 管理页一致：`audio_sample`、`name`、`consent`、`ref_text`，可选 `speaker_description`）
- 删除已上传音色（上游不支持删除时给出明确提示，不假装成功）

页面不要求填写 8091 URL。可保留指向原 `/tts/` 的次要链接，供仍想直连 8091 的本机调试。

## 与原 `/tts/` 的关系

- 不改写 `web/tts/index.html` 的直连 8091 行为。
- 不把 `/tts/` 默认改成走 8010 代理。
- 不在本规格内部署 Base 克隆模型；上传失败时展示上游返回的错误即可。

## 非范围

- 不把数字人会话默认 TTS 改为 Omni
- 不在 8010 进程内嵌 vLLM
- 不要求单测连接真实 8091
