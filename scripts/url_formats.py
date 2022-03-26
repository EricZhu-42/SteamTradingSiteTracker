# ==== meta ====
steam_item_page_fmt = r'https://steamcommunity.com/market/listings/{appid:d}/{hash_name:s}'
buff_index_json_fmt = r'https://buff.163.com/api/market/goods?game={game:s}&page_num={page_num:d}&page_size=80&min_price=1&max_price=5000&sort_by=price.asc'
igxe_search_page_fmt = r'https://www.igxe.cn/market/{game:s}?keyword={name:s}'
c5_csgo_search_page_fmt = r'https://www.c5game.com/csgo/default/result.html?k={name:s}'
c5_dota_search_page_fmt = r'https://www.c5game.com/dota.html?k={name:s}'


# ==== data ====
index_page_fmt = r'https://steamcommunity.com/market/listings/{appid:d}/{hash_name:s}'
order_json_fmt = r'https://steamcommunity.com/market/itemordershistogram?country=HK&currency=23&language=english&item_nameid={market_id:d}&two_factor=0&norender=1'
volume_json_fmt = r'https://steamcommunity.com/market/priceoverview/?appid={appid:d}&currency=23&market_hash_name={hash_name:s}'
buff_json_fmt = r'https://buff.163.com/api/market/goods/sell_order?game={game:s}&goods_id={buff_id:d}'
igxe_json_fmt = r'https://www.igxe.cn/product/trade/{appid:d}/{igxe_id:d}'
c5_json_fmt = r'https://www.c5game.com/gw/steamtrade/sga/sell/v1/list?itemId={c5_id:d}'