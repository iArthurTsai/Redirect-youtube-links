import httpx
import time
import json
import asyncio
import os

# 1. 你定義的評分核心邏輯
async def get_instance_score(client, url, inst_type="invidious"):
    score = 0
    metrics = {"api": False, "cors": False, "latency": 0}
    url = url.rstrip('/')
    
    start_time = time.perf_counter()
    try:
        # API 測試路徑
        target = f"{url}/api/v1/videos/dQw4w9WgXcQ" if inst_type == "invidious" else f"{url}/streams/dQw4w9WgXcQ"
        resp = await client.get(target, timeout=10.0, follow_redirects=True)
        
        if resp.status_code == 200:
            data = resp.json()
            if "title" in data: # 確保真的有拿到影片資料
                metrics["api"] = True
                score += 50 
                
                # CORS 測試
                if "access-control-allow-origin" in resp.headers:
                    metrics["cors"] = True
                    score += 20
                    
        metrics["latency"] = (time.perf_counter() - start_time) * 1000
        
        # 延遲評分
        if metrics["latency"] < 500: score += 30
        elif metrics["latency"] < 1500: score += 15
            
    except Exception as e:
        print(f"❌ 檢測 {url} 時發生錯誤: {e}")
        return 0, metrics

    return score, metrics

# 2. 執行主邏輯
async def main():
    # 確保讀得到 targets.json
    if not os.path.exists('targets.json'):
        print("CRITICAL: targets.json not found!")
        return

    with open('targets.json', 'r') as f:
        targets = json.load(f)

    print(f"📡 開始監測 {len(targets)} 個站點...")
    
    final_results = []
    
    # 建立一個不驗證 SSL 的客戶端 (有些自建站證書會過期，但不影響使用)
    async with httpx.AsyncClient(verify=False) as client:
        for item in targets:
            url = item['url']
            inst_type = item.get('type', 'invidious')
            
            print(f"正在檢查: {url} ({inst_type})...", end="")
            score, metrics = await get_instance_score(client, url, inst_type)
            
            # 只要 API 活著或是分數大於 0 就記錄
            if score > 0 or metrics['api']:
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

    # 按分數從高到低排序
    final_results.sort(key=lambda x: x['score'], reverse=True)

    # 3. 輸出結果 (這是解決 Actions 報錯的關鍵)
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=4, ensure_ascii=False)
    
    print(f"🎉 監測完成，已產生 data.json (共 {len(final_results)} 個站點)")

if __name__ == "__main__":
    asyncio.run(main())
