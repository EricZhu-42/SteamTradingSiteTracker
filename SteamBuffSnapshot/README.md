# SteamBuffSnapshot

本数据集包含了 2022/02/14 期间 BUFF 平台 DOTA2, CSGO 两游戏的饰品价格数据与其对应的 Steam Market 数据，共计 38075 条。

> 数据可能不完整（缺失应该不超过完整列表的 5 %），建议仅作简单分析使用。

## 文件说明

- `dataset/`: 数据集，拆分为 4 个 zip 文件（共约 80 MB），合并解压后为 20 个 json 文件，每个 json 包含至多 2000 条数据；解压后总大小约 740 MB
- `sample.json`: 包含从完整数据集中随机抽出的 100 条数据，供浏览测试使用
- `demo.ipynb`: 一个利用该数据集训练决策树分类器，借以获得简单的低比例饰品池筛选维护规则的 python demo


## 数据字段说明

每条数据有四个字段：'buff_meta', 'buff_order', 'steam_volume', 'steam_order'

- 'buff_meta': 饰品在 BUFF 平台的基本信息，来自 `buff.163.com/api/market/goods` 接口，包含两个额外字段：`market_id` （物品在 Steam Market 对应的唯一 id） 与 `updated_at`（数据获取时刻的 timestamp，下同）
- 'buff_order': 饰品在 BUFF 平台的出售订单信息，来自 `buff.163.com/api/market/goods/sell_order` 接口，**仅包含第一页数据**
- `steam_volume`: 饰品在 Steam Market 的 24h 出售量与售价统计，来自 `steamcommunity.com/market/priceoverview/` 接口
- `steam_order`: 饰品在 Steam Market 的即时求购/寄售价格直方图数据，来自 `steamcommunity.com/market/itemordershistogram` 接口

