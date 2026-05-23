import time
import requests
import hashlib
import json
import re
import csv
import os
import random

class TaobaoMtopScraper:
    def __init__(self, cookie_str):
        self.url = "https://h5api.m.taobao.com/h5/mtop.relationrecommend.wirelessrecommend.recommend/2.0/"
        self.app_key = "12574478"
        self.cookie_str = cookie_str
        self.headers = {
            "cookie": self.cookie_str,
            "referer": "https://s.taobao.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0"
        }
        self.csv_file = "家装.csv"
        self.init_csv()

    def init_csv(self):
        """初始化CSV文件，写入表头"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, mode='w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "关键词", "页码", "商品ID", "标题", "价格", "原价描述", "店铺名称",
                    "实际销量", "发货地", "是否广告", "店铺URL", "商品链接", "优惠标签", "属性","商品封面","热门标签","商品卖点","店铺标签"
                ])

    def get_token(self):
        """从当前Cookie字符串中提取Token"""
        token_match = re.search(r'_m_h5_tk=([a-f0-9]{32})_', self.cookie_str)
        if not token_match:
            print(" Cookie 中丢失 _m_h5_tk，请更新 Cookie！")
            return None
        return token_match.group(1)

    def get_sign(self, data_str, t):
        """生成签名"""
        token = self.get_token()
        if not token: return None
        sign_str = f"{token}&{t}&{self.app_key}&{data_str}"
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest()

    def fix_url(self, url):
        """修复URL前缀"""
        if not url: return ""
        if url.startswith("//"): return "https:" + url
        if url.startswith("http"): return url
        return "https://" + url

    def save_one_row(self, item_data):
        """写入单行数据到CSV"""
        with open(self.csv_file, mode='a', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                item_data.get("keyword", ""),
                item_data.get("page_num", ""),
                item_data.get("item_id", ""),
                item_data.get("title", ""),
                item_data.get("price", ""),
                item_data.get("priceDesc", ""),
                item_data.get("shop_title", ""),
                item_data.get("realSales", ""),
                item_data.get("procity", ""),
                item_data.get("isP4p", ""),
                item_data.get("shop_url", ""),
                item_data.get("auctionURL", ""),
                "|".join(item_data.get("coupon", [])), # 列表转字符串
                str(item_data.get("property", ""))   ,  # 字典/列表转字符串
                item_data.get("pic_path", ""),
                item_data.get("hotListInfo", ""),
                item_data.get("summaryTips", ""),
                item_data.get("shop_tag", ""),

            ])

    def fetch_data(self, keyword, page, retry=0):
        """
        核心爬取函数
        :param retry: 重试次数，用于处理Token过期
        """
        if retry > 3:
            print(" 重试次数过多，跳过当前页")
            return

        # 1. 构造动态参数
        inner_params = {
            "device": "HMA-AL00",
            "isBeta": "false",
            "grayHair": "false",
            "from": "nt_history",
            "brand": "HUAWEI",
            "info": "wifi",
            "index": "4",
            "rainbow": "",
            "schemaType": "auction",
            "elderHome": "false",
            "isEnterSrpSearch": "true",
            "newSearch": "false",
            "network": "wifi",
            "subtype": "",
            "hasPreposeFilter": "false",
            "prepositionVersion": "v2",
            "client_os": "Android",
            "gpsEnabled": "false",
            "searchDoorFrom": "srp",
            "debug_rerankNewOpenCard": "false",
            "homePageVersion": "v7",
            "searchElderHomeOpen": "false",
            "search_action": "initiative",
            "sugg": "_4_1",
            "sversion": "13.6",
            "style": "list",
            "ttid": "600000@taobao_pc_10.7.0",
            "needTabs": "true",
            "areaCode": "CN",
            "vm": "nw",
            "countryNum": "156",
            "m": "pc",
            "page": page,         # 动态页码
            "n": 48,
            "q": keyword,         # 动态关键词
            "qSource": "url",
            "pageSource": "a21bo.jianhua/a.search_manual.0",
            "channelSrp": "",
            "tab": "all",
            "pageSize": 48,
            "totalPage": 100,
            "totalResults": 4800,
            "sourceS": "0",
            "sort": "_coefp",
            "filterTag": "",
            "service": "",
            "prop": "",
            "loc": ""
        }

        # 2. 构造 Data 字符串
        real_data_dict = {
            "appId": "34385",
            "params": json.dumps(inner_params, separators=(',', ':'), ensure_ascii=False)
        }
        final_data_str = json.dumps(real_data_dict, separators=(',', ':'), ensure_ascii=False)

        # 3. 签名
        t = str(int(time.time() * 1000))
        sign = self.get_sign(final_data_str, t)
        if not sign: return
        # 4. 请求参数
        params = {
            "jsv": "2.7.2",
            "appKey": self.app_key,
            "t": t,
            "sign": sign,
            "api": "mtop.relationrecommend.wirelessrecommend.recommend",
            "v": "2.0",
            "timeout": "10000",
            "type": "jsonp",
            "dataType": "jsonp",
            "callback": "mtopjsonp6",
            "data": final_data_str,
        }

        try:
            print(f" 正在请求: {keyword} 第 {page} 页...")
            response = requests.get(self.url, headers=self.headers, params=params, timeout=10)

            # 5. 核心逻辑：检测 Token 是否过期
            # 如果 Cookie 过期，服务器会在 Response Headers 的 Set-Cookie 中给一个新的
            # 同时也可能在 body 中返回 FAIL_SYS_TOKEN_EMPTY

            # 自动更新 Cookie 逻辑
            if response.cookies:
                print(" 检测到 Cookie 更新，正在刷新...")
                cookies_dict = requests.utils.dict_from_cookiejar(response.cookies)
                # 简单地把新 cookie 追加/替换到字符串中（简易处理）
                new_cookies = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
                self.cookie_str += "; " + new_cookies
                self.headers["cookie"] = self.cookie_str # 更新 headers

            text = response.text

            # 检查是否因为 Token 问题失败
            if "FAIL_SYS_TOKEN_EMPTY" in text or "FAIL_SYS_ILLEGAL_ACCESS" in text:
                print(f"Token 过期或非法 ({text[:30]}...)，正在使用新 Cookie 重试 ({retry+1}/3)...")
                time.sleep(1)
                return self.fetch_data(keyword, page, retry + 1)

            # 6. 解析数据
            # 去掉 jsonp 的壳
            if "(" in text and ")" in text:
                json_str = text[text.find('(')+1:text.rfind(')')]
            else:
                json_str = text

            data_obj = json.loads(json_str)

            if "data" not in data_obj or "itemsArray" not in data_obj["data"]:
                print(f" 本页无数据或解析失败: {json_str[:50]}")
                return

            items = data_obj["data"]["itemsArray"]
            print(f" 成功获取 {len(items)} 条数据")

            for item in items:
                try:
                    item_data = {}
                    # 基础信息
                    item_data["keyword"] = keyword
                    item_data["page_num"] = page
                    item_data["item_id"] = item.get("item_id", "")
                    item_data["title"] = re.sub(r"<.*?>", "", item.get("title", ""))
                    item_data["price"] = item.get("priceShow", {}).get("price", "")
                    item_data["priceDesc"] = item.get("priceShow", {}).get("priceDesc", "")
                    item_data["realSales"] = item.get("realSales", "0")
                    item_data["procity"] = item.get("procity", "")
                    item_data["isP4p"] = item.get("isP4p", "false")
                    item_data["pic_path"] = item.get("pic_path", "")
                    item_data["hotListInfo"] = item.get("hotListInfo", "") # {rank_short_text: "88VIP甄选套头衫热销榜·第7名"}
                    item_data["summaryTips"] = item.get("summaryTips", "") #  ["48万+穿搭控看过"]

                    # 店铺信息
                    shop_info = item.get("shopInfo", {})
                    item_data["shop_title"] = shop_info.get("title", "")
                    item_data["shop_tag"] = item.get("shopTag", "") # "回头客30万"
                    item_data["shop_url"] = self.fix_url(shop_info.get("url", ""))

                    # 链接
                    item_data["auctionURL"] = self.fix_url(item.get("auctionURL", ""))

                    # 优惠标签
                    coupon = []
                    for icon in item.get("icons", []):
                        if icon.get("text"):
                            coupon.append(icon["text"])
                    item_data["coupon"] = coupon

                    # 属性
                    property_list = []
                    for pro in item.get("structuredUSPInfo", []):
                        property_list.append(f"{pro.get('propertyName')}:{pro.get('propertyValueName')}")
                    item_data["property"] = property_list

                    #  立即保存到CSV
                    self.save_one_row(item_data)

                except Exception as e:
                    print(f" 解析单条出错: {e}")
                    continue

        except Exception as e:
            print(f" 请求异常: {e}")

    def run(self, keywords, max_pages):
        for kw in keywords:
            print(f"\n 开始爬取关键词: {kw}")
            for page in range(1, max_pages + 1):
                self.fetch_data(kw, page)

                #  防封禁：随机延时
                delay = random.uniform(18, 25)
                print(f"等待 {delay:.2f} 秒防止被封...")
                time.sleep(delay)

# ================= 运行区域 =================
if __name__ == "__main__":

    # 1. 填入你最新的 Cookie (必须包含 _m_h5_tk)
    # 如果运行提示 TOKEN_EMPTY 并重试失败，请重新复制浏览器 Cookie
    MY_COOKIE = ("t=3515f603f757083e02d4107b9d3af4d3; thw=cn; xlly_s=1; _tb_token_=e7e1b83317e5; sca=1e94bdcc; _samesite_flag_=true; cookie2=16275ee66c737968babfec95300de006; wk_cookie2=132058340f3fcb66fd4febafe709db51; wk_unb=UUpjNmDGgjg0%2BthCHw%3D%3D; _hvn_lgc_=0; lgc=tb070589493279; cancelledSubSites=empty; dnk=tb070589493279; tracknick=tb070589493279; aui=2220376147255; sdkSilent=1765040872548; havana_sdkSilent=1765040872548; mtop_partitioned_detect=1; _m_h5_tk=188dc0a6f3aa3aa02bd451997b6a4e98_1765029400645; _m_h5_tk_enc=374eaad2bf252498c39257de5ce32f85; 3PcFlag=1765023477977; unb=2220376147255; cookie17=UUpjNmDGgjg0%2BthCHw%3D%3D; _cc_=URm48syIZQ%3D%3D; _l_g_=Ug%3D%3D; sg=951; _nk_=tb070589493279; cookie1=BxFiCYE3WC%2B6h1IlxtE8BVo%2FSvTOZDnBQW53jrMqsKU%3D; sgcookie=E100vnJl1Rj0mmCTTT5RJdkgaNMbHk6dMkVS5WoZuG4L2PizE6YzJlmvCf3JQ5YVeUbVd%2BoU9UdmeKvrKqvYzL5AGAMyuJMOyb2eoO0252XPifc%3D; havana_lgc2_0=eyJoaWQiOjIyMjAzNzYxNDcyNTUsInNnIjoiYzY1ODliZDMxZGRkY2Y3ZWY4ZmNlMmE5NmJjMDdmMDQiLCJzaXRlIjowLCJ0b2tlbiI6IjFQS25fWWdhWXM2bVZ3ZlRKSlZQWHdRIn0; havana_lgc_exp=1796127576572; cookie3_bak=16275ee66c737968babfec95300de006; cookie3_bak_exp=1765282776572; uc1=pas=0&cookie14=UoYY5pDDHXT4rw%3D%3D&cookie21=WqG3DMC9Eman&cookie15=VT5L2FSpMGV7TQ%3D%3D&cookie16=VFC%2FuZ9az08KUQ56dCrZDlbNdA%3D%3D&existShop=false; uc3=lg2=W5iHLLyFOGW7aA%3D%3D&id2=UUpjNmDGgjg0%2BthCHw%3D%3D&vt3=F8dD2kgr8jOxkZ19r3A%3D&nk2=F5RFh66%2B29zxkGx7j%2BM%3D; csg=1d43c7d9; env_bak=FM%2BgzieMDk%2F%2FQ2vcrmtSfvn8NR6f03DciOkQj3sAGEFQ; skt=8bce5e0682bd9686; existShop=MTc2NTAyMzU3Ng%3D%3D; uc4=nk4=0%40FY4O7ocZNnvvRAliZUo6IhVVUCD7pO7d8A%3D%3D&id4=0%40U2gp9rPme2%2Bw9tJA7gV1F0neMWDo6vQ0; tfstk=gEX-ICOXSr4k2B3r2wV0t3N8tSZDeSjzraSsKeYoOZQAAED34LVepwLA8UAkFUDppMQF-wIU4HTCRwLhZS2G4gJedPYLIRjrvDuqTTpI-i9yxQz0mq2G4gJedP4gIR2pcI_pAXTCRKOXqhvIFYO7DItklYtIFHgbDH8Xd3tWPjwXvH3SFU_CcoKele9BNw9bDH8XRp9IpDhJ8X8Ip_r088P8ZUkIdtKJNSjWlvtVH3dJ5g6-dviw2QL1VEa8ax96GMRdLDkpPg1N8h_SPPAPAsQv2pemNdsAONKVFR0J0_jfjEstYvSye1B9F_UqgLbRhK656DMCDLLy9tAxyrL1Ui6whI2_Xi6VrgWAxDwBmNYf4T9LClJJFU9v094qFeCfOTAyL4aMaM1Ak3p14a6GBxKsSFKnNoExTXRW0zArzghffOQMDFqcmXlei5tvSoExTXRW0nLgmEcETIV1.; isg=BG9vPZ1ZWtJS-l70oSMW7zDd_oN5FMM2ylWRuIH8C17k0I_SieRThm2GUsBuqJuu")
    # 2. 定义要爬取的关键词列表
    TARGET_KEYWORDS = [ '电视柜', '瓷砖', '地毯', '灯具', '装饰画',
                       '厨房', '智能家居', '沙发', '儿童家具', '老人家具', '客厅',
                       '墙漆', '收纳柜', '新中式', '茶几', '节能灯', '吊顶', '卫生间',
                       '地板', '衣柜', '餐桌椅', '欧式奢华', '日式风格', '阳台', '室内绿植',
                       '现代简约', '花瓶', '北欧风格', '卧室']

    # 3. 每个关键词爬多少页
    PAGES_PER_KEYWORD = 8
    # 4. 启动爬虫
    scraper = TaobaoMtopScraper(MY_COOKIE)
    scraper.run(TARGET_KEYWORDS, PAGES_PER_KEYWORD)

