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
- 完成时间: 2026-09-17T13:07:23.467Z
- 摘要: A1–A4 均通过：活跃用户改密后旧密码失败、新密码可登录且会话失效；禁用用户可改密、启用后须用新密码，禁改管理员/自己、过短、401/403 均符合；普通用户行有确认后改密、管理员行没有；web/ 与顶栏自己改密未改。

## 验收

| 编号 | 结果 | 来源 | 验收项 | 原因 |
| --- | --- | --- | --- | --- |
| A1 | passed | brief.md | A1：管理员为活跃普通用户设新密码后，旧密码登录失败（与错误密码同一文案），新密码可以；该用户原有会话失效 | POST /api/v1/admin/users/{id}/password 更新哈希并 DELETE 该用户全部 sessions。test_a1 覆盖：旧密码登录 401 且 msg 为 LOGIN_ERROR（与错误密码相同），新密码可登录；预先 create_session 的 token 已从 sessions 表删除。 |
| A2 | passed | brief.md | A2：已禁用用户也可改密；启用后须用新密码登录。改管理员、当前登录账号或不存在的 id 失败；未登录 401，普通用户 403；新密码少于 6 位被拒绝且哈希不变 | 已禁用用户改密 200，登录仍 401（LOGIN_ERROR），启用后旧密码 401、新密码 200。改当前管理员账号 400、不存在 id 404；未登录 401、普通用户 403；密码短于 6 位 400 且原密码仍可登录（哈希未变）。role!=user 时返回「只能给普通用户改密」。 |
| A3 | passed | brief.md | A3：普通用户行有改密按钮并经确认后输入新密码；管理员行没有 | Ops.vue 普通用户行 v-if="u.role === 'user'" 显示「改密」，resetPassword 先 window.confirm 再 window.prompt 后 POST {password}；管理员行无该按钮。README/README-EN 管理员说明已含改密。 |
| A4 | passed | brief.md | A4：原 `web/` 无改动；顶栏自己改密行为不变 | git diff --exit-code -- web/ 通过。PasswordForm 仍走 POST /api/v1/auth/password（current_password/new_password），change_password 未改；test_user_change_password 仍覆盖顶栏自己改密。 |

## 检查

| 检查 | 命令 | 工作目录 | 状态 | 退出码 | 耗时 |
| --- | --- | --- | --- | ---: | ---: |
| Admin reset password and related unit tests | -m unittest tests.test_admin_reset_password tests.test_user_change_password tests.test_admin_delete_user tests.test_admin_disable_user tests.test_admin_enable_user tests.test_gallery_admin_pages tests.test_platform_v1 tests.test_orders | . | passed | 0 | 7742 ms |
| web/ unchanged | diff --exit-code -- web/ | . | passed | 0 | 27 ms |
| Reset route, Ops button, README | -n admin/users/.*/password\\|resetPassword\\|/api/v1/admin/users/{user_id}/password\\|用户（禁用/启用/删除/改密）\\|disable/enable/delete/reset password server/platform_routes.py frontend/src/views/admin/Ops.vue README.md README-EN.md | . | passed | 0 | 8 ms |

## 阻塞项

_无。_

## 风险与跳过的工作

- 未在浏览器点过改密按钮（brief 约定单测不连浏览器；源码与 grep 已覆盖 A3）
- 生产 /app/ 需重新 npm run build 后才有已构建产物

## 之前的迭代

| 目标周期 | 迭代 | 尝试 | 结果 | 未解决项 | 摘要 | 完成时间 |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | 1 | pass | — | A1–A4 均通过：活跃用户改密后旧密码失败、新密码可登录且会话失效；禁用用户可改密、启用后须用新密码，禁改管理员/自己、过短、401/403 均符合；普通用户行有确认后改密、管理员行没有；web/ 与顶栏自己改密未改。 | 2026-09-17T13:07:23.467Z |



## 结论

A1–A4 均通过：活跃用户改密后旧密码失败、新密码可登录且会话失效；禁用用户可改密、启用后须用新密码，禁改管理员/自己、过短、401/403 均符合；普通用户行有确认后改密、管理员行没有；web/ 与顶栏自己改密未改。
