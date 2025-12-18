import feedparser
import requests
import urllib.parse
import os
from datetime import datetime, timedelta

# --- 配置区 ---

# 关键词列表
# 格式：{"name": "显示名称", "keyword": "搜索关键词"}
TARGETS = [
    {"name": "万能青年旅店", "keyword": "万能青年旅店 巡演 OR 演出"},
    {"name": "痛仰乐队", "keyword": "痛仰乐队 巡演 OR 演出"},
]

# Server酱 Key (可选)
SC_KEY = os.environ.get("SC_KEY")

# --- 核心代码 ---

def send_wechat(title, content):
    if not SC_KEY:
        print("⚠️ 未配置 Server酱 Key，跳过推送")
        return
    url = f"https://sctapi.ftqq.com/{SC_KEY}.send"
    data = {"title": title, "desp": content}
    try:
        requests.post(url, data=data)
        print("✅ 微信推送已发送")
    except Exception as e:
        print(f"❌ 推送失败: {e}")

def check_google_news():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🌍 连接 Google News RSS...")
    
    has_new_info = False
    msg_content = ""

    for item in TARGETS:
        # 构建 Google News RSS URL (针对中文环境)
        encoded_keyword = urllib.parse.quote(item['keyword'])
        url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=zh-CN&gl=CN&ceid=CN:zh-CN"
        
        try:
            # 解析 RSS
            # Google News 对 GitHub 非常友好，不需要特殊 Header
            feed = feedparser.parse(url)
            
            if not feed.entries:
                print(f"☁️ [{item['name']}] 暂无相关新闻")
                continue

            print(f"✅ [{item['name']}] 发现 {len(feed.entries)} 条相关资讯，正在筛选...")

            # 遍历前 3 条，寻找最近发布的内容
            found_for_this_band = False
            for entry in feed.entries[:3]:
                title = entry.title
                link = entry.link
                published = entry.get('published', '')
                
                # Google RSS 的时间格式通常是: "Mon, 29 Sep 2025 08:00:00 GMT"
                # 这里我们简单做个展示，不做复杂的日期比对，直接把最新的推给你
                
                print(f"   - 标题: {title}")
                print(f"   - 时间: {published}")
                
                # 这里的逻辑是：只要有新闻，就记录下来
                # 实际使用中，你可以加上日期判断，比如只推最近 2 天的
                # 为了演示效果，我们先把第一条最新的加进去
                
                if not found_for_this_band:
                    msg_content += f"## {item['name']}\n{title}\n时间：{published}\n[点击阅读]({link})\n\n"
                    found_for_this_band = True
                    has_new_info = True

        except Exception as e:
            print(f"❌ 出错 [{item['name']}]: {e}")

    if has_new_info:
        print("🔥 发现演出情报，准备推送...")
        send_wechat("🎸 乐队巡演情报 (Google源)", msg_content)
    else:
        print("💤 今日无新情报")

if __name__ == "__main__":
    check_google_news()
