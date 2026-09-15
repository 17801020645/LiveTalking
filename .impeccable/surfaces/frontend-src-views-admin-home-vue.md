---
version: 1
slug: "frontend-src-views-admin-home-vue"
primary_target: "frontend/src/views/admin/Home.vue"
related_targets: ["frontend/src/layouts/AdminLayout.vue"]
---

# Surface: Admin home

- **Route:** `/app/admin`
- **Target:** `frontend/src/views/admin/Home.vue`
- **Mode:** Operate
- **Audience:** GPU operators scanning workload
- **Job:** See pending orders, active sessions, generating tasks; enter demo live
- **Constraints:** Do not invent counts or customers. Engine capabilities stay; this shell may change.

## Direction contract

THESIS: The home is a preview wall, not a SaaS card grid. Three monitors are the work; a tally means live, idle, or fault. It refuses the light indigo sidebar plus nested glass cards.

OWN-WORLD: Matte gallery wall (#111318), Electric Indigo (#4361ee) as the only brand wash, frost glass on thick bezels, green/red as tally lamps only, plush corners and real frame shadows. Content removed, it still reads as a dark monitor wall.

STORY: The operator sees what needs them now, believes the numbers are the live gallery, and clicks a monitor or 「去演示连麦」 to act.

FIRST VIEWPORT: Thin dark rail left with LiveTalking and five admin links. Main wall: three large preview monitors in a row (订单 / 连麦 / 生成), each with a huge count, a tally lamp, and a short caption. 「去演示连麦」 sits under the wall as the program cut, not inside a fourth card. Username and logout stay on a slim top strip.

FORM: Broadcast Gallery (grounded pick; seed key 7c9c70d8). Not the assigned rundown board.

APPROVED COMP: `.impeccable/mocks/admin-home-comp-row.png` — three equal preview monitors in a row; 去演示连麦 as program cut under the wall. Comp Chinese is not literal; implement real copy. Bezels and lamps are CSS, not rasterized type.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
