import feedparser
import requests
import urllib.parse
import os
from datetime import datetime
from time import mktime

# --- 配置区 ---
SC_KEY = os.environ.get("SC_KEY")

# ✅ 白名单：标题里必须包含这些词之一，才算有效情报
# 这样能过滤掉“新专辑发布”、“歌词赏析”等非演出信息
VALID_KEYWORDS = ["巡演", "演出", "音乐节", "Livehouse", "开票", "阵容", "专场", "站", "购票"]

# 🚫 黑名单：标题里如果有这些词，直接扔掉
# 过滤掉乱七八糟的干扰
KX_KEYWORDS = ["歌词", "下载", "资源", "MP3", "在线试听", "天气", "预报", "小说"]

# --- 核心代码 ---

def get_band_list():
    bands = []
    try:
        with open('bands.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                name = line.strip()
                if name:
                    # Bing 的搜索逻辑：
                    # "乐队名" (巡演 OR 演出 OR 音乐节)
                    # 加上双引号强制匹配名字
                    bands.append({
                        "name": name,
                        "keyword": f'"{name}" (巡演 OR 演出 OR 音乐节 OR 开票)'
                    })
        return bands
    except FileNotFoundError:
        return []

def send_wechat(title, content):
    if not SC_KEY:
        print("⚠️ 未配置 Server酱 Key")
        print(content) # 调试用
        return
    
    url = f"https://sctapi.ftqq.com/{SC_KEY}.send"
    data = {"title": title, "desp": content}
    try:
        requests.post(url, data=data)
        print("✅ 微信推送已发送")
    except Exception as e:
        print(f"❌ 推送失败: {e}")

def check_bing_news():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🌍 切换至 Bing 引擎搜索...")
    
    targets = get_band_list()
    if not targets:
        return

    msg_content = ""
    total_count = 0

    for item in targets:
        # 使用 Bing 的 RSS 接口
        encoded_keyword = urllib.parse.quote(item['keyword'])
        url = f"https://www.bing.com/search?q={encoded_keyword}&format=rss"
        
        try:
            feed = feedparser.parse(url)
            
            if feed.entries:
                band_section = ""
                has_news = False
                
                # 乐队名转小写，用于对比
                band_name_lower = item['name'].lower().replace('"', '').replace('乐队', '')

                for entry in feed.entries[:5]: # 只要前5条
                    title = entry.title
                    link = entry.link
                    
                    # --- 🧹 强力清洗逻辑 ---
                    
                    # 1. 必须包含乐队名 (防止搜“四月雨”出来“四月下雨”)
                    if band_name_lower not in title.lower():
                        continue
                        
                    # 2. 必须包含“白名单”里的词 (必须是演出相关的)
                    # 比如：必须有“巡演”、“开票”、“Livehouse”等字眼
                    if not any(k in title for k in VALID_KEYWORDS):
                        continue

                    # 3. 不能包含“黑名单”里的词
                    if any(k in title for k in KX_KEYWORDS):
                        continue

                    # --- 时间处理 ---
                    # Bing RSS 的时间格式有时候不一样，这里做个容错
                    date_str = "近期"
                    icon = "🔥" # Bing 抓的大多是最近的，默认给火
                    
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime.fromtimestamp(mktime(entry.published_parsed))
                        date_str = pub_date.strftime('%Y-%m-%d')
                        # 如果是30天前的旧闻，图标改一下
                        if (datetime.now() - pub_date).days > 30:
                            icon = "📄"

                    band_section += f"{icon} `{date_str}` [{title}]({link})\n\n"
                    has_news = True
                    total_count += 1
                
                if has_news:
                    msg_content += f"### 🎸 {item['name']}\n{band_section}---\n"
                else:
                    print(f"   [{item['name']}] 暂无符合条件的演出情报 (已过滤无效信息)")

        except Exception as e:
            print(f"❌ 出错 [{item['name']}]: {e}")

    if total_count > 0:
        print("🚀 抓取完成，正在推送...")
        send_wechat(f"🎸 演出情报更新 ({datetime.now().strftime('%m-%d')})", msg_content)
    else:
        print("💤 今天没有发现任何有效的演出情报")

if __name__ == "__main__":
    check_bing_news()
