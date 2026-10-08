# CATVERSE 上线说明 · 先试玩，后买域名

> 本项目目前暂存在 **私有** `siren-memory-lab/catverse` 目录。不要将整个 `siren-memory-lab` 直接发布到互联网；只部署下面列出的静态文件。

## 建议路线

1. 先验收本 PR 的网页外观与玩法，保留 Draft 状态。
2. 准备一个**只有 CATVERSE 的独立目录或独立 GitHub 仓库**。需发布的文件为：
   - `index.html`
   - `arcade.html`
   - `catverse-icon.svg`
   - `site.webmanifest`
   - `sw.js`
3. Cloudflare Dashboard → Workers & Pages → 创建 Pages 项目。对于只想立即试玩、无需 Git 自动更新的情况，可用 **Direct Upload（拖拽文件夹或 ZIP）**；只上传上述文件组成的目录，不要上传整个记忆库。
4. 部署完成后会得到实际的 `*.pages.dev` 地址；打开确认五个房间、游乐厅、存档功能与手机布局是否正常。
5. 喜欢以后，再考虑购买域名，在 Pages 项目里配置 Custom Domains。独立域名不是运行游戏的必要条件。

注意：Cloudflare Pages 使用 Direct Upload 创建的项目，未来**无法原地切换为 Git 自动集成**；需要重新创建 Git 集成项目。如果确定想要日后每个 PR 自动产生预览，更推荐先建立纯 CATVERSE 的独立仓库，再选择 Git 集成。官方说明：[Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/)、[Static HTML](https://developers.cloudflare.com/pages/framework-guides/deploy-anything/)、[Custom Domains](https://developers.cloudflare.com/pages/configuration/custom-domains/)。

## iPhone 使用

- 通过 HTTPS 网页打开一次，等待页面资源缓存；随后可通过 Safari 分享菜单的“添加到主屏幕”安装快捷入口。
- Manifest、SVG 图标、Service Worker 基础离线缓存已在项目中，离线访问依赖浏览器支持及首次在线缓存是否成功。
- `file://` 直接打开时，Service Worker 不会启用；要体验离线效果请通过 HTTPS 的 Pages 地址访问。
- 游玩纪录用浏览器本地存储；换域名/换设备时**不能自动继承**：先在旧地址导出 JSON，再到新地址导入。
- 网站有公开网址 ≠ 私人授权访问；目前没有用户登录或访问控制。只放可公开的小游戏静态内容，不放 token、日记、私人聊天或其他敏感资料。

## 仍需验收

- [ ] Safari 真机图形、触摸、字体和弹珠物理表现
- [ ] iPhone 导出 / 导入 JSON 流程
- [ ] 最高分同域名跨页面保留
- [ ] 打开音效、静音切换正常，默认静音
- [ ] 完成线上首次缓存后离线打开
- [ ] 主屏幕图标显示效果（SVG 兼容性因浏览器而异，后续可补 PNG 图标）

**域名购买原则**：先确认喜欢的名字、续费价格和管理平台；不要为测试期急着购买。最重要的是把私人记忆库和公共游戏隔离。
