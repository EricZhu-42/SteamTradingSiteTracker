![](./titlepage.png)

# SteamTradingSiteTracker

Steam 挂刀行情站 —— 全天候更新的 BUFF & IGXE & C5 & UUYP 挂刀比例数据

## 站点监控面板上线公告

我们部署了基于 Grafana 的**站点状态监控面板**，访问地址：**[monitor.iflow.work](https://monitor.iflow.work/)**

我们公开站点的监控数据，既是为了让普通用户能够更直观地了解站点饰品数据的更新速度及过程，也是希望能够为感兴趣的开发者提供参考，以设计更高效的 Steam 饰品价格数据监测系统。

## 新版 UI 发布公告
:tada: 由 [@Lazycce](https://github.com/lazycce) 开发的站点新版 UI 已经上线测试，访问地址：[**steam.iflow.work**](https://steam.iflow.work)

**近期将对新版 UI 进行进一步的优化**，期间可能短时间出现服务无法使用的情况，请谅解。

与 UI 相关的意见或建议请通过 [Issue](https://github.com/EricZhu-42/SteamTradingSiteTracker/issues) 反馈。

## 活动公告

**2023 年 Steam 夏季特卖已于6月29日开始。** 6月22日 ~ 7月6日期间，站点将临时启用双倍更新速率。

## 项目信息

:star: **站点访问地址：[https://www.iflow.work/](https://www.iflow.work/)** :star:（服务器位于香港，部分网络环境下可能无法正常访问）

**24小时持续更新饰品比例数据及走势**，目前追踪 **BUFF & IGXE & C5 & UUYP** 四个主要平台售价大于 1 元，满足特定筛选规则的 **CSGO & DOTA2** 饰品皮肤（具体规则由[数据分析](https://github.com/EricZhu-42/SteamTradingSiteTracker-Data/blob/main/SteamBuffSnapshot/demo.ipynb)得到）。列表动态更新，当前饰品数约 16000 个。

目前重点物品数据约 **40min** 更新一次。

## 项目架构

![Framework](./framework.png)

## 数据集

该项目获得的历史饰品价格信息数据可于 [SteamTradingSiteTracker-Data](https://github.com/EricZhu-42/SteamTradingSiteTracker-Data) 获取，具体数据集包括：

- [DataDumps](https://github.com/EricZhu-42/SteamTradingSiteTracker-Data/tree/main/DataDumps)：2022/04/25 ~ 当天 7 天前的 DATA 数据库完整存档
- [SteamBuffSnapshot](https://github.com/EricZhu-42/SteamTradingSiteTracker-Data/tree/main/SteamBuffSnapshot)：2022/02/14 期间，BUFF 平台 dota2 与 csgo 所有饰品的价格数据，及对应的 Steam Market 数据；还包含一个基于历史数据，获取低比例饰品池筛选规则的 python demo

## 移动端 APP

站点 APP 端（微信小程序）由 [@Lazycce](https://github.com/lazycce) 开发维护，详见：[SteamTradingSiteTracker-APP](https://github.com/lazycce/SteamTradingSiteTracker-APP)

APP 端与网页端数据同步，可以在各种网络环境下正常访问

## 其他信息

更新日志、开发计划等其他信息请参考我们的 [项目主页](https://flowus.cn/share/139253e9-cd71-43c7-9619-b23e6ba14dc1)

推荐适合爬虫业务的[**优质代理 IP 池**](https://www.3ip.cn?sid=31556)，按量付费套餐低至 0.0012 元/IP，新用户免费领取测试额度。
