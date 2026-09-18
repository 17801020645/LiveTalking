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
- 完成时间: 2026-09-18T10:57:12.925Z
- 摘要: A1–A4 通过：一次性哈希令牌 24h，公开重设成功后作废令牌与会话且不自动登录；失败文案统一；Login/Ops 入口齐全；web/ 与自改密、代人改密保留。

## 验收

| 编号 | 结果 | 来源 | 验收项 | 原因 |
| --- | --- | --- | --- | --- |
| A1 | passed | brief.md | A1：有效令牌可为普通用户设新密码；旧密码失效，该用户原有登录会话失效；成功后须用新密码重新登录 | forgot_password 校验通过后更新 password_hash、DELETE sessions 与 password_reset_tokens，且不写 Cookie；test_a1 覆盖旧密/旧会话 401、新密登录成功、库中无明文令牌 |
| A2 | passed | brief.md | A2：错令牌、过期、重复使用、未知用户名均失败，文案不暴露该用户名是否存在 | 错令牌、过期、复用、未知用户名、管理员名均返回统一「重置失败」；短密码优先拒绝；test_a2 覆盖 |
| A3 | passed | brief.md | A3：登录页有忘记密码入口；管理员普通用户行有发令牌；不能给管理员或自己发 | Login.vue 有忘记密码入口；Ops 仅普通用户行发令牌；不能给管理员或自己发；禁用用户可改密但登录仍失败 |
| A4 | passed | brief.md | A4：原 `web/` 无改动；顶栏自己改密与管理员直接改密行为不变 | web/ 无改动；顶栏 PasswordForm 与管理员直接改密仍在；代人改密作废未用令牌 |

## 检查

| 检查 | 命令 | 工作目录 | 状态 | 退出码 | 耗时 |
| --- | --- | --- | --- | ---: | ---: |
| Forgot password token and related unit tests | -m unittest tests.test_forgot_password_token tests.test_admin_reset_password tests.test_admin_delete_user tests.test_user_change_password | . | passed | 0 | 4850 ms |
| Original web/ unchanged | diff --exit-code -- web/ | . | passed | 0 | 8 ms |
| Reset token route, Login/Ops UI, README | -n admin/users/.*/reset-token\\|issueResetToken\\|/api/v1/auth/forgot-password\\|忘记密码\\|发令牌\\|用户（禁用/启用/删除/改密/重置令牌）\\|disable/enable/delete/reset password/reset token server/platform_routes.py frontend/src/views/Login.vue frontend/src/views/admin/Ops.vue README.md README-EN.md | . | passed | 0 | 8 ms |

## 阻塞项

_无。_

## 风险与跳过的工作

- 过期令牌在哈希校验前短路，与错令牌存在轻微时序差异（非功能失败）
- 未在浏览器点选登录页忘记密码与 Ops 发令牌

## 之前的迭代

| 目标周期 | 迭代 | 尝试 | 结果 | 未解决项 | 摘要 | 完成时间 |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | 1 | pass | — | A1–A4 通过：一次性哈希令牌 24h，公开重设成功后作废令牌与会话且不自动登录；失败文案统一；Login/Ops 入口齐全；web/ 与自改密、代人改密保留。 | 2026-09-18T10:57:12.925Z |



## 结论

A1–A4 通过：一次性哈希令牌 24h，公开重设成功后作废令牌与会话且不自动登录；失败文案统一；Login/Ops 入口齐全；web/ 与自改密、代人改密保留。
