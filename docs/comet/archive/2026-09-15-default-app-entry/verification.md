---
generated_from_state_version: 7
---

# 验证

## 当前结果

- 结果: **已归档**
- 验证情况: **已完成检查，验证结果已确认**
- 目标周期: 1
- 迭代: 1
- 验证器尝试次数: 1
- 完成时间: 2026-09-15T11:14:57.501Z
- 摘要: 默认 WebRTC 根路径改走 /app/，原站改走 /index.html，Live ASR 入口与 rtmp/rtcpush 特例均按 brief 落地。

## 验收

| 编号 | 结果 | 来源 | 验收项 | 原因 |
| --- | --- | --- | --- | --- |
| A1 | passed | brief.md | A1：默认 WebRTC 下 `GET /`（不跟随跳转）返回 302/301，Location 为 `/app/` 或等价 `/app` | index() 在非 rtmp/rtcpush 时 HTTPFound 到 /app/；单测 GET / 不跟随跳转断言 301/302 且 Location 以 /app/ 或 /app 结尾。 |
| A2 | passed | brief.md | A2：`GET /index.html` 仍返回原站控制台（200），不是 Vue 壳 | GET /index.html 返回 200 原站标题 LiveTalking - 数字人实时驱动，不含 Vue id=app；静态 web/index.html 仍可匿名打开。 |
| A3 | passed | brief.md | A3：`/app/admin/live` 的原站入口指向 `/index.html`，文案不再是「打开 /」链到 `/` | Live.vue 为 href=/index.html 与文案「打开 /index.html」，源码无 href=/；相关测试已同步。 |
| A4 | passed | brief.md | A4：`web/` 无改动；rtmp / rtcpush 时 `GET /` 仍分别指向 `rtmpapi.html` / `rtcpushapi.html` | git diff --exit-code -- web/ 通过；rtmp/rtcpush 时 GET / 仍分别指向 rtmpapi.html / rtcpushapi.html，单测覆盖。 |

## 检查

| 检查 | 命令 | 工作目录 | 状态 | 退出码 | 耗时 |
| --- | --- | --- | --- | ---: | ---: |
| Default entry and related unit tests | -m unittest tests.test_default_app_entry tests.test_gallery_admin_pages tests.test_admin_live_console tests.test_user_live tests.test_platform_v1 | . | passed | 0 | 4278 ms |
| Original web/ unchanged | diff --exit-code -- web/ | . | passed | 0 | 44 ms |

## 阻塞项

_无。_

## 风险与跳过的工作

- 8010 未在听，未做浏览器跟跳验证；A1–A4 为 HTTP/源码/git 项。

## 之前的迭代

| 目标周期 | 迭代 | 尝试 | 结果 | 未解决项 | 摘要 | 完成时间 |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | 1 | pass | — | 默认 WebRTC 根路径改走 /app/，原站改走 /index.html，Live ASR 入口与 rtmp/rtcpush 特例均按 brief 落地。 | 2026-09-15T11:14:57.501Z |



## 结论

默认 WebRTC 根路径改走 /app/，原站改走 /index.html，Live ASR 入口与 rtmp/rtcpush 特例均按 brief 落地。
