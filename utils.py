# utils.py (Access Key와 Async/Await 적용 버전)
import math
import json
import config
import urllib.request
import urllib.parse
import asyncio  # Pygbag 비동기 환경을 위해 필요
import pygame

# 랭킹 항목 정의 (동일)
RANK_CATEGORIES = [
  "Levels", "Kills", "Bosses", "DifficultyScore", "SurvivalTime"
]

# ----------------------------------------------------
# 비동기 통신 래퍼 함수 (웹 호환의 핵심)
# ----------------------------------------------------
async def _fetch_data_async(url, headers, method, data=None):
    # 이 코드가 urlopen을 asyncio에 통합하여 웹에서 비동기로 실행되게 함
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        loop = asyncio.get_event_loop()
        # run_in_executor를 사용하여 동기 함수를 비동기로 실행
        response = await loop.run_in_executor(None, urllib.request.urlopen, req)
        print(f"SUCCESS: {method} to {url} returned {response.getcode()}") 
        
        return response.read().decode('utf-8')
    except Exception as e:
        # 401 Unauthorized 에러 등의 상세 정보를 출력해 디버깅 돕기
        if hasattr(e, 'read'):
            error_body = e.read().decode('utf-8')
            # 🟢 추가: 실패 시 상세 정보 출력
            print(f"FAILED: {method} to {url} returned {e.code}. BODY: {error_body}")
            raise e
        else:
            print(f"ASYNC FETCH ERROR: {e}")
        raise e

# ----------------------------------------------------
# 랭킹 저장/로드 함수 (Access Key 사용)
# ----------------------------------------------------

async def load_rankings_jsonbin():
    """JSONbin에서 전체 랭킹 데이터를 GET 요청으로 수신합니다."""
    
    headers = {
        # 🚩 config.JSONBIN_API_KEY에 발급받은 Access Key를 사용하도록 가정
        'X-Access-Key': config.JSONBIN_API_KEY, 
        'Accept': 'application/json'
    }
    
    try:
        data_str = await _fetch_data_async(config.JSONBIN_BIN_URL + "/latest", headers, 'GET')
        return json.loads(data_str).get('record', {}).get('rankings', [])
    except Exception:
        return []

async def save_new_ranking_jsonbin(name, score_data):
    """새 기록을 JSONbin에 PUT 요청으로 덮어씁니다. (Access Key 사용)"""
    
    # 1. 기존 데이터 로드 (비동기 함수 호출)
    current_data = await load_rankings_jsonbin()
    
    # 2. 새 기록 생성 (이전 로직과 동일)
    new_record = {
        "RankCategory": "", 
        "RankValue": 0.0,
        "ID": name,
        "Levels": float(score_data.get('levels', 0.0)),
        "Kills": float(score_data.get('kills', 0.0)),
        "Bosses": float(score_data.get('bosses', 0.0)),
        "DifficultyScore": float(score_data.get('difficulty_score', 0.0)),
        "SurvivalTime": float(score_data.get('survival_time', 0.0))
    }
    
    # 3. 항목별 랭킹 진입 확인 및 추가 로직 (이전 로직과 동일)
    records_to_add = []
    
    for category_key in RANK_CATEGORIES:
        category_score = new_record[category_key]
        
        filtered_rankings = [r for r in current_data if r.get('RankCategory') == category_key]
        filtered_rankings.sort(key=lambda x: x.get('RankValue', 0.0), reverse=True)
        
        if len(filtered_rankings) < 10 or category_score > filtered_rankings[9].get('RankValue', 0.0):
            record_to_add = new_record.copy()
            record_to_add['RankCategory'] = category_key
            record_to_add['RankValue'] = category_score
            records_to_add.append(record_to_add)

    # 4. 랭킹에 든 기록이 있을 경우에만 서버에 PUT 요청
    if records_to_add:
        for record in records_to_add: current_data.append(record)
        
        final_rankings = []
        for category_key in RANK_CATEGORIES:
            category_list = [r for r in current_data if r.get('RankCategory') == category_key]
            category_list.sort(key=lambda x: x.get('RankValue', 0.0), reverse=True)
            final_rankings.extend(category_list[:10])
            
        # 5. JSONbin에 PUT 요청
        data_to_save = {"rankings": final_rankings}
        data_json = json.dumps(data_to_save).encode('utf-8')
        
        headers = {
            'Content-Type': 'application/json',
            'X-Access-Key': config.JSONBIN_API_KEY, # 🚩 Access Key 사용
            'X-Bin-Versioning': 'false' 
        }
        
        try:
            await _fetch_data_async(config.JSONBIN_BIN_URL, headers, 'PUT', data=data_json)
            return {"success": True, "message": "랭킹 저장 완료"}
        except Exception as e:
            return {"success": False, "message": f"저장 오류: {e}"}

    return {"success": True, "message": "10위권 밖 기록, 저장 안 함"}


# 🚩 main.py에서 비동기 함수로 직접 호출할 수 있도록 함수 이름 변경
load_rankings_online = load_rankings_jsonbin 
save_new_ranking_online = save_new_ranking_jsonbin

# ... (기존 utils 함수는 그대로 유지)
def get_wrapped_delta(val1, val2, map_dim):
    delta = val2 - val1
    if abs(delta) > map_dim / 2:
        if delta > 0: delta -= map_dim
        else: delta += map_dim
    return delta

def distance_sq_wrapped(x1, y1, x2, y2, map_w, map_h):
    dx = get_wrapped_delta(x1, x2, map_w)
    dy = get_wrapped_delta(y1, y2, map_h)
    return dx*dx + dy*dy