# utils.py (JSONbin.io 온라인 통신 버전 - 클린)
import math
import json
import config
import urllib.request
import urllib.parse
import pygame 

# 랭킹 항목 정의 (정렬 및 필터링에 사용)
RANK_CATEGORIES = [
  "Levels", "Kills", "Bosses", "DifficultyScore", "SurvivalTime"
]

# ----------------------------------------------------
# 랭킹 저장/로드 함수 (JSONbin.io 버전)
# ----------------------------------------------------

def load_rankings_jsonbin():
    """JSONbin에서 전체 랭킹 데이터를 GET 요청으로 수신합니다."""
    
    req = urllib.request.Request(
        config.JSONBIN_BIN_URL + "/latest", 
        headers={'X-Master-Key': config.JSONBIN_API_KEY, 'Accept': 'application/json'},
        method='GET'
    )
    
    try:
        # 들여쓰기 수정 완료
        with urllib.request.urlopen(req) as response:
            data = response.read().decode('utf-8')
            return json.loads(data).get('record', {}).get('rankings', [])
    except Exception as e:
        print(f"ERROR: 랭킹 로드 실패: {e}")
        return []

def save_new_ranking_jsonbin(name, score_data):
    """새 기록을 JSONbin의 기존 랭킹에 통합하고, 전체 데이터를 PUT 요청으로 덮어씁니다."""
    
    # 1. 기존 데이터 로드
    current_data = load_rankings_jsonbin()
    
    # 2. 새 기록 생성 (score_data의 키를 main.py와 일치하도록 수정: level -> levels)
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
    
    # 3. 항목별 랭킹 진입 확인 및 추가 로직
    records_to_add = []
    
    for category_key in RANK_CATEGORIES:
        category_score = new_record[category_key]
        
        filtered_rankings = [
            r for r in current_data 
            if r.get('RankCategory') == category_key
        ]
        
        filtered_rankings.sort(key=lambda x: x.get('RankValue', 0.0), reverse=True)
        
        if len(filtered_rankings) < 10 or category_score > filtered_rankings[9].get('RankValue', 0.0):
            record_to_add = new_record.copy()
            record_to_add['RankCategory'] = category_key
            record_to_add['RankValue'] = category_score
            records_to_add.append(record_to_add)

    # 4. 랭킹에 든 기록이 있을 경우에만 서버에 PUT 요청
    if records_to_add:
        for record in records_to_add:
            current_data.append(record)
        
        final_rankings = []
        for category_key in RANK_CATEGORIES:
            category_list = [r for r in current_data if r.get('RankCategory') == category_key]
            category_list.sort(key=lambda x: x.get('RankValue', 0.0), reverse=True)
            final_rankings.extend(category_list[:10])
            
        data_to_save = {"rankings": final_rankings}
        data_json = json.dumps(data_to_save).encode('utf-8')
        
        req = urllib.request.Request(
            config.JSONBIN_BIN_URL, 
            data=data_json, 
            headers={
                'Content-Type': 'application/json',
                'X-Master-Key': config.JSONBIN_API_KEY,
                'X-Bin-Versioning': 'false' 
            },
            method='PUT'
        )
        try:
            with urllib.request.urlopen(req) as response:
                response.read()
                return {"success": True, "message": "저장 완료"}
        except Exception as e:
            return {"success": False, "message": f"저장 오류: {e}"}

    return {"success": True, "message": "10위권 밖 기록"}

# 🚩 함수 이름 매핑
load_rankings_online = load_rankings_jsonbin 
save_new_ranking_online = save_new_ranking_jsonbin

# 기존 유틸 함수들
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