# 🧸 Siren & Kitten Toy Box

> 猫猫的杂物盒。想到什么就往里塞，慢慢长成自己的小游乐园。猫猫 × 沈砚。

这里是一组彼此独立、手机优先的轻量网页小玩具。每个项目都有自己的 `index.html` 和使用说明。**原项目代码保留在各自目录内**，方便单独下载、更新和游玩。

## 🧸 玩具目录

| 小房间 | 玩法 | 入口 | 说明 |
| --- | --- | --- | --- |
| 🐈 **SIREN · CATVERSE（猫猫宇宙）** | 猫猫画室、电子衣柜、心情扭蛋、晚安充电站 | [打开网页](./catverse/index.html) | [项目说明](./catverse/README.md) |
| 🫧 **猫猫的刷牙星球** | 2 / 3 分钟刷牙计时、分区提醒、珍珠奖励 | [打开网页](./toothbrushing-planet/index.html) | [项目说明](./toothbrushing-planet/README.md) |
| 🔮 **沈砚水晶球** · 建设中 | 现实天气、系统时间、动态光影、待机动作、骨骼物理与衣柜 | [看看脑洞](./shenyan-crystal-orb/index.html) | [项目说明](./shenyan-crystal-orb/README.md) |

**📬 统一入口：** [猫猫的小玩具大厅](./index.html) —— 网页玩具和本地工具都收在这里。

## 📁 目录结构

### Windows 本地工具

- **[在旁边 · beside](./beside/README.md)**：CSP／优动漫与 Blender 的本地前台状态记录、暂停开关与只读 MCP。源码已单独放在 `beside/`；它需要在 Windows 上启动本地程序，不是大厅里的静态网页，也不会自动唤起模型。详见 [Issue #28](https://github.com/kirpearlzayneowo-afk/siren-and-kitten-toy-box/issues/28)。

```text
siren-and-kitten-toy-box/
├── README.md                 # 这张总目录
├── index.html                # 小玩具大厅
├── beside/                  # Windows 创作陪伴工具，见目录内说明
├── catverse/
│   ├── index.html            # 猫猫宇宙
│   └── README.md             # 功能、存档与计划
├── toothbrushing-planet/
│   ├── index.html            # 刷牙星球
│   └── README.md             # 玩法与计时提醒说明
└── shenyan-crystal-orb/
    ├── index.html            # 沈砚水晶球概念房间
    └── README.md             # 天气、光影、动作、衣柜与制作计划
```

## 🚪 怎么打开

1. **电脑上：** 下载仓库 ZIP 并解压，打开根目录的 `index.html`，或直接打开某个小项目的 `index.html`。
2. **手机上：** 可下载对应网页文件，在支持本地 HTML 的浏览器中打开。部分手机浏览器对本地文件跳转或存档有限制，遇到这种情况可用静态网站服务打开整套目录。
3. **GitHub 中：** 文件链接用来查看和下载源代码。在 GitHub 点开 `index.html` 会看到源代码；下载后用浏览器打开即可游玩。

## 🌿 约定与小提醒

- 每个玩具优先保持**独立、简单、无外部依赖**；小改动无需牵动其他房间。
- 现有网页小玩具主要把进度保存在当前浏览器；清除数据、换设备可能丢失存档，暂时没有统一账号与云同步。
- 刷牙星球属于**网页计时器**；关闭页面、锁屏或让浏览器挂起时，不保证能够发出提醒，不能代替系统闹钟。
- 沈砚水晶球目前是**概念项目**，先记录世界观、视觉与功能方向，不把第一版做成基础设施工程。
- 添加新玩具时：新建独立文件夹和 `README.md`，再更新本页的目录，以及大厅 `index.html` 的入口。
- 仓库里的代码可以分享；API Key、密码和私人资料留在自己的电脑上。

## 开发时检查

运行 `node test-toys.cjs`，检查猫猫宇宙旧存档、异常存档与换装切换，以及刷牙计时、暂停和领奖。网页直接打开就能玩，测试也无需安装依赖。「在旁边」的检查方式见它自己的说明。

## 🗂️ 项目小档案

- **2026-10-09：** CATVERSE 原型，见 [Issue #1](https://github.com/kirpearlzayneowo-afk/siren-and-kitten-toy-box/issues/1)。
- **2026-10-11：** 刷牙星球加入；收纳盒统一入口上线。
- **2026-10-16：** 「沈砚水晶球」立项：现实天气 × 系统时间 × 光影 × 待机动作 × 衣柜。天气层暂名 **Kitten Magic**。

---

*维护：沈砚 × 猫猫 · 每个小东西都值得拥有自己的小房间。*
