![](./titlepage.png)

# SteamTradingSiteTracker

Steam 挂刀行情站 —— 全天候更新的 BUFF & IGXE & C5 & UUYP 挂刀比例数据

> For a description of this project in English, please refer to the [project wiki](https://github.com/EricZhu-42/SteamTradingSiteTracker/wiki)

## 更新公告

[2024/06/16] 我们的新版[项目主页](https://www.yuque.com/null_42/steam)已经上线。关于项目（非开源代码部分）的最新进展，请参考项目主页的说明。

[2024/04/03] 新增了 “近期成交” 比例的显示功能，表示以 Steam Market 24 小时内交易价格中位数的价格卖出后的挂刀比例，详见：[#48](https://github.com/EricZhu-42/SteamTradingSiteTracker/issues/48)

[2024/02/18] 我们的 [饰品数据 API](https://www.yuque.com/null_42/steam/glmytl66g4l4sufg) 正式发布

## 饰品 ID 映射表

我们发布了一份 DOTA2 & CS2 饰品在 Steam Market 与第三方交易平台的 ID 对照表：[SteamTradingSite-ID-Mapper](https://github.com/EricZhu-42/SteamTradingSite-ID-Mapper).

We are glad to release an ID mapping for DOTA2 & CS2 tradeable items between the Steam Market and major trading platforms: [SteamTradingSite-ID-Mapper](https://github.com/EricZhu-42/SteamTradingSite-ID-Mapper).

## ~~站点监控面板上线公告~~

~~我们部署了基于 Grafana 的**站点状态监控面板**，访问地址：**[monitor.iflow.work](https://monitor.iflow.work/)**~~

~~我们公开站点的监控数据，既是为了让普通用户能够更直观地了解站点饰品数据的更新速度及过程，也是希望能够为感兴趣的开发者提供参考，以设计更高效的 Steam 饰品价格数据监测系统。~~

## 项目信息

:star: **站点访问地址：[https://www.iflow.work/](https://www.iflow.work/)** :star:（基于 Cloudflare CDN，部分网络环境下可能无法正常访问）

**24小时持续更新饰品比例数据及走势**，目前追踪 **BUFF & IGXE & C5 & UUYP** 四个主要平台所有 **CSGO & DOTA2** 饰品（共约 64000 个），并基于特定筛选规则（具体规则由[数据分析](https://github.com/EricZhu-42/SteamTradingSiteTracker-Data/blob/main/SteamBuffSnapshot/demo.ipynb)得到）维护设定饰品更新优先级，目前重点饰品数据约 **10 min** 更新一次。

## 项目架构

> 该项目架构图可能已经过时，仅供参考。

![Framework](./framework.png)

## 数据集

该项目获得的历史饰品价格信息数据可于 [SteamTradingSiteTracker-Data](https://github.com/EricZhu-42/SteamTradingSiteTracker-Data) 获取，具体数据集包括：

- [DataDumps](https://github.com/EricZhu-42/SteamTradingSiteTracker-Data/tree/main/DataDumps)：2022/04/25 至今的 Priority 数据库完整存档，每 12 小时更新一次;
- [SteamBuffSnapshot](https://github.com/EricZhu-42/SteamTradingSiteTracker-Data/tree/main/SteamBuffSnapshot)：2022/02/14 期间，BUFF 平台 dota2 与 csgo 所有饰品的价格数据，及对应的 Steam Market 数据；还包含一个基于历史数据，获取低比例饰品池筛选规则的 python demo.

## 移动端 APP

站点 APP 端（微信小程序）由 [@Lazycce](https://github.com/lazycce) 开发维护，详见：[SteamTradingSiteTracker-APP](https://github.com/lazycce/SteamTradingSiteTracker-APP)

APP 端与网页端数据同步，可以在各种网络环境下正常访问

## 其他信息

**更新日志、开发计划**等其他信息请参考我们的 [项目主页](https://www.yuque.com/null_42/steam).

如果您希望成为本项目的**赞助商**，请参考：[常见问题](https://www.yuque.com/null_42/steam/tfe59eeg6m1b3wki).

