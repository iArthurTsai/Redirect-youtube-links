import httpx
import time
import json
import asyncio
import os

# 1. 強化版評分核心邏輯
async def get_instance_score(client, url, inst_type="invidious"):
    score = 0
    metrics = {"api": False, "cors": False, "latency": 0}
    url = url.rstrip('/')
    
    # 準備兩組策略：一組模擬瀏覽器，一組完全裸奔
    strategies = [
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
        {} # 空標頭，有時反而能過
    ]
    
    test_path = "/api/v1/videos/dQw4w9WgXcQ" if inst_type == "invidious" else "/streams/dQw4w9WgXcQ"
    
    for headers in strategies:
        start_time = time.perf_counter()
        try:
            resp = await client.get(url + test_path, timeout=12.0, follow_redirects=True, headers=headers)
            metrics["latency"] = (time.perf_counter() - start_time) * 1000
            
            if resp.status_code == 200:
                data = resp.json()
                if "title" in data:
                    metrics["api"] = True
                    score += 50
                    if "access-control-allow-origin" in resp.headers:
                        metrics["cors"] = True
                        score += 20
                    break # 只要有一種策略成功就跳出迴圈
            else:
                print(f" [HTTP {resp.status_code} with { 'Headers' if headers else 'No-Header' }]", end="")
        except Exception:
            continue

    # 延遲評分
    if metrics["api"]:
        if metrics["latency"] < 800: score += 30
        elif metrics["latency"] < 2000: score += 15
            
    return score, metrics
# 2. 執行主邏輯
async def main():
    if not os.path.exists('targets.json'):
        print("CRITICAL: targets.json not found!")
        return

    with open('targets.json', 'r') as f:
        targets = json.load(f)

    print(f"📡 啟動系統監測，目標：{len(targets)} 個站點...")
    
    final_results = []
    
    # 使用無視 SSL 憑證的客戶端
    async with httpx.AsyncClient(verify=False) as client:
        for item in targets:
            url = item['url']
            inst_type = item.get('type', 'invidious')
            
            print(f"正在檢查: {url} ({inst_type})...", end="", flush=True)
            score, metrics = await get_instance_score(client, url, inst_type)
            
            if metrics['api']:
                final_results.append({
                    "url": url,
                    "type": inst_type,
                    "score": score,
                    "latency": f"{int(metrics['latency'])}ms",
                    "cors": metrics['cors'],
                    "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                print(f" ✅ {score}分")
            else:
                print(" ❌ 失效")

    # 按分數排序
    final_results.sort(key=lambda x: x['score'], reverse=True)

    # 3. 輸出結果
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=4, ensure_ascii=False)
    
    print(f"🎉 更新完畢！已將 {len(final_results)} 個活體實例寫入 data.json")

if __name__ == "__main__":

    asyncio.run(main())
