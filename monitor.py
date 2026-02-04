import httpx
import time

async def get_instance_score(url, type="invidious"):
    score = 0
    metrics = {"api": False, "cors": False, "latency": 0}
    
    start_time = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            # 1. API 測試
            target = f"{url}/api/v1/videos/dQw4w9WgXcQ" if type == "invidious" else f"{url}/streams/dQw4w9WgXcQ"
            resp = await client.get(target)
            
            if resp.status_code == 200:
                metrics["api"] = True
                score += 50 # API 正常給予基礎分
                
                # 2. CORS 測試 (模仿 instances-api)
                if "access-control-allow-origin" in resp.headers:
                    metrics["cors"] = True
                    score += 20
                    
            metrics["latency"] = (time.perf_counter() - start_time) * 1000
            
            # 3. 延遲評分 (越快分數越高)
            if metrics["latency"] < 500: score += 30
            elif metrics["latency"] < 1500: score += 15
            
    except:
        return 0, metrics

    return score, metrics