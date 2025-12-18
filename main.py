import feedparser
import requests
import os
import time
from datetime import datetime, timedelta

# --- 配置区 ---

# 微博 UID
TARGETS = [
    {"name": "万能青年旅店", "uid": "1736760581"},
    {"name": "痛仰乐队", "uid": "1662260795"},
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

def check_rss():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🌍 连接 RSSHub 官方节点 (rsshub.app)...")
    
    has_new_info = False
    msg_content = ""

    for band in TARGETS:
        # 使用 RSSHub 官方提供的微博接口
        # 格式: https://rsshub.app/weibo/user/{uid}
        url = f"https://rsshub.app/weibo/user/{band['uid']}"
        
        try:
            # 解析 RSS
            feed = feedparser.parse(url)
            
            if not feed.entries:
                print(f"☁️ [{band['name']}] 获取成功，但暂无条目 (或 RSSHub 正在缓存)")
                continue

            # 获取最新一条
            entry = feed.entries[0]
            title = entry.title
            link = entry.link
            published = entry.get('published', '未知时间')
            
            print(f"✅ [{band['name']}] 最新: {title[:30]}...")

            # 简单的判断逻辑：
            # 检查发布时间是否在过去 24 小时内 (GitHub Actions 每天跑一次)
            # RSSHub 的时间格式通常是标准格式，这里为了简化，我们直接看内容
            
            # 关键词过滤
            keywords = ["巡演", "演出", "开票", "音乐节", "Live"]
            if any(k in title for k in keywords):
                # 再次确认时间，防止把旧新闻重复推
                # 这里做一个简单的处理：如果标题里包含了关键词，就打印出来供人工确认
                # 进阶版应该存一个 history.json 到 GitHub Artifacts，但那样太复杂
                
                msg_content += f"## {band['name']}\n{title}\n[查看微博]({link})\n\n"
                has_new_info = True

        except Exception as e:
            print(f"❌ 出错 [{band['name']}]: {e}")

    if has_new_info:
        print("🔥 发现演出信息，准备推送...")
        send_wechat("🎸 乐队巡演日报", msg_content)
    else:
        print("💤 今日无新巡演消息")

if __name__ == "__main__":
    check_rss()
