![](./titlepage.png)

# SteamTradingSiteTracker

Steam 挂刀行情站 —— 全天候更新的 BUFF & IGXE & C5 & UUYP 挂刀比例数据

## 近期站点情况说明

**5月 26 日至 29 日期间，iflow.work 多次受到 DDoS 攻击，因此我们将站点流量迁移到了 Cloudflare，并更换了服务器 IP**

这可能影响站点在境内部分地区的可达性，详情请见：[站点主页说明](https://www.wolai.com/eZZ1UwWEM9Hawro3cXZjVq)

## 更新及分支公告

为提高数据的更新频率，自 2023/04/01 起，站点使用新的技术架构，同时主分支开始维护新版本代码。

原先版本的代码（通过多进程实现并行爬虫，仅需配置 MongoDB，运行更稳定）将切换至 [sync](https://github.com/EricZhu-42/SteamTradingSiteTracker/tree/sync) 分支维护。

新版本代码的使用文档将于后期更新。

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

站点 APP 端（微信小程序）由 [@lazycce](https://github.com/lazycce) 开发维护，详见：[SteamTradingSiteTracker-APP](https://github.com/lazycce/SteamTradingSiteTracker-APP)

APP 端与网页端数据同步，可以在各种网络环境下正常访问

## 其他信息

更新日志、开发计划等其他信息请参考我们的 [项目主页](https://www.wolai.com/eZZ1UwWEM9Hawro3cXZjVq)

推荐适合爬虫业务的[**优质代理 IP 池**](https://www.3ip.cn?sid=31556)，按量付费套餐低至 0.0015 元/IP，新用户免费领取测试额度。
