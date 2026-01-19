"""
크립토 인사이트 대시보드 V8.3 (Final Complete Edition)
==============================================================
[V8.3 핵심 기능]
1. 🎯 Sell Score Engine: 5가지 지표 가중치 합산 (0-100점)
2. 📅 분할 매도 캘린더: 점수에 따라 매도 날짜와 수량을 자동 계산
3. 🤖 MVRV 자동/수동 하이브리드: 웹 데이터 수집 시도 후 실패 시 수동 전환
4. 👨‍⚖️ AI 위원회 One-Voice: 여러 AI의 의견을 하나로 통합
5. ⚡ 액션 중심 UI: 접속하자마자 '지금 해야 할 행동' 표시

[V8.2 업데이트]
1. 🎯 Sell Score Engine: 0-100 점수 기반 매도 신호 시스템
2. 📊 포트폴리오 리스크 지수: 전체 자산 위험도 한눈에
3. 🔔 텔레그램 알림 강화: Sell Score 기반 알림
4. ⏰ 점수 변화 속도 감지: Blow-off Top 조기 경보
5. 🐛 plotly_chart 중복 ID 에러 수정

[V8.1 업데이트]
1. 🌡️ 시장 심리 지표: 공포탐욕지수, BTC 도미넌스, 알트시즌 지수
2. 📜 AI 위원회 히스토리: 과거 투표 결과 저장 및 비교
3. 📊 총 시가총액/24h 변동률 표시
4. 🔧 모델 ID 최신화 (Claude Sonnet 4)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
import feedparser
from datetime import datetime, timedelta
import time
import re
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO

# -----------------------------------------------------------------------------
# 라이브러리 임포트 (예외 처리)
# -----------------------------------------------------------------------------
try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    from ta.momentum import RSIIndicator
    from ta.trend import SMAIndicator, MACD
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False

try:
    from fredapi import Fred
    FRED_AVAILABLE = True
except ImportError:
    FRED_AVAILABLE = False

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

# -----------------------------------------------------------------------------
# 페이지 설정 & CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="크립토 인사이트 V8.3",
    page_icon="🐋",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #f8fafc; color: #1e293b; }
    .metric-card { background: white; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .kimchi-badge { padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 0.9em; display: inline-block; }
    .k-red { background-color: #fee2e2; color: #991b1b; border: 1px solid #f87171; }
    .k-blue { background-color: #dbeafe; color: #1e40af; border: 1px solid #60a5fa; }
    .k-green { background-color: #dcfce7; color: #166534; border: 1px solid #4ade80; }
    
    .info-label { font-size: 0.85em; color: #6b7280; margin-bottom: 2px; }
    .info-value { font-size: 1.1em; font-weight: 700; color: #111827; }
    
    .news-card { padding: 10px; border-bottom: 1px solid #eee; }
    .news-source { font-size: 0.8em; color: #64748b; font-weight: bold; }
    .news-title { font-size: 1.0em; font-weight: 600; color: #1e293b; text-decoration: none; }
    .news-title:hover { color: #2563eb; text-decoration: underline; }
    
    .ai-box { background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 15px; border-radius: 8px; margin-top: 10px; }
    .alert-box { padding: 15px; border-radius: 8px; margin-bottom: 10px; font-weight: bold; }
    .alert-danger { background-color: #fee2e2; color: #991b1b; }
    .alert-success { background-color: #dcfce7; color: #166534; }
    .scroll-box { height: 200px; overflow-y: auto; background-color: #ffffff; padding: 15px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 0.95em; line-height: 1.6; color: #334155; }
    
    /* [V6.8] 목표가 가이드 스타일 */
    .target-guide-box {
        background-color: #eff6ff; 
        border: 1px solid #bfdbfe; 
        border-radius: 8px; 
        padding: 12px; 
        margin-top: 10px; 
        margin-bottom: 10px;
    }
    .guide-title { font-size: 0.9em; font-weight: bold; color: #1e40af; margin-bottom: 8px; border-bottom: 1px solid #dbeafe; padding-bottom: 4px; }
    .guide-row { display: flex; justify-content: space-between; font-size: 0.85em; margin-bottom: 4px; }
    .guide-label { color: #475569; }
    .guide-val { font-weight: bold; color: #0f172a; cursor: pointer; }
    
    .twitter-btn { display: block; width: 100%; padding: 10px; background-color: #1DA1F2; color: white !important; border-radius: 8px; text-align: center; text-decoration: none; font-weight: bold; }
    
    /* [V7.9] 24시간 변동률 스타일 */
    .change-positive { color: #16a34a; font-weight: bold; }
    .change-negative { color: #dc2626; font-weight: bold; }
    .change-neutral { color: #6b7280; }
    
    /* [V7.9] 모바일 반응형 스타일 */
    @media (max-width: 768px) {
        .stApp { padding: 0.5rem; }
        [data-testid="column"] { padding: 0.25rem !important; }
        .stMetric { font-size: 0.85em; }
        .stDataFrame { font-size: 0.8em; }
        h1 { font-size: 1.5rem !important; }
        h3 { font-size: 1.1rem !important; }
        .kimchi-badge { font-size: 0.75em; padding: 3px 8px; }
    }
    
    /* [V7.9] 김치 프리미엄 테이블 스타일 */
    .kimchi-table { width: 100%; border-collapse: collapse; font-size: 0.9em; }
    .kimchi-table th, .kimchi-table td { padding: 8px; text-align: center; border-bottom: 1px solid #e5e7eb; }
    .kimchi-table th { background-color: #f3f4f6; font-weight: 600; }
    
    /* [V8.3] 행동 지침 카드 (최상단) */
    .action-card {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: white;
        padding: 30px;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(37, 99, 235, 0.2);
        margin-bottom: 25px;
        text-align: center;
    }
    .action-title { font-size: 1.2em; opacity: 0.9; margin-bottom: 10px; font-weight: 500; }
    .action-main { font-size: 2.5em; font-weight: 800; margin-bottom: 15px; letter-spacing: -1px; }
    .action-sub { 
        font-size: 1.1em; 
        background: rgba(255,255,255,0.15); 
        padding: 8px 20px; 
        border-radius: 30px; 
        display: inline-block; 
        backdrop-filter: blur(5px);
    }
    
    /* [V8.3] Sell Score 박스 */
    .metric-container {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* [V8.3] 캘린더 스타일 */
    .calendar-box {
        background: #ffffff;
        border-left: 5px solid #3b82f6;
        padding: 20px;
        border-radius: 8px;
        margin-top: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 세션 상태 초기화
# -----------------------------------------------------------------------------
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'manual_data' not in st.session_state:
    st.session_state.manual_data = {'mvrv_zscore': 2.2, 'coinbase_rank': 50, 'ism_pmi': 48.0}
if 'telegram' not in st.session_state:
    st.session_state.telegram = {'bot_token': '', 'chat_id': '', 'enabled': False}
if 'sent_alerts' not in st.session_state:
    st.session_state.sent_alerts = set()
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False

# [V7.9] API 키 세션 상태 초기화
if 'gemini_key' not in st.session_state:
    st.session_state.gemini_key = ""
if 'openai_key' not in st.session_state:
    st.session_state.openai_key = ""
if 'claude_key' not in st.session_state:
    st.session_state.claude_key = ""
if 'grok_key' not in st.session_state:
    st.session_state.grok_key = ""
if 'groq_key' not in st.session_state:  # [V8.0] Groq 오픈소스 모델용
    st.session_state.groq_key = ""
if 'telegram_id' not in st.session_state:
    st.session_state.telegram_id = ""

# -----------------------------------------------------------------------------
# [V7.5] Firebase 연동 함수
# -----------------------------------------------------------------------------
def init_firebase():
    """Streamlit Secrets를 이용해 Firebase에 연결"""
    if not FIREBASE_AVAILABLE:
        return None
    
    if not firebase_admin._apps:
        try:
            cred_dict = dict(st.secrets["firebase"])
            cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Firebase 연결 실패: {e}")
            return None
    
    return firestore.client()

def load_user_data(username):
    """Firestore에서 사용자 데이터 불러오기"""
    db = init_firebase()
    if not db:
        return None
    
    try:
        doc_ref = db.collection("users").document(username)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        else:
            return {
                "portfolio": [], 
                "manual_data": {'mvrv_zscore': 2.2, 'coinbase_rank': 50, 'ism_pmi': 48.0},
                "telegram": {'bot_token': '', 'chat_id': '', 'enabled': False},
                "api_keys": {"gemini": "", "fred": "", "openai": "", "claude": "", "grok": "", "groq": ""}
            }
    except Exception as e:
        st.warning(f"데이터 로드 실패: {e}")
        return None

def save_user_data(username):
    """Firestore에 사용자 데이터 저장"""
    db = init_firebase()
    if not db or not username:
        return False
    
    try:
        data = {
            "portfolio": st.session_state.portfolio,
            "manual_data": st.session_state.manual_data,
            "telegram": st.session_state.telegram,
            "api_keys": {
                "gemini": st.session_state.get("gemini_key", ""),
                "fred": st.session_state.get("fred_key", ""),
                "openai": st.session_state.get("openai_key", ""),
                "claude": st.session_state.get("claude_key", ""),
                "grok": st.session_state.get("grok_key", ""),
                "groq": st.session_state.get("groq_key", "")  # [V8.0] Groq 추가
            }
        }
        db.collection("users").document(username).set(data)
        return True
    except Exception as e:
        st.warning(f"데이터 저장 실패: {e}")
        return False

# [수정 3-1] 자산 이력(History) 저장 함수 추가
def update_asset_history(username, total_krw):
    """현재 총 자산을 Firestore의 history 컬렉션에 저장"""
    if not username or total_krw == 0: 
        return

    try:
        db = init_firebase()
        if not db:
            return
            
        today = datetime.now().strftime("%Y-%m-%d")
        
        # users -> username -> history -> 날짜 문서 생성
        doc_ref = db.collection("users").document(username).collection("history").document(today)
        doc_ref.set({
            "date": today,
            "total_krw": total_krw,
            "timestamp": firestore.SERVER_TIMESTAMP
        }, merge=True)
        # (성공 시 별도 메시지 없이 조용히 저장)
    except Exception as e:
        print(f"히스토리 저장 실패: {e}")

# -----------------------------------------------------------------------------
# [V7.9] AI 모델 호출 함수 및 위원회 (Grok 완벽 지원)
# -----------------------------------------------------------------------------

# 1. 모델 ID 설정 (2025년 1월 기준 최신 버전)
MODELS = {
    "OPENAI": "gpt-4o",                 
    "ANTHROPIC": "claude-sonnet-4-20250514",  # Claude Sonnet 4 최신
    "GOOGLE": "gemini-1.5-flash",               # REST API용         
    "XAI": "grok-2-latest",              # Grok 2 최신 버전
    # Groq 오픈소스 모델들 (https://console.groq.com/keys 에서 API 키 발급)
    # Meta Llama 모델만 사용 (미국 개발사)
    "GROQ_LLAMA": "llama-3.3-70b-versatile",       # Meta - 범용 분석 (안정적)
    "GROQ_LLAMA4": "meta-llama/llama-4-scout-17b-16e-instruct",  # Meta - 최신 Llama 4
}

# 2. 각 AI 호출 함수들
def ask_gemini(api_key, prompt, system_prompt="You are a helpful assistant. Answer in Korean."):
    """Google Gemini REST API 직접 호출 (라이브러리 의존 없음)"""
    if not api_key:
        return "⚠️ API Key가 없습니다."
    
    api_key = api_key.strip()
    
    # 1. 먼저 사용 가능한 모델 목록 조회
    available_models = []
    try:
        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        list_res = requests.get(list_url, timeout=10)
        
        if list_res.status_code == 200:
            models_data = list_res.json().get('models', [])
            for m in models_data:
                model_name = m.get('name', '').replace('models/', '')
                # generateContent 지원하는 모델만
                if 'generateContent' in str(m.get('supportedGenerationMethods', [])):
                    available_models.append(model_name)
        elif list_res.status_code == 400:
            error = list_res.json().get('error', {}).get('message', '')
            return f"❌ API 키 오류: {error}"
        else:
            # 목록 조회 실패해도 계속 진행
            pass
    except:
        pass
    
    # 2. 사용할 모델 결정
    preferred_models = ["gemini-2.0-flash-exp", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro", "gemini-1.0-pro"]
    
    models_to_try = []
    if available_models:
        # 사용 가능한 모델 중에서 선호 순서대로
        for pref in preferred_models:
            if pref in available_models:
                models_to_try.append(pref)
        # 나머지 사용 가능한 모델도 추가
        for am in available_models:
            if am not in models_to_try and 'gemini' in am:
                models_to_try.append(am)
    else:
        models_to_try = preferred_models
    
    if not models_to_try:
        return f"❌ 사용 가능한 모델 없음. 조회된 모델: {available_models}"
    
    # 3. 모델 호출 시도
    last_error = ""
    for model in models_to_try[:5]:  # 최대 5개만 시도
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            
            headers = {"Content-Type": "application/json"}
            data = {
                "contents": [
                    {"parts": [{"text": f"{system_prompt}\n\n{prompt}"}]}
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 1000
                }
            }
            
            res = requests.post(url, headers=headers, json=data, timeout=30)
            
            if res.status_code == 200:
                result = res.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    return result['candidates'][0]['content']['parts'][0]['text']
                else:
                    last_error = f"{model}: 응답 비어있음"
                    continue
            else:
                error_msg = res.json().get('error', {}).get('message', res.text)[:100]
                last_error = f"{model}: {res.status_code} - {error_msg}"
                continue
                    
        except Exception as e:
            last_error = f"{model}: {str(e)[:50]}"
            continue
    
    return f"❌ Gemini 실패: {last_error}. 사용가능모델: {available_models[:3]}"

def ask_chatgpt(api_key, prompt):
    """OpenAI GPT 호출 - 펀드매니저 역할"""
    if not api_key: 
        return "⚠️ API Key가 없습니다."
    try:
        headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
        data = {
            "model": MODELS["OPENAI"],
            "messages": [
                {"role": "system", "content": "당신은 10년 경력의 펀드매니저입니다. 리스크 대비 수익률을 중시하며, 포트폴리오 분산과 자산 배분 관점에서 분석합니다. 한국어로 답변하세요."}, 
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5
        }
        res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=20)
        return res.json()['choices'][0]['message']['content'] if res.status_code == 200 else f"오류: {res.text}"
    except Exception as e: 
        return f"연결 실패: {e}"

def ask_claude(api_key, prompt):
    """Anthropic Claude 호출 - 데이터 분석가 역할"""
    if not api_key: 
        return "⚠️ API Key가 없습니다."
    try:
        headers = {"x-api-key": api_key.strip(), "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
        data = {
            "model": MODELS["ANTHROPIC"],
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}],
            "system": "당신은 온체인 데이터와 기술적 지표를 전문으로 하는 데이터 분석가입니다. 숫자와 차트 패턴을 기반으로 객관적이고 냉철하게 분석합니다. 한국어로 답변하세요."
        }
        res = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data, timeout=20)
        return res.json()['content'][0]['text'] if res.status_code == 200 else f"오류: {res.text}"
    except Exception as e: 
        return f"연결 실패: {e}"

def ask_grok(api_key, prompt):
    """xAI (Grok) API 호출 - 거시경제 분석 전문가 역할"""
    if not api_key: 
        return "⚠️ API Key가 없습니다."
    try:
        headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
        data = {
            "model": MODELS["XAI"],
            "messages": [
                {"role": "system", "content": "당신은 거시경제 분석 전문가입니다. 금리, 인플레이션, 달러 강세, 연준 정책 등 매크로 환경이 암호화폐에 미치는 영향을 분석합니다. 한국어로 답변하세요."}, 
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        res = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=data, timeout=20)
        
        if res.status_code == 200:
            return res.json()['choices'][0]['message']['content']
        else:
            return f"❌ Grok 오류 ({res.status_code}): {res.text}"
    except Exception as e: 
        return f"Grok 연결 실패: {e}"

# -----------------------------------------------------------------------------
# [V8.0] Groq API 호출 함수들 (오픈소스 모델)
# Groq은 Meta Llama 등 오픈소스 모델을 초고속으로 서빙
# API 키 발급: https://console.groq.com/keys
# -----------------------------------------------------------------------------
def ask_groq(api_key, prompt, model_key="GROQ_LLAMA", system_prompt="You are a helpful assistant. Answer in Korean."):
    """Groq API 범용 호출 함수 (OpenAI 호환 형식)"""
    if not api_key: 
        return "⚠️ Groq API Key가 없습니다."
    
    model = MODELS.get(model_key, "llama-3.3-70b-versatile")
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key.strip()}", 
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt}, 
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions", 
            headers=headers, 
            json=data, 
            timeout=30
        )
        
        if res.status_code == 200:
            return res.json()['choices'][0]['message']['content']
        else:
            error_msg = res.json().get('error', {}).get('message', res.text)[:100]
            return f"❌ Groq 오류 ({res.status_code}): {error_msg}"
    except Exception as e: 
        return f"Groq 연결 실패: {e}"

def ask_groq_llama(api_key, prompt):
    """Groq Llama 3.3 70B - 온체인 데이터 분석가 역할"""
    system_prompt = """당신은 온체인 데이터와 기술적 지표를 전문으로 하는 데이터 분석가입니다. 
    MVRV, 거래량, 활성 주소 수, 해시레이트 등 블록체인 데이터를 기반으로 객관적이고 냉철하게 분석합니다. 
    숫자와 데이터에 기반한 논리적 분석을 제공합니다. 한국어로 답변하세요."""
    return ask_groq(api_key, prompt, "GROQ_LLAMA", system_prompt)

def ask_groq_llama4(api_key, prompt):
    """Groq Llama 4 Scout - 리스크 관리 및 균형 분석 역할"""
    system_prompt = """당신은 암호화폐 투자의 리스크 관리 전문가입니다.
    변동성, 하락 위험, 포트폴리오 집중도 등을 분석하고 위험 요소를 식별합니다.
    낙관론과 비관론 양쪽을 균형있게 고려하여 신중한 투자 조언을 제공합니다.
    한국어로 답변하세요."""
    return ask_groq(api_key, prompt, "GROQ_LLAMA4", system_prompt)

# =============================================================================
# [V8.3 ENGINE 1] Sell Score 계산 엔진
# =============================================================================
def calc_total_sell_score(mvrv, rsi, fng, btc_dom, dxy_rising):
    """
    종합 매도 점수 계산 (0~100점)
    가중치: MVRV(25) + RSI(25) + FnG(20) + Dom/Macro(30)
    """
    score = 0
    reasons = []
    
    # 1. MVRV Z-Score (25점)
    if mvrv >= 7.0: score += 25; reasons.append("🔥 MVRV 역사적 고점 (7.0+)")
    elif mvrv >= 5.0: score += 20; reasons.append("⚠️ MVRV 고평가 구간 (5.0+)")
    elif mvrv >= 3.0: score += 10; reasons.append("📈 MVRV 상승세 진입")
    
    # 2. RSI (주봉 기준) (25점)
    if rsi >= 85: score += 25; reasons.append(f"🔥 RSI 극단적 과열 ({rsi:.0f})")
    elif rsi >= 75: score += 20; reasons.append(f"⚠️ RSI 과열 ({rsi:.0f})")
    elif rsi >= 70: score += 15
    
    # 3. 공포탐욕지수 (20점)
    if fng >= 90: score += 20; reasons.append(f"😱 극단적 탐욕 ({fng})")
    elif fng >= 80: score += 15; reasons.append(f"😨 강한 탐욕 ({fng})")
    elif fng >= 70: score += 10
    
    # 4. 시장 구조 (도미넌스 & 매크로) (30점)
    if btc_dom <= 40: score += 15; reasons.append("📉 도미넌스 저점 (알트 과열)")
    if dxy_rising: score += 15; reasons.append("💵 달러 강세 (시장 압박)")
    
    final_score = min(score, 100)
    return final_score, reasons

def get_action_plan(score):
    """점수에 따른 행동 지침 반환"""
    if score >= 85:
        return "🚨 전량 매도 (EXIT)", "사이클 고점입니다. 뒤도 돌아보지 말고 떠나세요.", "#991b1b"
    elif score >= 70:
        return "🔴 적극 매도", "현금 비중을 70% 이상으로 늘리세요.", "#ef4444"
    elif score >= 50:
        return "🟠 분할 매도 시작", "상승 시마다 10~20%씩 수익 실현하세요.", "#f97316"
    elif score >= 30:
        return "🟡 관망 (HOLD)", "아직 추세가 꺾이지 않았습니다. 추세를 즐기세요.", "#eab308"
    else:
        return "🟢 매수/보유", "저점 구간입니다. 수량을 모아가세요.", "#22c55e"

# =============================================================================
# [V8.3 ENGINE 2] 분할 매도 캘린더 생성 엔진
# =============================================================================
def generate_sell_calendar(score, current_qty):
    """
    Sell Score에 기반하여 최적의 분할 매도 스케줄 생성
    Returns: Pandas DataFrame
    """
    if score < 50:
        return None  # 매도 구간 아님
    
    calendar = []
    start_date = datetime.now()
    
    # 점수대별 전략 설정
    if score >= 85: # [긴급] 빠르게 털고 나가기
        plan = [
            (0.5, 0),  # 오늘 50%
            (0.3, 1),  # 내일 30%
            (0.2, 2)   # 모레 20%
        ]
    elif score >= 70: # [적극] 1주일 내 정리
        plan = [
            (0.3, 0),  # 오늘 30%
            (0.3, 3),  # 3일 뒤 30%
            (0.4, 7)   # 7일 뒤 40%
        ]
    else: # [분할] 느긋하게 정리 (50~70점)
        plan = [
            (0.2, 0),  # 오늘 20%
            (0.2, 7),  # 7일 뒤 20%
            (0.2, 14), # 14일 뒤 20%
            (0.2, 21), # 21일 뒤 20%
            (0.2, 30)  # 30일 뒤 20%
        ]
        
    # 캘린더 데이터 생성
    accumulated_qty = 0
    for ratio, days in plan:
        sell_date = start_date + timedelta(days=days)
        sell_amount = current_qty * ratio
        accumulated_qty += sell_amount
        
        calendar.append({
            "날짜": sell_date.strftime("%Y-%m-%d"),
            "구분": "오늘" if days == 0 else f"D+{days}",
            "매도 비율": f"{ratio*100:.0f}%",
            "매도 수량": sell_amount,
            "매도 후 잔액": current_qty - accumulated_qty
        })
        
    return pd.DataFrame(calendar)

# =============================================================================
# [V8.3 ENGINE 3] 통합 시장 데이터 수집 (Sell Score용)
# =============================================================================
@st.cache_data(ttl=300)
def get_market_data_v83():
    """시장 데이터 조회 (오류 시 기본값 반환)"""
    data = {'btc_price': 0, 'dom': 50, 'fng': 50, 'dxy_chg': 0}
    try:
        # 1. CoinGecko (Dominance)
        cg_res = requests.get("https://api.coingecko.com/api/v3/global", timeout=5).json()
        data['dom'] = cg_res['data']['market_cap_percentage']['btc']
        
        # 2. Alternative.me (FnG)
        fng_res = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5).json()
        data['fng'] = int(fng_res['data'][0]['value'])
        
        # 3. Yfinance (DXY)
        if YFINANCE_AVAILABLE:
            dxy = yf.Ticker("DX-Y.NYB").history(period="5d")
            if len(dxy) >= 2:
                # MultiIndex 처리
                close_col = dxy['Close']
                if hasattr(close_col, 'iloc'):
                    curr_val = float(close_col.iloc[-1]) if len(close_col.shape) == 1 else float(close_col.iloc[-1, 0])
                    prev_val = float(close_col.iloc[-2]) if len(close_col.shape) == 1 else float(close_col.iloc[-2, 0])
                    data['dxy_chg'] = (curr_val - prev_val) / prev_val * 100
    except:
        pass # API 오류 시 기본값 유지
    return data

@st.cache_data(ttl=3600)
def get_btc_ohlcv_weekly():
    """BTC 주봉 데이터 (RSI 계산용)"""
    if YFINANCE_AVAILABLE:
        try:
            df = yf.download("BTC-USD", period="2y", interval="1wk", progress=False)
            if not df.empty:
                # MultiIndex 컬럼 처리
                if isinstance(df.columns, pd.MultiIndex):
                    return pd.DataFrame({
                        'Close': df['Close'].iloc[:, 0] if len(df['Close'].shape) > 1 else df['Close']
                    })
                return df[['Close']]
        except: 
            pass
    return None

def get_current_mvrv():
    """
    MVRV 값 조회 전략:
    1. (추후) 웹 스크래핑 로직 시도
    2. 실패 시 수동 입력값 사용
    """
    # 현재는 안정성을 위해 바로 수동값 반환 (스크래핑 로직은 별도 모듈 필요)
    return st.session_state.manual_data.get('mvrv_zscore', 2.2), False

# -----------------------------------------------------------------------------
# 데이터 함수 (API)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300)
def get_usd_krw_rate():
    try:
        if YFINANCE_AVAILABLE:
            hist = yf.Ticker("KRW=X").history(period="1d")
            if not hist.empty: return float(hist['Close'].iloc[-1])
    except: pass
    return 1450.0

# -----------------------------------------------------------------------------
# [V8.1] 시장 심리 지표 API 함수들
# -----------------------------------------------------------------------------
@st.cache_data(ttl=600)  # 10분 캐시
def get_fear_greed_index():
    """Alternative.me API에서 공포탐욕지수 조회"""
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()['data'][0]
            return {
                'value': int(data['value']),
                'classification': data['value_classification'],
                'timestamp': data['timestamp'],
                'update': data.get('time_until_update', '')
            }
    except:
        pass
    return {'value': 50, 'classification': 'Neutral', 'timestamp': '', 'update': ''}

@st.cache_data(ttl=600)  # 10분 캐시
def get_btc_dominance():
    """CoinGecko API에서 BTC 도미넌스 조회"""
    try:
        url = "https://api.coingecko.com/api/v3/global"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()['data']
            return {
                'btc_dominance': data['market_cap_percentage']['btc'],
                'eth_dominance': data['market_cap_percentage'].get('eth', 0),
                'total_market_cap': data['total_market_cap']['usd'],
                'total_volume': data['total_volume']['usd'],
                'market_cap_change_24h': data['market_cap_change_percentage_24h_usd'],
                'active_cryptocurrencies': data['active_cryptocurrencies']
            }
    except:
        pass
    return {
        'btc_dominance': 0, 'eth_dominance': 0, 
        'total_market_cap': 0, 'total_volume': 0,
        'market_cap_change_24h': 0, 'active_cryptocurrencies': 0
    }

@st.cache_data(ttl=600)
def get_altcoin_season_index():
    """알트코인 시즌 지수 계산 (Top 50 코인 중 BTC 대비 성과)"""
    try:
        # CoinGecko에서 상위 50개 코인의 90일 성과 조회
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1&sparkline=false&price_change_percentage=90d"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            coins = res.json()
            btc_change = 0
            outperformers = 0
            total_alts = 0
            
            for coin in coins:
                change_90d = coin.get('price_change_percentage_90d_in_currency', 0) or 0
                if coin['id'] == 'bitcoin':
                    btc_change = change_90d
                else:
                    total_alts += 1
                    if change_90d > btc_change:
                        outperformers += 1
            
            # 알트코인 시즌 지수: BTC를 이긴 알트코인 비율 (0-100)
            alt_season_index = (outperformers / total_alts * 100) if total_alts > 0 else 50
            
            return {
                'index': alt_season_index,
                'btc_90d_change': btc_change,
                'outperformers': outperformers,
                'total_alts': total_alts,
                'is_alt_season': alt_season_index >= 75,  # 75% 이상이면 알트시즌
                'is_btc_season': alt_season_index <= 25   # 25% 이하면 BTC 시즌
            }
    except:
        pass
    return {'index': 50, 'btc_90d_change': 0, 'outperformers': 0, 'total_alts': 0, 'is_alt_season': False, 'is_btc_season': False}

# --- 텔레그램 알림 함수 ---
def send_telegram_alert(message):
    """텔레그램으로 알림 메시지 전송"""
    tg = st.session_state.telegram
    if not tg.get('enabled') or not tg.get('bot_token') or not tg.get('chat_id'):
        return False
    try:
        url = f"https://api.telegram.org/bot{tg['bot_token']}/sendMessage"
        payload = {'chat_id': tg['chat_id'], 'text': message, 'parse_mode': 'HTML'}
        res = requests.post(url, data=payload, timeout=5)
        return res.status_code == 200
    except:
        return False

def check_and_send_alerts(portfolio, rate, mvrv):
    """매도 신호 및 목표가 도달 시 알림 전송"""
    alerts = []
    
    # 1. MVRV Z-Score 고평가 경고 (7.0 이상)
    if mvrv >= 7.0:
        alert_key = "mvrv_high"
        if alert_key not in st.session_state.sent_alerts:
            alerts.append(f"🚨 <b>MVRV 고평가 경고!</b>\n\nMVRV Z-Score가 {mvrv:.1f}에 도달했습니다.\n시장 고점 가능성이 높으니 차익실현을 고려하세요.")
            st.session_state.sent_alerts.add(alert_key)
    
    # 2. 목표가 도달 알림
    for p in portfolio:
        ticker = p['ticker']
        target = p.get('target_price', 0)
        exchange = p.get('exchange', 'Binance')
        
        cur_p, curr = get_market_price(ticker, exchange)
        if cur_p <= 0:
            continue
        
        # 목표가 도달 여부
        if target > 0 and cur_p >= target:
            alert_key = f"target_{ticker}_{target}"
            if alert_key not in st.session_state.sent_alerts:
                unit = '₩' if curr == 'KRW' else '$'
                alerts.append(f"🎯 <b>{ticker} 목표가 도달!</b>\n\n현재가: {unit}{cur_p:,.2f}\n목표가: {unit}{target:,.2f}\n\n매도 타이밍이 왔습니다! 📈")
                st.session_state.sent_alerts.add(alert_key)
        
        # [V7.9] 24시간 급등/급락 알림 (±10% 이상)
        change_24h = get_24h_change(ticker, exchange)
        if abs(change_24h) >= 10:
            alert_key = f"change24h_{ticker}_{datetime.now().strftime('%Y%m%d')}"
            if alert_key not in st.session_state.sent_alerts:
                direction = "🚀 급등" if change_24h > 0 else "📉 급락"
                alerts.append(f"{direction} <b>{ticker} 24시간 {change_24h:+.1f}% 변동!</b>\n\n현재가가 급격히 변동했습니다.\n포트폴리오를 확인해보세요.")
                st.session_state.sent_alerts.add(alert_key)
    
    # 알림 전송
    for msg in alerts:
        send_telegram_alert(msg)

@st.cache_data(ttl=300)
def get_dxy_index():
    try:
        if YFINANCE_AVAILABLE:
            hist = yf.Ticker("DX-Y.NYB").history(period="5d")
            if not hist.empty:
                curr = float(hist['Close'].iloc[-1])
                prev = float(hist['Close'].iloc[-2])
                return curr, (curr-prev)/prev*100
    except: pass
    return 104.5, 0.0

@st.cache_data(ttl=60)
def get_stock_price(ticker):
    """주식 가격 조회 (미국/한국)"""
    try:
        if YFINANCE_AVAILABLE:
            df = yf.Ticker(ticker).history(period="1d")
            if not df.empty: return float(df['Close'].iloc[-1])
    except: pass
    return 0.0

@st.cache_data(ttl=10)
def get_market_price(ticker, exchange):
    # [V7.0] 주식 지원
    if exchange == "US Stock": return get_stock_price(ticker), "USD"
    elif exchange == "KR Stock": return get_stock_price(ticker), "KRW"
    
    try:
        if exchange == "Upbit":
            url = f"https://api.upbit.com/v1/ticker?markets=KRW-{ticker}"
            return float(requests.get(url, timeout=2).json()[0]['trade_price']), "KRW"
        elif exchange == "Bithumb":
            url = f"https://api.bithumb.com/public/ticker/{ticker}_KRW"
            res = requests.get(url, timeout=2).json()
            if res['status'] == '0000': return float(res['data']['closing_price']), "KRW"
        elif exchange == "Korbit":
            url = f"https://api.korbit.co.kr/v1/ticker?currency_pair={ticker.lower()}_krw"
            return float(requests.get(url, timeout=2).json()['last']), "KRW"
        elif exchange == "Binance":
            # Binance는 한국에서 지역 제한됨 → CoinGecko API로 대체
            coin_id_map = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "XRP": "ripple", 
                          "ADA": "cardano", "DOGE": "dogecoin", "DOT": "polkadot", "AVAX": "avalanche-2",
                          "LINK": "chainlink", "MATIC": "matic-network", "SHIB": "shiba-inu"}
            coin_id = coin_id_map.get(ticker, ticker.lower())
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
            res = requests.get(url, timeout=5).json()
            if coin_id in res:
                return float(res[coin_id]['usd']), "USD"
            # CoinGecko 실패 시 CCXT OKX로 폴백
            if CCXT_AVAILABLE:
                ex = ccxt.okx({'timeout': 5000})
                return float(ex.fetch_ticker(f"{ticker}/USDT")['last']), "USD"
        elif CCXT_AVAILABLE:
            ex_map = {"OKX": "okx", "Bitget": "bitget", "Gate.io": "gateio"}
            if exchange in ex_map:
                ex = getattr(ccxt, ex_map[exchange])()
                return float(ex.fetch_ticker(f"{ticker}/USDT")['last']), "USD"
    except: pass
    return 0.0, "USD"

# [V7.9] 24시간 변동률 조회 함수
@st.cache_data(ttl=60)
def get_24h_change(ticker, exchange="Upbit"):
    """24시간 가격 변동률 조회"""
    try:
        if exchange == "Upbit":
            url = f"https://api.upbit.com/v1/ticker?markets=KRW-{ticker}"
            res = requests.get(url, timeout=3).json()
            if res:
                return res[0].get('signed_change_rate', 0) * 100  # 퍼센트로 변환
        elif exchange in ["Binance", "OKX"]:
            # CoinGecko에서 24시간 변동률 조회
            coin_id_map = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "XRP": "ripple", 
                          "ADA": "cardano", "DOGE": "dogecoin", "DOT": "polkadot", "AVAX": "avalanche-2"}
            coin_id = coin_id_map.get(ticker, ticker.lower())
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
            res = requests.get(url, timeout=5).json()
            if coin_id in res:
                return res[coin_id].get('usd_24h_change', 0)
    except:
        pass
    return 0.0

# [V7.9] 코인별 김치 프리미엄 조회
@st.cache_data(ttl=30)
def get_kimchi_premium(ticker, rate):
    """특정 코인의 김치 프리미엄 계산"""
    try:
        # 업비트 가격 (KRW)
        upbit_url = f"https://api.upbit.com/v1/ticker?markets=KRW-{ticker}"
        upbit_res = requests.get(upbit_url, timeout=3).json()
        if not upbit_res:
            return None
        krw_price = upbit_res[0]['trade_price']
        
        # 해외 가격 (USD) - CoinGecko 사용
        coin_id_map = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "XRP": "ripple", 
                      "ADA": "cardano", "DOGE": "dogecoin", "DOT": "polkadot", "AVAX": "avalanche-2",
                      "LINK": "chainlink", "MATIC": "matic-network", "SHIB": "shiba-inu"}
        coin_id = coin_id_map.get(ticker)
        if not coin_id:
            return None
            
        cg_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        cg_res = requests.get(cg_url, timeout=5).json()
        if coin_id not in cg_res:
            return None
        usd_price = cg_res[coin_id]['usd']
        
        # 김치 프리미엄 계산
        premium = ((krw_price / (usd_price * rate)) - 1) * 100
        return round(premium, 2)
    except:
        return None

@st.cache_data(ttl=600)  # 10분 캐시
def get_translated_news(keywords, api_key=None):
    """[V7.9] 코인 전문 매체 뉴스 수집 및 번역"""
    
    news_items = []
    
    # ==========================================================================
    # 1. 한국 코인 전문 매체 (번역 불필요)
    # ==========================================================================
    korean_feeds = [
        {"name": "블록미디어", "url": "https://www.blockmedia.co.kr/feed/", "icon": "📰"},
        {"name": "토큰포스트", "url": "https://www.tokenpost.kr/rss", "icon": "🪙"},
    ]
    
    for feed in korean_feeds:
        try:
            f = feedparser.parse(feed['url'])
            for entry in f.entries[:4]:
                title = entry.title.strip()
                if not any(n['title'] == title for n in news_items):
                    pub_date = ""
                    if hasattr(entry, 'published'):
                        pub_date = entry.published[:20]
                    elif hasattr(entry, 'updated'):
                        pub_date = entry.updated[:20]
                    
                    news_items.append({
                        'source': f"{feed['icon']} {feed['name']}", 
                        'title': title, 
                        'link': entry.link,
                        'lang': 'ko', 
                        'date': pub_date,
                    })
        except:
            continue
    
    # ==========================================================================
    # 2. 해외 코인 전문 매체 수집
    # ==========================================================================
    eng_feeds = [
        {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "icon": "🌐"},
        {"name": "CoinTelegraph", "url": "https://cointelegraph.com/rss", "icon": "📡"},
        {"name": "The Block", "url": "https://www.theblock.co/rss.xml", "icon": "🧱"},
    ]
    
    eng_items = []
    for feed in eng_feeds:
        try:
            f = feedparser.parse(feed['url'])
            for entry in f.entries[:3]:
                title = entry.title.strip()
                if not any(n['title'] == title for n in eng_items):
                    pub_date = ""
                    if hasattr(entry, 'published'):
                        pub_date = entry.published[:20]
                    
                    eng_items.append({
                        'source_name': feed['name'],
                        'source': f"{feed['icon']} {feed['name']}", 
                        'original_title': title,
                        'title': title,
                        'link': entry.link,
                        'lang': 'en', 
                        'date': pub_date,
                    })
        except:
            continue
    
    # ==========================================================================
    # 3. Gemini로 영어 뉴스 제목 번역 (REST API 사용)
    # ==========================================================================
    if eng_items and api_key:
        try:
            # 번역할 제목들 (번호 붙여서 매칭 정확도 향상)
            titles_text = ""
            for idx, item in enumerate(eng_items):
                titles_text += f"{idx+1}. {item['original_title']}\n"
            
            prompt = f"""다음 영어 암호화폐 뉴스 제목들을 한국어로 번역해주세요.

규칙:
- 각 번역 앞에 원본과 같은 번호를 붙여주세요 (예: "1. 번역된 제목")
- Bitcoin → 비트코인, Ethereum → 이더리움으로 변환
- ETF, SEC, CEO 등 약어는 그대로 유지
- 뉴스 제목답게 간결하게

원문:
{titles_text}"""
            
            # REST API 직접 호출
            response_text = ask_gemini(api_key, prompt, "You are a professional translator.")
            
            if response_text and not response_text.startswith("❌") and not response_text.startswith("⚠️"):
                # 번역 결과 파싱 (번호로 매칭)
                for line in response_text.strip().split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # "1. 번역된 제목" 형태에서 번호와 제목 분리
                    match = re.match(r'^(\d+)[.\)]\s*(.+)$', line)
                    if match:
                        idx = int(match.group(1)) - 1  # 0-based index
                        translated = match.group(2).strip()
                        
                        if 0 <= idx < len(eng_items) and translated and len(translated) > 3:
                            eng_items[idx]['title'] = translated
                            eng_items[idx]['lang'] = 'ko'
                            eng_items[idx]['source'] = f"🇺🇸→🇰🇷 {eng_items[idx]['source_name']}"
            
        except Exception as e:
            # 번역 실패해도 원문으로 진행
            pass
    
    # 영어 뉴스 추가
    news_items.extend(eng_items)
    
    # 시간순 정렬 (최신 먼저)
    news_items.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    return news_items[:15]

@st.cache_data(ttl=3600)
@st.cache_data(ttl=3600)
def clean_and_translate_desc(text, api_key=None):
    if not text: return "설명 정보가 없습니다."
    
    # 1. HTML 태그 및 엔티티 제거
    import html
    clean_text = re.sub('<[^<]+?>', '', text).strip()
    clean_text = html.unescape(clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip() # 공백 정리
    
    # 한국어 비중 확인
    korean_char_count = len(re.findall('[가-힣]', clean_text))
    is_korean = (korean_char_count / len(clean_text)) > 0.2 if len(clean_text) > 0 else False
    
    if not is_korean and api_key:
        try:
            # [수정] 단순 번역 대신 '요약'을 요청하여 완결된 문장 유도
            prompt = f"""
            Summarize the following cryptocurrency description into 3 to 5 natural Korean sentences.
            Ensure the output is a complete paragraph and ends with a proper punctuation mark.
            
            Description:
            {clean_text[:3000]}
            """
            result = ask_gemini(api_key, prompt, "You are a professional crypto analyst.")
            
            if result and not result.startswith("❌") and not result.startswith("⚠️"):
                return result.strip()
            return clean_text
        except: return clean_text
    return clean_text

@st.cache_data(ttl=3600)
def get_coingecko_details(ticker, api_key=None):
    """API 호출 실패 시 AI로 설명 생성 및 기본값 반환"""
    default_data = {
        'name': ticker, 'rank': '-', 'market_cap': 0, 
        'desc': '상세 정보를 불러올 수 없습니다 (API 제한).',
        'total_supply': 0, 'circulating_supply': 0,
        'ath': 0, 'ath_change': 0, 'atl': 0, 'atl_change': 0
    }
    
    try:
        # 1. 확장된 정적 매핑 (상위 50위 코인) - API 호출 절약
        mapping = {
            'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana', 'XRP': 'ripple', 'DOGE': 'dogecoin', 
            'ADA': 'cardano', 'AVAX': 'avalanche-2', 'DOT': 'polkadot', 'TRX': 'tron', 'LINK': 'chainlink',
            'MATIC': 'matic-network', 'SHIB': 'shiba-inu', 'LTC': 'litecoin', 'BCH': 'bitcoin-cash',
            'UNI': 'uniswap', 'XLM': 'stellar', 'ATOM': 'cosmos', 'ETC': 'ethereum-classic',
            'HBAR': 'hedera-hashgraph', 'FIL': 'filecoin', 'LDO': 'lido-dao', 'APT': 'aptos',
            'ARB': 'arbitrum', 'NEAR': 'near', 'QNT': 'quant', 'VET': 'vechain', 'ICP': 'internet-computer',
            'GRT': 'the-graph', 'ALGO': 'algorand', 'STX': 'blockstack', 'AAVE': 'aave', 'EGLD': 'elrond-erd-2',
            'SAND': 'the-sandbox', 'MANA': 'decentraland', 'THETA': 'theta-token', 'XTZ': 'tezos',
            'AXS': 'axie-infinity', 'EOS': 'eos', 'CAKE': 'pancakeswap', 'FTM': 'fantom', 'KLAY': 'klay-token',
            'NEO': 'neo', 'IOTA': 'iota', 'XMR': 'monero', 'MKR': 'maker', 'RUNE': 'thorchain',
            'SNX': 'havven', 'CRV': 'curve-dao-token', 'FLOW': 'flow' 
        }
        coin_id = mapping.get(ticker.upper())
        
        if not coin_id:
            # 매핑에 없으면 검색 API 호출
            search = requests.get(f"https://api.coingecko.com/api/v3/search?query={ticker}", timeout=3).json()
            if search.get('coins'): 
                coin_id = search['coins'][0]['id']
            else: 
                # 검색 실패 시 AI Fallback 시도 (설명 생성)
                if api_key:
                    desc_ai = ask_gemini(api_key, f"Explain what is {ticker} cryptocurrency in 3 sentences.", "You are a crypto expert. Answer in Korean.")
                    if "❌" not in desc_ai:
                        default_data['desc'] = f"[AI 요약] {desc_ai}"
                        return default_data
                return default_data
        
        # 2. 코인 상세 정보 가져오기
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=ko&tickers=false&market_data=true"
        res = requests.get(url, timeout=5)
        
        # API 제한(429) 또는 오류 시 AI Fallback
        if res.status_code != 200:
            if api_key:
                desc_ai = ask_gemini(api_key, f"{ticker} ({coin_id}) 코인에 대해 3줄로 핵심만 요약해줘.", "암호화폐 전문가입니다. 한국어로 답변하세요.")
                if "❌" not in desc_ai:
                    default_data['desc'] = f"💡 **AI 자동 요약 (API 제한 대안)**\n\n{desc_ai}"
                    return default_data
            return default_data
            
        data = res.json()
        
        if 'market_data' not in data:
            return default_data
            
        m = data['market_data']
        desc_raw = data.get('description', {}).get('ko', '') or data.get('description', {}).get('en', '')
        
        return {
            'name': data.get('name', ticker), 
            'rank': m.get('market_cap_rank', '-'),
            'market_cap': m.get('market_cap', {}).get('usd', 0) or 0,
            'total_supply': m.get('total_supply', 0) or 0, 
            'circulating_supply': m.get('circulating_supply', 0) or 0,
            'ath': m.get('ath', {}).get('usd', 0) or 0, 
            'ath_change': m.get('ath_change_percentage', {}).get('usd', 0) or 0,
            'atl': m.get('atl', {}).get('usd', 0) or 0, 
            'atl_change': m.get('atl_change_percentage', {}).get('usd', 0) or 0,
            'desc': desc_raw or '설명 정보가 없습니다.'
        }
    except Exception:
        # 예외 발생 시에도 AI 시도
        if api_key:
            try:
                desc_ai = ask_gemini(api_key, f"{ticker} 코인에 대해 3줄로 핵심만 요약해줘.", "암호화폐 전문가입니다. 한국어로 답변하세요.")
                if "❌" not in desc_ai:
                    default_data['desc'] = f"💡 **AI 자동 요약 (오류 대안)**\n\n{desc_ai}"
                    return default_data
            except: pass
        return default_data

# --- 차트 및 분석 함수 ---
@st.cache_data(ttl=3600)
def get_weekly_ohlcv(symbol="BTC", weeks=60):
    """주봉 데이터 (yfinance 우선 - 한국 지역 제한 회피)"""
    # 1차 시도: yfinance (안정적, 지역 제한 없음)
    try:
        if YFINANCE_AVAILABLE:
            ticker = f"{symbol}-USD" if symbol in ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'DOGE', 'AVAX', 'LINK', 'SHIB'] else symbol
            df_yf = yf.download(ticker, period=f"{weeks}w", interval="1wk", progress=False)
            if not df_yf.empty:
                # 멀티인덱스 컬럼 처리
                if isinstance(df_yf.columns, pd.MultiIndex):
                    df = pd.DataFrame({
                        'o': df_yf['Open'].iloc[:, 0] if len(df_yf['Open'].shape) > 1 else df_yf['Open'],
                        'h': df_yf['High'].iloc[:, 0] if len(df_yf['High'].shape) > 1 else df_yf['High'],
                        'l': df_yf['Low'].iloc[:, 0] if len(df_yf['Low'].shape) > 1 else df_yf['Low'],
                        'c': df_yf['Close'].iloc[:, 0] if len(df_yf['Close'].shape) > 1 else df_yf['Close'],
                        'v': df_yf['Volume'].iloc[:, 0] if len(df_yf['Volume'].shape) > 1 else df_yf['Volume']
                    })
                else:
                    df = pd.DataFrame({
                        'o': df_yf['Open'], 'h': df_yf['High'], 
                        'l': df_yf['Low'], 'c': df_yf['Close'], 'v': df_yf['Volume']
                    })
                return df
    except: pass
    
    # 2차 시도: CCXT (OKX - 한국 접근 가능)
    try:
        if CCXT_AVAILABLE:
            pair = f"{symbol}/USDT" if '/' not in symbol else symbol
            ex = ccxt.okx({'timeout': 10000})
            df = pd.DataFrame(ex.fetch_ohlcv(pair, '1w', limit=weeks), columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            df['ts'] = pd.to_datetime(df['ts'], unit='ms')
            return df.set_index('ts')
    except: pass
    
    return None

@st.cache_data(ttl=3600)
def get_daily_ohlcv(symbol="BTC", days=1000):
    """일봉 데이터 (yfinance 우선 - 한국 지역 제한 회피) - Pi Cycle 계산용"""
    # 1차 시도: yfinance (안정적, 지역 제한 없음)
    try:
        if YFINANCE_AVAILABLE:
            ticker = f"{symbol}-USD" if symbol in ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'DOGE'] else symbol
            df_yf = yf.download(ticker, period=f"{min(days, 3650)}d", interval="1d", progress=False)
            if not df_yf.empty:
                # 멀티인덱스 컬럼 처리
                if isinstance(df_yf.columns, pd.MultiIndex):
                    df = pd.DataFrame({
                        'o': df_yf['Open'].iloc[:, 0] if len(df_yf['Open'].shape) > 1 else df_yf['Open'],
                        'h': df_yf['High'].iloc[:, 0] if len(df_yf['High'].shape) > 1 else df_yf['High'],
                        'l': df_yf['Low'].iloc[:, 0] if len(df_yf['Low'].shape) > 1 else df_yf['Low'],
                        'c': df_yf['Close'].iloc[:, 0] if len(df_yf['Close'].shape) > 1 else df_yf['Close'],
                        'v': df_yf['Volume'].iloc[:, 0] if len(df_yf['Volume'].shape) > 1 else df_yf['Volume']
                    })
                else:
                    df = pd.DataFrame({
                        'o': df_yf['Open'], 'h': df_yf['High'], 
                        'l': df_yf['Low'], 'c': df_yf['Close'], 'v': df_yf['Volume']
                    })
                return df
    except: pass
    
    # 2차 시도: CCXT (OKX - 한국 접근 가능)
    try:
        if CCXT_AVAILABLE:
            ex = ccxt.okx({'timeout': 10000})
            df = pd.DataFrame(ex.fetch_ohlcv(f'{symbol}/USDT', '1d', limit=min(days, 1000)), columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            df['ts'] = pd.to_datetime(df['ts'], unit='ms')
            return df.set_index('ts')
    except: pass
    
    return None

def analyze_technical(df):
    if df is None or len(df) < 30: return {"signal": "N/A", "score": 0, "summary": []}
    close = df['c']
    sma20 = SMAIndicator(close, 20).sma_indicator().iloc[-1]
    rsi = RSIIndicator(close, 14).rsi().iloc[-1]
    summary = []
    score = 50
    if close.iloc[-1] > sma20: score += 20; summary.append("📈 주가 > 20주선 (상승 추세)")
    else: score -= 20; summary.append("📉 주가 < 20주선 (하락 추세)")
    if rsi < 30: score += 30; summary.append(f"💎 과매도 (RSI {rsi:.0f})")
    elif rsi > 70: score -= 20; summary.append(f"🔥 과매수 (RSI {rsi:.0f})")
    sig = "매수" if score >= 60 else "매도" if score <= 40 else "중립"
    return {"signal": sig, "score": score, "summary": summary}

@st.cache_data(ttl=3600)
def get_historical_data(ticker, days=365):
    try:
        if YFINANCE_AVAILABLE: return yf.download(ticker, period=f"{days}d", interval="1d", progress=False)
    except: pass
    return None

@st.cache_data(ttl=3600)
def get_btc_dominance():
    try: return requests.get("https://api.coingecko.com/api/v3/global", timeout=5).json()['data']['market_cap_percentage']['btc']
    except: return 58.0

@st.cache_data(ttl=1800)
def get_fear_greed():
    try: return int(requests.get("https://api.alternative.me/fng/?limit=1", timeout=5).json()['data'][0]['value'])
    except: return 50

# --- [V6.8] 스마트 목표가 계산 함수 ---
def calculate_smart_targets(price, ath):
    if price <= 0: return {}
    
    # 1. Round Number (심리적 저항)
    magnitude = 10 ** (len(str(int(price))) - 1)
    # 현재가보다 높은 다음 라운드 숫자 (예: 92 -> 100, 1200 -> 2000)
    round_fig = math.ceil(price / magnitude) * magnitude
    if round_fig == price: round_fig += magnitude
    if round_fig < price * 1.05: # 너무 가까우면 한 단계 더 위로
        round_fig += magnitude

    targets = {
        "ATH (전고점)": ath,
        "Fib 1.618 (불장)": ath * 1.618 if ath > 0 else 0,
        "수익 2배 (원금회수)": price * 2,
        "라운드 피겨 (심리)": round_fig
    }
    return targets

# --- [V7.0] 헤지 데이터 분석 함수 ---
@st.cache_data(ttl=3600)
def get_hedge_data(crypto_ticker="BTC-USD", user_stocks=[]):
    """비트코인과 [추천 헤지 자산 + 내 주식]의 상관관계 분석"""
    tickers = {
        "BTC": crypto_ticker,
        "TLT (미국채)": "TLT",
        "GLD (금)": "GLD",
        "SCHD (배당주)": "SCHD",
        "VOO (S&P500)": "VOO"
    }
    # 사용자 보유 주식 추가
    for s in user_stocks:
        if s not in tickers.values():
            tickers[f"{s} (My)"] = s
    try:
        if YFINANCE_AVAILABLE:
            df = yf.download(list(tickers.values()), period="6mo", progress=False)['Close']
            inv_map = {v: k for k, v in tickers.items()}
            df.columns = [inv_map.get(c, c) for c in df.columns]
            normalized = (df / df.iloc[0] - 1) * 100
            if 'BTC' in df.columns:
                corr = df.corr()['BTC'].drop('BTC')
                return normalized, corr
    except: pass
    return None, None

# -----------------------------------------------------------------------------
# [추가] 개별 키 저장을 위한 DB 업데이트 헬퍼 함수
# -----------------------------------------------------------------------------
def update_single_key_db(username, key_type, value, is_telegram=False):
    """
    Firebase와 세션 상태를 동시에 업데이트하는 함수
    key_type: 'gemini', 'openai' 등 (DB 필드명)
    value: 저장할 값
    is_telegram: 텔레그램 ID인지 여부 (DB 구조가 다를 수 있음)
    """
    if not username:
        st.error("로그인이 필요합니다.")
        return False

    db = init_firebase()
    if not db:
        st.error("DB 연결 실패")
        return False

    # 🔧 공백 제거 (복사 시 포함된 앞뒤 공백 제거)
    value = value.strip() if value else ""

    try:
        doc_ref = db.collection("users").document(username)
        
        if is_telegram:
            # 텔레그램 ID는 루트 레벨 혹은 별도 필드로 저장
            doc_ref.set({
                "telegram_id": value,
                "last_updated": firestore.SERVER_TIMESTAMP
            }, merge=True)
            # 세션 업데이트
            st.session_state.telegram_id = value
            # 텔레그램 딕셔너리도 동기화
            if 'telegram' in st.session_state:
                st.session_state.telegram['chat_id'] = value
        else:
            # API 키들은 api_keys 맵 안에 저장
            doc_ref.set({
                "api_keys": {key_type: value},
                "last_updated": firestore.SERVER_TIMESTAMP
            }, merge=True)
            # 세션 업데이트 (변수명 규칙: {key_type}_key)
            st.session_state[f"{key_type}_key"] = value

        return True
    except Exception as e:
        st.error(f"저장 중 오류 발생: {e}")
        return False

# -----------------------------------------------------------------------------
# [수정] 사이드바: 로그인 + 개별 API 키 관리 기능
# -----------------------------------------------------------------------------
def render_sidebar():
    st.sidebar.title("🐋 크립토 인사이트 V8.2")
    
    # [V7.9] 이미 로그인된 경우 로그인 폼 스킵 (main에서 처리)
    if not st.session_state.get('is_logged_in', False):
        st.sidebar.info("👈 메인 화면에서 로그인해주세요.")
        st.stop()

    # 2. 로그인 후 화면
    st.sidebar.success(f"환영합니다, **{st.session_state.username}**님!")
    
    if st.sidebar.button("로그아웃", type="secondary"):
        st.session_state.clear()
        st.rerun()

    st.sidebar.divider()

    # 3. 🔑 API 키 및 설정 (개별 저장/삭제 기능 적용)
    with st.sidebar.expander("🔑 API 키 및 설정", expanded=True):
        st.caption("각 키를 입력 후 **저장** 버튼을 누르세요.")
        
        # 내부 UI 렌더링용 함수 (반복 코드 제거)
        def render_key_input(label, session_key, db_key, is_password=True, is_telegram=False):
            val = st.text_input(label, value=st.session_state.get(session_key, ""), type="password" if is_password else "default", key=f"input_{session_key}")
            
            # 버튼 영역 (2개 컬럼)
            b1, b2 = st.columns(2)
            with b1:
                if st.button("저장", key=f"save_{session_key}", use_container_width=True):
                    if update_single_key_db(st.session_state.username, db_key, val, is_telegram):
                        st.toast(f"✅ {label} 저장 완료!", icon="💾")
                        time.sleep(0.5)
                        st.rerun()
            with b2:
                if st.button("삭제", key=f"del_{session_key}", type="primary", use_container_width=True):
                    if update_single_key_db(st.session_state.username, db_key, "", is_telegram):
                        st.toast(f"🗑️ {label} 삭제 완료!", icon="🗑️")
                        time.sleep(0.5)
                        st.rerun()
            st.markdown("---") # 구분선

        # 1. Gemini
        render_key_input("Gemini API Key", "gemini_key", "gemini")
        
        # 2. OpenAI
        render_key_input("OpenAI API Key", "openai_key", "openai")
        
        # 3. Claude (유료 API 필요)
        render_key_input("Claude API Key", "claude_key", "claude")
        
        # 4. Grok (xAI 유료 API 필요)
        render_key_input("Grok API Key", "grok_key", "grok")
        
        # 5. [V8.0] Groq (무료! 오픈소스 모델 - Meta Llama)
        st.caption("🆓 **무료 대안**: Groq으로 Llama 모델 사용")
        render_key_input("Groq API Key", "groq_key", "groq")
        st.markdown("[👉 Groq 무료 API 키 발급](https://console.groq.com/keys)", unsafe_allow_html=True)
        
        # 텔레그램은 별도 섹션으로 이동됨
        st.caption("📢 텔레그램 알림은 아래 별도 섹션에서 설정")

    # 4. 나머지 사이드바 기능 (기존 유지)
    st.sidebar.divider()
    rate = get_usd_krw_rate()
    st.sidebar.markdown(f"**💵 환율:** `{rate:,.0f} 원/$`")
    
    auto_refresh = st.sidebar.checkbox("⚡ 실시간 갱신 (10초)", value=False)
    
    st.sidebar.divider()
    
    # 5. 자산 추가/수정 섹션
    with st.sidebar.expander("💰 자산 추가/수정", expanded=False):
        exchanges = ["Binance", "Upbit", "Bithumb", "Korbit", "US Stock", "KR Stock", "OKX", "Bitget", "Gate.io"]
        exchange = st.selectbox("거래소/종목구분", exchanges)
        is_krw = exchange in ["Upbit", "Bithumb", "Korbit", "KR Stock"]
        
        if exchange == "US Stock": ticker_hint = "예: AAPL, TSLA, TLT"
        elif exchange == "KR Stock": ticker_hint = "예: 005930.KS (삼성전자)"
        else: ticker_hint = "예: BTC, ETH, SOL"
        
        c1, c2 = st.columns(2)
        ticker = c1.text_input("종목 코드", placeholder=ticker_hint).upper()
        qty = c2.number_input("수량", 0.0, step=0.01)
        
        step_val = 10000.0 if is_krw else 100.0
        unit = "₩" if is_krw else "$"
        avg = st.number_input(f"평단가 ({unit})", 0.0, step=step_val)
        
        # 스마트 목표가 가이드
        if ticker and avg > 0 and "Stock" not in exchange:
            info = get_coingecko_details(ticker, st.session_state.get('gemini_key'))
            if info:
                ath_val = info['ath'] * (rate if is_krw else 1)
                targets = calculate_smart_targets(avg, ath_val)
                st.markdown(f"""
                <div class='target-guide-box'>
                    <div class='guide-title'>🎯 목표가 추천 가이드</div>
                    <div class='guide-row'><span class='guide-label'>📉 전고점 (ATH)</span> <span class='guide-val'>{targets['ATH (전고점)']:,.0f}</span></div>
                    <div class='guide-row'><span class='guide-label'>🔢 심리적 저항선</span> <span class='guide-val'>{targets['라운드 피겨 (심리)']:,.0f}</span></div>
                    <div class='guide-row'><span class='guide-label'>💰 수익 2배 (회수)</span> <span class='guide-val'>{targets['수익 2배 (원금회수)']:,.0f}</span></div>
                </div>
                """, unsafe_allow_html=True)

        tgt = st.number_input("목표가", 0.0, step=step_val)
        
        if st.button("➕ 저장", use_container_width=True):
            if ticker and qty > 0:
                found = False
                for p in st.session_state.portfolio:
                    if p['ticker'] == ticker and p.get('exchange') == exchange:
                        p['quantity'] = qty; p['avg_price'] = avg; p['target_price'] = tgt
                        found = True; break
                if not found:
                    st.session_state.portfolio.append({'ticker': ticker, 'quantity': qty, 'avg_price': avg, 'target_price': tgt, 'exchange': exchange})
                save_user_data(st.session_state.username)
                st.rerun()

    # 포트폴리오 목록
    if st.session_state.portfolio:
        st.sidebar.markdown("##### 📋 내 자산")
        for i, p in enumerate(st.session_state.portfolio):
            c1, c2 = st.sidebar.columns([4, 1])
            ex = p.get('exchange', 'Binance')
            icon = "🏢" if "Stock" in ex else "🪙"
            c1.caption(f"{icon} [{ex[:6]}] {p['ticker']} ({p['quantity']})")
            if c2.button("🗑️", key=f"del_pf_{i}"):
                st.session_state.portfolio.pop(i)
                save_user_data(st.session_state.username)
                st.rerun()
                
    st.sidebar.divider()
    
    # 텔레그램 봇 설정 (통합 UI)
    with st.sidebar.expander("📢 텔레그램 알림 설정", expanded=False):
        st.markdown("##### 🤖 텔레그램 봇 연동")
        st.caption("목표가 도달, 급등/급락 시 알림을 받습니다.")
        
        # 현재 설정 상태 표시
        current_token = st.session_state.telegram.get('bot_token', '')
        current_chat_id = st.session_state.get('telegram_id', '')
        
        # Bot Token 입력
        tg_token = st.text_input(
            "Bot Token", 
            value=current_token, 
            type="password",
            placeholder="1234567890:ABCdefGHI...",
            help="@BotFather에서 생성한 봇 토큰"
        )
        
        # Chat ID 입력
        tg_chat_id = st.text_input(
            "Chat ID", 
            value=current_chat_id,
            placeholder="123456789",
            help="@userinfobot에서 확인한 내 Chat ID"
        )
        
        # 알림 활성화
        tg_enabled = st.checkbox(
            "🔔 알림 활성화", 
            value=st.session_state.telegram.get('enabled', False)
        )
        
        # 저장 및 테스트 버튼 (간격 조정)
        col_save, col_test = st.columns([1, 1])
        
        with col_save:
            if st.button("저장", key="tg_save_btn", use_container_width=True):
                st.session_state.telegram['bot_token'] = tg_token
                st.session_state.telegram['chat_id'] = tg_chat_id
                st.session_state.telegram['enabled'] = tg_enabled
                st.session_state.telegram_id = tg_chat_id
                save_user_data(st.session_state.username)
                st.success("✅ 저장 완료!")
                time.sleep(0.5)
                st.rerun()
        
        with col_test:
            # 테스트 버튼
            test_disabled = not (tg_token and tg_chat_id)
            if st.button("테스트", key="tg_test_btn", use_container_width=True, disabled=test_disabled):
                st.session_state.telegram['bot_token'] = tg_token
                st.session_state.telegram['chat_id'] = tg_chat_id
                st.session_state.telegram['enabled'] = True
                
                test_msg = f"""✅ 크립토 인사이트 알림 테스트 성공!

🕐 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
👤 사용자: {st.session_state.username}

이 메시지가 보이면 알림이 정상 작동합니다! 🎉"""
                
                if send_telegram_alert(test_msg):
                    st.success("✅ 전송 성공!")
                else:
                    st.error("❌ 전송 실패")
                    st.caption("Bot Token과 Chat ID를 확인해주세요.")
        
        # 설정 상태 표시
        st.divider()
        if tg_token and tg_chat_id and tg_enabled:
            st.success("✅ 알림 준비 완료")
        elif tg_token and tg_chat_id:
            st.info("ℹ️ '알림 활성화'를 체크해주세요")
        else:
            st.warning("⚠️ Bot Token과 Chat ID를 입력해주세요")
        
        # 도움말
        with st.expander("❓ 설정 방법"):
            st.markdown("""
            **1. Bot Token 발급**
            1. 텔레그램에서 `@BotFather` 검색
            2. `/newbot` 명령어로 봇 생성
            3. 받은 토큰을 복사
            
            **2. Chat ID 확인**
            1. 텔레그램에서 `@userinfobot` 검색
            2. `/start` 입력
            3. 표시된 ID 복사
            
            **3. 봇과 대화 시작**
            - 만든 봇을 검색해서 `/start` 입력
            - 이 단계를 해야 메시지 수신 가능!
            """)
    
    # 반환값 (Gemini, OpenAI, Claude, Grok, Groq 키, 자동갱신여부)
    return (
        st.session_state.gemini_key, 
        st.session_state.openai_key, 
        st.session_state.claude_key, 
        st.session_state.grok_key, 
        st.session_state.groq_key,  # [V8.0] Groq 오픈소스
        auto_refresh
    )

# -----------------------------------------------------------------------------
# 탭 1: 대시보드
# -----------------------------------------------------------------------------
def render_dashboard_tab(gemini_key):
    st.markdown("### 📊 내 자산 & 시장 현황")
    
    # -------------------------------------------------------------------------
    # [V8.3] Sell Score Engine & Action Card
    # -------------------------------------------------------------------------
    # 1. 데이터 수집
    mkt_v83 = get_market_data_v83()
    mvrv, is_auto = get_current_mvrv()
    btc_df_wk = get_btc_ohlcv_weekly()
    
    rsi = 50
    if btc_df_wk is not None and TA_AVAILABLE:
        try:
            rsi = RSIIndicator(btc_df_wk['Close'], 14).rsi().iloc[-1]
        except: pass
        
    # 2. Sell Score 계산
    score, reasons = calc_total_sell_score(mvrv, rsi, mkt_v83['fng'], mkt_v83['dom'], mkt_v83['dxy_chg'] > 0)
    action_title, action_desc, color = get_action_plan(score)
    
    # --- [UI Section 1] 행동 지침 카드 ---
    st.markdown(f"""
    <div class='action-card' style='background: linear-gradient(135deg, {color} 0%, {color}dd 100%);'>
        <div class='action-title'>🚀 현재 AI & 알고리즘 권장 행동</div>
        <div class='action-main'>{action_title}</div>
        <div class='action-sub'>{action_desc}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # --- [UI Section 2] 핵심 지표 그리드 ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sell Score", f"{score}점", "종합 위험도", delta_color="inverse")
    c2.metric("MVRV Z-Score", f"{mvrv:.2f}", "고점 지표")
    c3.metric("공포/탐욕", f"{mkt_v83['fng']}", "Greed" if mkt_v83['fng']>50 else "Fear")
    c4.metric("주봉 RSI", f"{rsi:.1f}", "과열" if rsi>70 else "정상")
    
    # 수동 보정 슬라이더
    if not is_auto:
        with st.expander("🔧 MVRV 값 수동 보정하기"):
            new_mvrv = st.slider("MVRV Z-Score 조절", 0.0, 10.0, float(mvrv), 0.1)
            if new_mvrv != mvrv:
                st.session_state.manual_data['mvrv_zscore'] = new_mvrv
                st.rerun()
                
    # 위험 요인 표시
    if reasons:
        st.warning(f"🚨 **감지된 위험 신호:** {', '.join(reasons)}")
    
    # --- [UI Section 3] 자동 분할 매도 캘린더 ---
    st.divider()
    
    # 포트폴리오에서 BTC 수량 찾기 (없으면 1.0개로 시뮬레이션)
    btc_qty = 0
    btc_ticker = "BTC"
    
    # 세션 포트폴리오 확인
    portfolio = st.session_state.portfolio
    if portfolio:
        for p in portfolio:
            if "BTC" in p['ticker']:
                btc_qty = p['quantity']
                break
            
    # BTC가 없으면 시뮬레이션 모드 안내
    simulated = False
    if btc_qty == 0:
        btc_qty = 1.0
        simulated = True
        
    # 캘린더 생성 (50점 이상일 때만)
    cal_df = generate_sell_calendar(score, btc_qty)
    
    if cal_df is not None:
        st.subheader(f"📅 AI 추천 분할 매도 캘린더 ({'내 보유량 기준' if not simulated else '1 BTC 기준 시뮬레이션'})")
        
        if simulated:
            st.info("💡 사이드바에서 자산을 등록하면 내 보유량에 맞춘 캘린더가 생성됩니다.")
            
        col_cal1, col_cal2 = st.columns([1, 1])
        
        with col_cal1:
            # 테이블 표시
            st.dataframe(
                cal_df.style.format({"매도 수량": "{:,.4f}", "매도 후 잔액": "{:,.4f}"}),
                use_container_width=True,
                hide_index=True
            )
            
        with col_cal2:
            # 차트 표시
            fig = px.bar(
                cal_df, 
                x='날짜', 
                y='매도 수량', 
                title="일자별 매도 실행 계획",
                text='매도 비율',
                color_discrete_sequence=[color]
            )
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True, key="calendar_chart_v83")
        
        st.divider()
            
    elif score < 50:
        st.info("✅ 현재는 매도 구간이 아닙니다. 캘린더가 생성되지 않습니다.")
        st.divider()
    
    # =========================================================================
    # [V8.1] 시장 심리 지표 (공포탐욕지수, BTC 도미넌스, 알트시즌)
    # =========================================================================
    with st.expander("🌡️ 시장 심리 지표 (클릭하여 펼치기)", expanded=True):
        try:
            fng = get_fear_greed_index()
            global_data = get_btc_dominance()
            alt_season = get_altcoin_season_index()
            
            # API 응답이 딕셔너리인지 확인 (안전 처리)
            if not isinstance(fng, dict):
                fng = {'value': 50, 'classification': 'Neutral'}
            if not isinstance(global_data, dict):
                global_data = {'btc_dominance': 0, 'eth_dominance': 0, 'total_market_cap': 0, 'market_cap_change_24h': 0}
            if not isinstance(alt_season, dict):
                alt_season = {'index': 50, 'is_alt_season': False, 'is_btc_season': False}
            
            col1, col2, col3, col4 = st.columns(4)
            
            # 1. 공포탐욕지수
            with col1:
                fng_value = fng.get('value', 50)
                if fng_value <= 25:
                    fng_color = "#dc2626"  # 극도의 공포 - 빨강
                    fng_emoji = "😱"
                    fng_label = "극도의 공포"
                elif fng_value <= 45:
                    fng_color = "#f97316"  # 공포 - 주황
                    fng_emoji = "😨"
                    fng_label = "공포"
                elif fng_value <= 55:
                    fng_color = "#eab308"  # 중립 - 노랑
                    fng_emoji = "😐"
                    fng_label = "중립"
                elif fng_value <= 75:
                    fng_color = "#84cc16"  # 탐욕 - 연두
                    fng_emoji = "😊"
                    fng_label = "탐욕"
                else:
                    fng_color = "#22c55e"  # 극도의 탐욕 - 초록
                    fng_emoji = "🤑"
                    fng_label = "극도의 탐욕"
                
                st.markdown(f"""
                <div style="text-align:center; padding:10px; background:linear-gradient(135deg, {fng_color}22, {fng_color}11); border-radius:10px; border:1px solid {fng_color}44;">
                    <div style="font-size:0.8em; color:#64748b;">공포탐욕지수</div>
                    <div style="font-size:2em; font-weight:bold; color:{fng_color};">{fng_emoji} {fng_value}</div>
                    <div style="font-size:0.9em; color:{fng_color}; font-weight:600;">{fng_label}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # 2. BTC 도미넌스
            with col2:
                btc_dom = global_data.get('btc_dominance', 0)
                eth_dom = global_data.get('eth_dominance', 0)
                dom_color = "#f7931a" if btc_dom >= 50 else "#627eea"
                dom_trend = "📈" if btc_dom >= 55 else ("📉" if btc_dom <= 45 else "➡️")
                
                if btc_dom > 0:
                    st.markdown(f"""
                    <div style="text-align:center; padding:10px; background:linear-gradient(135deg, {dom_color}22, {dom_color}11); border-radius:10px; border:1px solid {dom_color}44;">
                        <div style="font-size:0.8em; color:#64748b;">BTC 도미넌스</div>
                        <div style="font-size:2em; font-weight:bold; color:{dom_color};">{dom_trend} {btc_dom:.1f}%</div>
                        <div style="font-size:0.9em; color:#64748b;">ETH: {eth_dom:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="text-align:center; padding:10px; background:#f3f4f6; border-radius:10px; border:1px solid #e5e7eb;">
                        <div style="font-size:0.8em; color:#64748b;">BTC 도미넌스</div>
                        <div style="font-size:1.5em; color:#9ca3af;">⏳ 로딩중</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # 3. 알트코인 시즌 지수
            with col3:
                alt_idx = alt_season.get('index', 50)
                is_alt = alt_season.get('is_alt_season', False)
                is_btc = alt_season.get('is_btc_season', False)
                
                if is_alt:
                    alt_color = "#8b5cf6"
                    alt_label = "🚀 알트시즌!"
                elif is_btc:
                    alt_color = "#f7931a"
                    alt_label = "₿ BTC 시즌"
                else:
                    alt_color = "#6b7280"
                    alt_label = "⚖️ 균형"
                
                st.markdown(f"""
                <div style="text-align:center; padding:10px; background:linear-gradient(135deg, {alt_color}22, {alt_color}11); border-radius:10px; border:1px solid {alt_color}44;">
                    <div style="font-size:0.8em; color:#64748b;">알트시즌 지수</div>
                    <div style="font-size:2em; font-weight:bold; color:{alt_color};">{alt_idx:.0f}</div>
                    <div style="font-size:0.9em; color:{alt_color}; font-weight:600;">{alt_label}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # 4. 전체 시장
            with col4:
                total_mcap = global_data.get('total_market_cap', 0)
                mcap_change = global_data.get('market_cap_change_24h', 0)
                mcap_color = "#22c55e" if mcap_change >= 0 else "#dc2626"
                mcap_trillion = total_mcap / 1e12 if total_mcap > 0 else 0
                
                if total_mcap > 0:
                    st.markdown(f"""
                    <div style="text-align:center; padding:10px; background:linear-gradient(135deg, #3b82f622, #3b82f611); border-radius:10px; border:1px solid #3b82f644;">
                        <div style="font-size:0.8em; color:#64748b;">총 시가총액</div>
                        <div style="font-size:1.8em; font-weight:bold; color:#3b82f6;">${mcap_trillion:.2f}T</div>
                        <div style="font-size:0.9em; color:{mcap_color}; font-weight:600;">{mcap_change:+.1f}% (24h)</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="text-align:center; padding:10px; background:#f3f4f6; border-radius:10px; border:1px solid #e5e7eb;">
                        <div style="font-size:0.8em; color:#64748b;">총 시가총액</div>
                        <div style="font-size:1.5em; color:#9ca3af;">⏳ 로딩중</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # 해석 가이드 (데이터가 있을 때만)
            if fng_value > 0 and btc_dom > 0:
                st.caption(f"💡 **해석**: 공포탐욕 {fng_value} {'(매수 기회 탐색)' if fng_value <= 30 else '(과열 주의)' if fng_value >= 70 else ''} | BTC 도미넌스 {btc_dom:.1f}% {'(자금 BTC 집중)' if btc_dom >= 55 else '(알트코인 강세)' if btc_dom <= 45 else ''} | 알트시즌 {alt_idx:.0f}/100 {'🎯' if is_alt else ''}")
        
        except Exception as e:
            st.warning(f"⚠️ 시장 심리 지표를 불러오는 중 오류가 발생했습니다. (대시보드는 정상 작동)")
            st.caption(f"오류: {str(e)[:100]}")
    
    # --- [여기서부터 새로 추가된 그래프 코드] ---
    if st.session_state.get('username'):
        try:
            db = init_firebase()
            if db:
                # 히스토리 데이터 가져오기 (날짜순 정렬)
                history_ref = db.collection("users").document(st.session_state.username).collection("history")
                docs = history_ref.order_by("date").stream()
                
                history_data = []
                for doc in docs:
                    data = doc.to_dict()
                    if data.get('date') and data.get('total_krw'):
                        history_data.append({"Date": data['date'], "Total Asset (KRW)": data['total_krw']})
                
                if len(history_data) > 1:  # 데이터가 2개 이상일 때만 그래프 그림
                    df_history = pd.DataFrame(history_data)
                    
                    # Plotly로 아름다운 라인 차트 그리기
                    fig_hist = px.line(df_history, x='Date', y='Total Asset (KRW)', 
                                       title="📈 내 자산 성장 추이", markers=True)
                    fig_hist.update_traces(line_color='#00CC96', line_width=3)
                    fig_hist.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig_hist, use_container_width=True, key="asset_history_chart")
                    st.divider()
                elif len(history_data) == 1:
                    st.caption(f"📅 자산 기록 시작일: {history_data[0]['Date']} (내일부터 그래프가 그려집니다)")
                    
        except Exception:
            # 에러 나도 대시보드는 보여줘야 하므로 pass
            pass
    # --- [그래프 코드 끝] ---
    
    rate = get_usd_krw_rate()
    portfolio = st.session_state.portfolio
    
    if not portfolio: 
        st.info("👈 사이드바에서 자산을 추가해주세요.")
        return

    total_krw = 0
    total_cost = 0
    treemap_data = []  # [V7.9] 트리맵용 데이터 (수익률 포함)
    table_data = []
    csv_data = []  # [V7.9] CSV 내보내기용
    
    for p in portfolio:
        cur_p, curr = get_market_price(p['ticker'], p.get('exchange', 'Binance'))
        k_rate = rate if curr == "USD" else 1
        val = p['quantity'] * cur_p * k_rate
        cost = p['quantity'] * p['avg_price'] * k_rate
        total_krw += val
        total_cost += cost
        profit_rate = (val-cost)/cost*100 if cost > 0 else 0
        
        # [V7.9] 트리맵용 데이터 (수익률에 따른 색상)
        treemap_data.append({
            'Coin': p['ticker'], 
            'Value': val, 
            'ProfitRate': profit_rate,
            'Display': f"{p['ticker']}\n₩{val/1000000:.1f}M\n{profit_rate:+.1f}%"
        })
        
        hit = (p['target_price'] > 0) and (cur_p >= p['target_price'])
        
        # [V7.9] 24시간 변동률 조회
        change_24h = get_24h_change(p['ticker'], p.get('exchange', 'Binance'))
        change_class = "change-positive" if change_24h > 0 else "change-negative" if change_24h < 0 else "change-neutral"
        
        table_data.append({
            "코인": p['ticker'], 
            "거래소": p.get('exchange'), 
            "수량": p['quantity'], 
            "평가금액": f"₩{val:,.0f}", 
            "24H": f"{change_24h:+.2f}%",
            "수익률": profit_rate, 
            "_hit": hit
        })
        
        # CSV용 데이터
        csv_data.append({
            "코인": p['ticker'],
            "거래소": p.get('exchange'),
            "수량": p['quantity'],
            "평단가": p['avg_price'],
            "현재가": cur_p,
            "평가금액(KRW)": val,
            "수익률(%)": profit_rate,
            "24시간변동률(%)": change_24h
        })

    k1, k2, k3 = st.columns(3)
    k1.metric("총 자산 (KRW)", f"₩{total_krw:,.0f}")
    pnl = total_krw - total_cost
    k2.metric("총 수익률", f"{pnl/total_cost*100:+.2f}%", f"₩{pnl:+,.0f}" if total_cost > 0 else "0")
    
    btc_k = get_market_price("BTC", "Upbit")[0]
    btc_u = get_market_price("BTC", "Binance")[0]
    kimchi = ((btc_k / (btc_u * rate)) - 1) * 100 if btc_u > 0 else 0
    with k3:
        badge_class = "k-red" if kimchi > 3 else "k-blue" if kimchi > 0 else "k-green"
        st.markdown(f"**🌶️ 김치 프리미엄**: <span class='kimchi-badge {badge_class}'>{kimchi:+.2f}%</span>", unsafe_allow_html=True)

    # [수정 3-3] 계산된 총 자산을 DB에 기록 (자동 저장)
    if st.session_state.get('username') and total_krw > 0:
        update_asset_history(st.session_state.username, total_krw)

    st.divider()
    c1, c2 = st.columns([1, 2])
    with c1:
        # [V7.9] 트리맵 시각화 (수익률에 따른 색상)
        if treemap_data:
            df_treemap = pd.DataFrame(treemap_data)
            
            # 자산 개수에 따라 시각화 방식 선택
            if len(treemap_data) >= 3:
                # 트리맵: 자산이 3개 이상일 때 직관적
                fig = px.treemap(
                    df_treemap, 
                    path=['Coin'], 
                    values='Value',
                    color='ProfitRate',
                    color_continuous_scale='RdYlGn',  # 빨강(손실) → 노랑(보합) → 초록(수익)
                    color_continuous_midpoint=0,
                    hover_data={'Value': ':,.0f', 'ProfitRate': ':.1f%'}
                )
                fig.update_traces(
                    textinfo="label+percent entry",
                    textfont_size=12
                )
                fig.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10), 
                    height=220,
                    coloraxis_showscale=False  # 컬러바 숨김
                )
                st.plotly_chart(fig, use_container_width=True, key="portfolio_treemap_chart")
                st.caption("🟢 수익 | 🟡 보합 | 🔴 손실")
            else:
                # 도넛차트: 자산이 2개 이하일 때
                fig = px.pie(df_treemap, values='Value', names='Coin', hole=0.4)
                fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=200)
                st.plotly_chart(fig, use_container_width=True, key="portfolio_pie_chart")
    with c2:
        if table_data:
            df = pd.DataFrame(table_data)
            st.dataframe(df.style.apply(lambda x: ['background-color: #fef3c7'] * len(x) if x['_hit'] else [''] * len(x), axis=1), 
                         column_config={"_hit": None, "24H": st.column_config.TextColumn("24H 변동")}, use_container_width=True, height=200)

    # [V7.9] CSV 내보내기 & 코인별 김치 프리미엄
    col_csv, col_kimchi = st.columns(2)
    
    with col_csv:
        if csv_data:
            csv_df = pd.DataFrame(csv_data)
            csv_string = csv_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 포트폴리오 CSV 다운로드",
                data=csv_string,
                file_name=f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col_kimchi:
        with st.expander("🌶️ 코인별 김치 프리미엄 상세"):
            kimchi_rows = []
            coin_tickers = list(set([p['ticker'] for p in portfolio if "Stock" not in p.get('exchange', '')]))
            for ticker in coin_tickers[:5]:  # 상위 5개만
                premium = get_kimchi_premium(ticker, rate)
                if premium is not None:
                    badge = "🔴" if premium > 5 else "🟡" if premium > 2 else "🟢" if premium > 0 else "🔵"
                    kimchi_rows.append(f"{badge} **{ticker}**: {premium:+.2f}%")
            if kimchi_rows:
                for row in kimchi_rows:
                    st.markdown(row)
            else:
                st.caption("김치 프리미엄 데이터를 불러올 수 없습니다.")

    st.divider()
    st.markdown("### 🧠 코인 인텔리전스 (AI & Data)")
    selected = st.selectbox("분석할 코인", list(set([p['ticker'] for p in portfolio])))
    
    if selected:
        with st.spinner(f'{selected} 데이터 및 뉴스 로딩 중...'):
            info = get_coingecko_details(selected, gemini_key)
            w_df = get_weekly_ohlcv(selected, 60)
            news = get_translated_news([selected, f"{selected} coin"], gemini_key)
            rate = get_usd_krw_rate()
            
            if info and w_df is not None:
                col_info, col_tech, col_news = st.columns([1.2, 1, 1])
                
                with col_info:
                    st.markdown(f"#### ℹ️ {info['name']} 정보")
                    
                    # 시총, 순위
                    m1, m2 = st.columns(2)
                    market_cap_krw = info['market_cap'] * rate
                    m1.metric("시총 순위", f"#{info['rank']}")
                    m2.metric("시가총액", f"₩{market_cap_krw/1e12:,.1f}조")
                    
                    # 발행량
                    m3, m4 = st.columns(2)
                    total_supply = info['total_supply'] or 0
                    circ_supply = info['circulating_supply'] or 0
                    m3.metric("총 발행량", f"{total_supply/1e6:,.1f}M" if total_supply else "무제한")
                    m4.metric("유통량", f"{circ_supply/1e6:,.1f}M")
                    
                    # 최고가/최저가 (원화)
                    m5, m6 = st.columns(2)
                    ath_krw = info['ath'] * rate
                    atl_krw = info['atl'] * rate
                    m5.metric("최고가 (ATH)", f"₩{ath_krw:,.0f}", f"{info['ath_change']:+.1f}%")
                    m6.metric("최저가 (ATL)", f"₩{atl_krw:,.0f}", f"{info['atl_change']:+.1f}%")
                    
                    st.markdown("---")
                    st.markdown("**📝 코인 설명**")
                    final_desc = clean_and_translate_desc(info['desc'], gemini_key)
                    st.markdown(f"<div class='scroll-box'>{final_desc}</div>", unsafe_allow_html=True)

                with col_tech:
                    st.markdown("#### 📊 기술적 전망")
                    outlook = analyze_technical(w_df)
                    color = "green" if "매수" in outlook['signal'] else "red" if "매도" in outlook['signal'] else "gray"
                    st.markdown(f"##### 시그널: <span style='color:{color}'>{outlook['signal']}</span>", unsafe_allow_html=True)
                    
                    rsi = RSIIndicator(w_df['c'], 14).rsi().tail(12)
                    fig = go.Figure(go.Scatter(x=rsi.index, y=rsi.values, mode='lines+markers', line=dict(color='#6366f1')))
                    fig.add_hline(y=70, line_dash="dot", line_color="red"); fig.add_hline(y=30, line_dash="dot", line_color="green")
                    st.plotly_chart(fig.update_layout(height=100, margin=dict(l=0,r=0,t=0,b=0), yaxis=dict(showgrid=False), xaxis=dict(showgrid=False)), use_container_width=True, key=f"rsi_sparkline_{selected}")
                    for s in outlook['summary']: st.caption(f"- {s}")

                with col_news:
                    st.markdown("#### 📰 관련 뉴스 (AI 번역)")
                    if news:
                        for n in news[:5]:
                            lang_badge = "🇰🇷" if n.get('lang') == 'ko' else "🇺🇸→🇰🇷" if gemini_key else "🇺🇸"
                            st.markdown(f"<div class='news-card'><div class='news-source'>{lang_badge} {n['source']}</div><a href='{n['link']}' target='_blank' class='news-title'>{n['title']}</a></div>", unsafe_allow_html=True)
                    else: st.info("관련 뉴스가 없습니다.")
                
                if gemini_key:
                     if st.button("✨ Gemini 심층 리포트 생성"):
                        news_context = "\n".join([n['title'] for n in news[:5]])
                        try:
                            prompt = f"""
                            암호화폐 전문가 {selected} 분석:
                            [가격] ${w_df['c'].iloc[-1]:,.2f}, Rank #{info['rank']}
                            [기술] {", ".join(outlook['summary'])}
                            [뉴스] {news_context}
                            1. 호재/악재 판단 2. 단기 전망 및 이유 3. 한국어 답변
                            """
                            res = ask_gemini(gemini_key, prompt, "You are a cryptocurrency analyst.")
                            if res and not res.startswith("❌"):
                                st.markdown(f"<div class='ai-box'>{res}</div>", unsafe_allow_html=True)
                            else:
                                st.error(res)
                        except: st.error("AI 분석 중 오류가 발생했습니다.")
            else:
                st.warning("데이터를 불러올 수 없습니다. (API 제한 등)")

# -----------------------------------------------------------------------------
# 탭 2: 사이클 & 매크로
# -----------------------------------------------------------------------------
def render_macro_tab(fred_key):
    st.markdown("### 🔮 시장 매크로 & 사이클")
    
    # DXY
    dxy_val, dxy_chg = get_dxy_index()
    c0, c_dum = st.columns([1, 3])
    with c0:
        st.markdown("#### 💵 달러 인덱스 (DXY)")
        st.metric("DXY", f"{dxy_val:.2f}", f"{dxy_chg:+.2f}%", delta_color="inverse")
        st.caption("달러 가치가 오르면 비트코인은 주로 하락합니다.")
    
    st.divider()
    
    # Pi Cycle Top Indicator
    st.markdown("#### 1. Pi Cycle Top Indicator")
    with st.expander("ℹ️ Pi Cycle 지표 해석 가이드"):
        st.markdown("""
        **비트코인 고점 탐지기**:
        - <span style='color:orange'>**111일 이동평균선**</span>이 <span style='color:green'>**350일 이동평균선(x2)**</span>을 떫고 올라갈 때(골든크로스)가 역사적 고점이었습니다.
        - 현재 두 선이 만난다면 **강력한 매도 신호**로 간주됩니다.
        """, unsafe_allow_html=True)
    
    btc_df = get_daily_ohlcv("BTC", 1000)
    if btc_df is not None and len(btc_df) > 350:
        ma111 = SMAIndicator(btc_df['c'], 111).sma_indicator()
        ma350x2 = SMAIndicator(btc_df['c'], 350).sma_indicator() * 2
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=btc_df.index, y=btc_df['c'], name='Price', line=dict(color='gray', width=1)))
        fig.add_trace(go.Scatter(x=btc_df.index, y=ma111, name='111 DMA', line=dict(color='orange', width=2)))
        fig.add_trace(go.Scatter(x=btc_df.index, y=ma350x2, name='350 DMA x2', line=dict(color='green', width=2)))
        st.plotly_chart(fig.update_layout(height=350, margin=dict(l=0,r=0,t=0,b=0), hovermode="x unified"), use_container_width=True, key="pi_cycle_chart")
    else:
        st.info("데이터 불러오는 중...")
    
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 😨 공포 & 탐욕 지수")
        fng = get_fear_greed()
        fig = go.Figure(go.Indicator(mode="gauge+number", value=fng, 
            gauge={'axis': {'range': [0, 100]}, 'steps': [{'range': [0, 25], 'color': "#ef4444"}, {'range': [75, 100], 'color': "#22c55e"}]}))
        st.plotly_chart(fig.update_layout(height=250), use_container_width=True, key="fng_gauge_macro")
        with st.expander("지표 해석"):
            st.markdown("- **0~25 (Extreme Fear)**: <span style='color:red'>매수 기회</span> (공포에 사라)", unsafe_allow_html=True)
            st.markdown("- **75~100 (Extreme Greed)**: <span style='color:green'>매도 고려</span> (탐욕에 팜아라)", unsafe_allow_html=True)
            
    with c2:
        st.markdown("#### 🚀 알트코인 시즌 지수")
        dom = get_btc_dominance()
        st.metric("BTC Dominance", f"{dom:.1f}%")
        st.progress(min(dom/100, 1.0))
        if dom < 40: st.success("🎉 알트코인 시즌 (매수 기회)")
        elif dom > 60: st.warning("💎 비트코인 독주장 (알트 주의)")
        else: st.info("⚖️ 중립/순환매 장세")
        with st.expander("도미넌스란?"):
            st.write("전체 코인 시총 중 비트코인이 차지하는 비율입니다. 낮을수록 알트코인 강세장을 의미합니다.")

    st.divider()
    c3, c4, c5 = st.columns(3)
    with c3:
        st.markdown("#### 📉 MVRV Z-Score")
        mvrv = st.number_input("점수 (Manual)", value=st.session_state.manual_data['mvrv_zscore'])
        st.session_state.manual_data['mvrv_zscore'] = mvrv
        if mvrv >= 7: st.error("🚨 고점 (Sell)")
        elif mvrv <= 0: st.success("✅ 저점 (Buy)")
        else: st.info("평가 적정")
        with st.expander("MVRV란?"):
            st.write("시장 가치와 실현 가치의 비율입니다. 0 이하는 저평가(매수), 7 이상은 고평가(매도) 구간입니다.")
        
    with c4:
        st.markdown("#### 📱 코인베이스 앱 순위")
        st.markdown('<a href="https://x.com/COINAppRankBot" target="_blank" class="twitter-btn">🐦 순위 확인</a>', unsafe_allow_html=True)
        rank = st.number_input("Rank (Manual)", value=st.session_state.manual_data['coinbase_rank'])
        st.session_state.manual_data['coinbase_rank'] = rank
        if rank <= 10: st.error("🚨 과열 (Top 10)")
        else: st.success("✅ 안정권")
        with st.expander("인간 지표"):
            st.write("앱스토어 1위는 일반 대중의 광기를 의미합니다. 이때가 단기 고점일 확률이 높습니다.")

    with c5:
        st.markdown("#### 🏭 ISM 제조업 지수")
        ism = st.session_state.manual_data['ism_pmi']
        if fred_key and FRED_AVAILABLE:
            try:
                data = Fred(api_key=fred_key).get_series('ISM/MAN_MANUFACTURING')
                if not data.empty: ism = data.iloc[-1]
            except: pass
        st.metric("Index", f"{ism:.1f}")
        st.progress(min(ism/100, 1.0))
        if ism < 50: st.caption("📉 경기 침체 가능성")
        else: st.caption("📈 경기 확장세")
        with st.expander("경기 지표 해석"):
            st.write("50 이상은 경제 확장, 50 이하는 수축을 의미합니다. 침체기엔 위험자산 회피 성향이 강해질 수 있습니다.")

# -----------------------------------------------------------------------------
# 탭 3: 심층 분석 (V7.6 안정성 강화)
# -----------------------------------------------------------------------------
def render_deep_tab():
    # 1. 고래 추적 섹션
    st.markdown("### 🔎 심층 분석 (실시간 체결 고래 포착)")
    st.caption("대량 체결 내역을 추적합니다. (한국에서는 업비트 데이터 사용)")

    whale_data_loaded = False
    
    # 방법 1: 업비트 API 시도 (한국 거래소 - 지역 제한 없음)
    try:
        url = "https://api.upbit.com/v1/trades/ticks?market=KRW-BTC&count=100"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            trades = res.json()
            rate = get_usd_krw_rate()
            # 5천만원(약 $35,000) 이상 대량 체결
            large = [t for t in trades if t['trade_price'] * t['trade_volume'] > 50000000]
            
            if large:
                df = pd.DataFrame(large)
                df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
                df['side'] = df['ask_bid'].map({'ASK': '🔴 매도', 'BID': '🟢 매수'})
                df['value_krw'] = df['trade_price'] * df['trade_volume']
                df['value_usd'] = df['value_krw'] / rate
                
                display_df = df[['time', 'side', 'trade_price', 'trade_volume', 'value_krw']].sort_values('time', ascending=False)
                display_df.columns = ['시간', '종류', '체결가(₩)', '수량(BTC)', '체결액(₩)']
                
                st.dataframe(
                    display_df.style.format({
                        '체결가(₩)': '₩{:,.0f}', 
                        '수량(BTC)': '{:,.4f}', 
                        '체결액(₩)': '₩{:,.0f}'
                    }), 
                    use_container_width=True,
                    height=300
                )
                whale_data_loaded = True
            else:
                st.info("📉 최근 100건 중 5천만원 이상 대량 체결 없음 (시장 조용)")
                whale_data_loaded = True
    except Exception as e:
        pass  # 업비트 실패 시 다음 방법 시도
    
    # 방법 2: OKX 시도 (한국 접근 가능)
    if not whale_data_loaded and CCXT_AVAILABLE:
        try:
            exchange = ccxt.okx({'timeout': 10000, 'enableRateLimit': True})
            trades = exchange.fetch_trades('BTC/USDT', limit=100)
            large = [t for t in trades if (t['price'] * t['amount']) > 50000]
            
            if large:
                df = pd.DataFrame(large)
                df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
                df['side'] = df['side'].map({'buy': '🟢 매수', 'sell': '🔴 매도'})
                df['value'] = df['price'] * df['amount']
                
                display_df = df[['time', 'side', 'price', 'amount', 'value']].sort_values('time', ascending=False)
                display_df.columns = ['시간', '종류', '체결가($)', '수량(BTC)', '체결액($)']
                
                st.dataframe(
                    display_df.style.format({
                        '체결가($)': '${:,.2f}', 
                        '수량(BTC)': '{:,.4f}', 
                        '체결액($)': '${:,.0f}'
                    }), 
                    use_container_width=True,
                    height=300
                )
                st.caption("📍 데이터 출처: OKX")
                whale_data_loaded = True
            else:
                st.info("📉 최근 100건 중 5만 달러 이상 대량 체결 없음")
                whale_data_loaded = True
        except Exception as e:
            pass
    
    # 모든 방법 실패 시
    if not whale_data_loaded:
        st.warning("⚠️ 고래 데이터를 불러올 수 없습니다.")
        st.info("""
        💡 **가능한 원인:**
        - 네트워크 연결 문제
        - API 일시적 장애
        - 지역 제한 (일부 해외 거래소는 한국에서 접근 불가)
        
        잠시 후 다시 시도해주세요.
        """)

    st.divider()

    # 2. 버핏 지표 섹션 (상관관계)
    st.markdown("### 📊 비트코인 vs 나스닥 상관관계 (버핏 지표)")
    st.caption("💡 비트코인이 증시(나스닥)와 얼마나 비슷하게 움직이는지 보여줍니다. (1.0에 가까울수록 동조화)")

    try:
        if not YFINANCE_AVAILABLE:
            raise Exception("yfinance 라이브러리 없음")
            
        end = datetime.now()
        start = end - timedelta(days=365)
        
        btc = yf.download("BTC-USD", start=start, end=end, progress=False)
        nasdaq = yf.download("^IXIC", start=start, end=end, progress=False)

        if btc.empty or nasdaq.empty:
            raise ValueError("데이터를 불러올 수 없습니다. (Yahoo Finance 응답 없음)")

        # 멀티인덱스 컬럼 처리
        if isinstance(btc.columns, pd.MultiIndex):
            btc = btc['Close'].iloc[:, 0] if len(btc['Close'].shape) > 1 else btc['Close']
        else:
            btc = btc['Close']
            
        if isinstance(nasdaq.columns, pd.MultiIndex):
            nasdaq = nasdaq['Close'].iloc[:, 0] if len(nasdaq['Close'].shape) > 1 else nasdaq['Close']
        else:
            nasdaq = nasdaq['Close']

        # 타임존 제거 및 결합
        btc.index = btc.index.tz_localize(None)
        nasdaq.index = nasdaq.index.tz_localize(None)
        
        df_corr = pd.concat([btc, nasdaq], axis=1).dropna()
        df_corr.columns = ['BTC', 'NASDAQ']
        
        corr = df_corr['BTC'].corr(df_corr['NASDAQ'])
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("상관계수 (최근 1년)", f"{corr:.2f}")
            if corr > 0.7: 
                st.error("🚨 동조화 심화 (커플링)")
                st.caption("증시가 떨어지면 코인도 떨어질 확률 높음")
            elif corr < 0.3: 
                st.success("✅ 탈동조화 (디커플링)")
                st.caption("증시와 독립적으로 움직임")
            else: 
                st.info("⚖️ 일반적 흐름")
        
        with col2:
            df_norm = df_corr / df_corr.iloc[0]
            st.line_chart(df_norm)
        
        with st.expander("버핏 지표 해석"):
            st.markdown("""
            - **상관계수 0.7 이상**: 비트코인이 주식처럼 움직임 (매크로 영향 큼)
            - **상관계수 0.3 이하**: 비트코인이 독립 자산으로 움직임
            - **투자 전략**: 디커플링 시 포트폴리오 분산 효과가 높아집니다.
            """)

    except Exception as e:
        st.error(f"⚠️ 차트 분석 실패: {e}")
        st.caption("일시적인 네트워크 오류일 수 있습니다. 나중에 다시 시도해주세요.")

# -----------------------------------------------------------------------------
# 탭 4: 뉴스 & 알림
# -----------------------------------------------------------------------------
def render_news_tab(gemini_key):
    st.markdown("### 📰 코인 전문 뉴스룸")
    st.caption("📰 블록미디어 | 🪙 토큰포스트 | 🌐 CoinDesk | 📡 CoinTelegraph | 🧱 The Block")
    
    # 상단 컨트롤
    col_status, col_refresh = st.columns([3, 1])
    with col_status:
        if gemini_key:
            st.success("✅ AI 번역 활성화 (Gemini)")
        else:
            st.warning("⚠️ 해외 뉴스 원문 표시 (API 키 필요)")
    with col_refresh:
        if st.button("🔄 새로고침", use_container_width=True):
            # 뉴스 캐시만 클리어
            get_translated_news.clear()
            st.rerun()
    
    st.divider()
    
    c1, c2 = st.columns([2, 1])
    
    with c1:
        with st.spinner("뉴스를 불러오는 중..."):
            # API 키가 있으면 항상 번역 시도
            news = get_translated_news([], gemini_key)
        
        if news:
            # 번역 통계
            translated_count = sum(1 for n in news if '→🇰🇷' in n.get('source', ''))
            english_count = sum(1 for n in news if n.get('lang') == 'en')
            korean_count = len(news) - translated_count - english_count
            
            st.markdown(f"#### 📰 최신 뉴스 ({len(news)}건)")
            if gemini_key and translated_count > 0:
                st.caption(f"🇰🇷 국내 {korean_count}건 | 🇺🇸→🇰🇷 번역 {translated_count}건")
            elif english_count > 0:
                st.caption(f"🇰🇷 국내 {korean_count}건 | 🌐 영어 {english_count}건")
            
            for n in news:
                # 번역된 해외 뉴스 구분
                is_translated = '→🇰🇷' in n.get('source', '')
                is_english = n.get('lang', '') == 'en'
                
                if is_translated:
                    bg_color = "#e0f2fe"  # 파란 배경 (번역됨)
                    border_color = "#0284c7"
                elif is_english:
                    bg_color = "#fef3c7"  # 노란 배경 (영어 원문)
                    border_color = "#f59e0b"
                else:
                    bg_color = "#ffffff"  # 흰 배경 (한국어)
                    border_color = "#e5e7eb"
                
                st.markdown(f"""
                <div style="background-color: {bg_color}; padding: 12px; border-radius: 8px; margin-bottom: 8px; border: 1px solid {border_color};">
                    <div style="font-size: 0.8em; color: #64748b; font-weight: 600; margin-bottom: 4px;">{n['source']}</div>
                    <a href="{n['link']}" target="_blank" style="color: #1e293b; text-decoration: none; font-size: 1em; font-weight: 500;">
                        {n['title']}
                    </a>
                    <div style="font-size: 0.75em; color: #94a3b8; margin-top: 4px;">{n.get('date', '')}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # 범례
            st.markdown("""
            <div style="font-size: 0.8em; color: #64748b; margin-top: 10px; padding: 8px; background: #f8fafc; border-radius: 4px;">
                ⬜ 국내 뉴스 | 🟦 AI 번역 완료 | 🟨 영어 원문
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("뉴스를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.")
            
        # 매체 안내
        with st.expander("📋 수집 매체 안내"):
            st.markdown("""
            **🇰🇷 국내 코인 전문 매체**
            - 📰 블록미디어: 심층 분석
            - 🪙 토큰포스트: 시장 동향
            
            **🌐 해외 코인 전문 매체**
            - CoinDesk: 글로벌 메이저 (AI 번역)
            - CoinTelegraph: 업계 분석 (AI 번역)
            - The Block: 기관 동향 (AI 번역)
            
            💡 Gemini API 키가 설정되면 해외 뉴스가 자동 번역됩니다.
            """)
    
    with c2:
        st.markdown("#### 🚨 알림 센터")
        signals = []
        
        mvrv = st.session_state.manual_data.get('mvrv_zscore', 0)
        if mvrv >= 7: 
            signals.append(("🔥 MVRV Z-Score 고평가", "error"))
        elif mvrv >= 5:
            signals.append(("⚠️ MVRV 주의 구간", "warning"))
            
        # 김치 프리미엄 알림
        try:
            rate = get_usd_krw_rate()
            btc_k = get_market_price("BTC", "Upbit")[0]
            btc_u = get_market_price("BTC", "Binance")[0]
            kimchi = ((btc_k / (btc_u * rate)) - 1) * 100 if btc_u > 0 else 0
            if kimchi > 5:
                signals.append((f"🌶️ 김치 프리미엄 과열 ({kimchi:.1f}%)", "error"))
            elif kimchi < -2:
                signals.append((f"🧊 역프리미엄 발생 ({kimchi:.1f}%)", "info"))
        except:
            pass
        
        if signals: 
            for sig, sig_type in signals:
                if sig_type == "error":
                    st.error(sig)
                elif sig_type == "warning":
                    st.warning(sig)
                else:
                    st.info(sig)
        else: 
            st.success("✅ 특이사항 없음")
        
        # API 키 상태
        st.divider()
        st.markdown("#### 🔑 번역 상태")
        if gemini_key:
            st.success("✅ Gemini 연결됨")
            st.caption("해외 뉴스 자동 번역 활성화")
        else:
            st.warning("⚠️ Gemini API 키 필요")
            st.caption("사이드바에서 API 키를 설정하면\n해외 뉴스가 한국어로 번역됩니다")

# -----------------------------------------------------------------------------
# 탭 5: 도구
# -----------------------------------------------------------------------------
def render_tools_tab():
    st.markdown("### 🧮 FOMO 계산기")
    st.caption("💡 '그때 샀으면...' 과거 투자 시뮬레이션 - 어떤 코인이든 계산 가능!")
    
    # 계산 방식 선택
    calc_mode = st.radio("계산 방식", ["🇺🇸 USD (달러)", "🇰🇷 KRW (원화)"], horizontal=True)
    
    # 코인 자유 입력
    col_coin, col_date, col_amt = st.columns([1, 1, 1])
    
    with col_coin:
        coin_input = st.text_input(
            "코인 티커", 
            value="BTC",
            placeholder="예: BTC, ETH, SOL, XRP, DOGE, PEPE...",
            help="코인 심볼을 입력하세요 (대소문자 무관)"
        ).strip().upper()
    
    with col_date:
        date = st.date_input(
            "투자 날짜", 
            datetime.now() - timedelta(days=365), 
            min_value=datetime(2015, 1, 1),
            max_value=datetime.now() - timedelta(days=1)
        )
    
    with col_amt:
        if calc_mode == "🇺🇸 USD (달러)":
            amt = st.number_input("투자금 (USD)", min_value=1, value=1000, step=100)
            currency_symbol = "$"
        else:
            amt = st.number_input("투자금 (만원)", min_value=1, value=100, step=10)
            currency_symbol = "₩"
    
    # 인기 코인 바로가기
    st.caption("🔥 인기 코인:")
    quick_cols = st.columns(8)
    quick_coins = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "PEPE", "SHIB"]
    for i, qc in enumerate(quick_coins):
        if quick_cols[i].button(qc, key=f"quick_{qc}", use_container_width=True):
            st.session_state['fomo_coin'] = qc
            st.rerun()
    
    # 세션에서 코인 가져오기
    if 'fomo_coin' in st.session_state:
        coin_input = st.session_state['fomo_coin']
        del st.session_state['fomo_coin']
    
    if st.button("📊 계산하기", type="primary", use_container_width=True):
        if not coin_input:
            st.error("코인 티커를 입력해주세요.")
            return
            
        try:
            if calc_mode == "🇺🇸 USD (달러)":
                # Yahoo Finance 사용 (USD)
                if YFINANCE_AVAILABLE:
                    ticker_symbol = f"{coin_input}-USD"
                    
                    with st.spinner(f"{coin_input} 데이터 조회 중..."):
                        df = yf.download(ticker_symbol, start=date, end=date + timedelta(days=7), progress=False)
                        
                        if df.empty:
                            st.error(f"❌ '{coin_input}' 데이터를 찾을 수 없습니다. 티커를 확인해주세요.")
                            st.caption("예: Bitcoin → BTC, Ethereum → ETH, Solana → SOL")
                            return
                        
                        # 멀티인덱스 처리
                        if isinstance(df.columns, pd.MultiIndex):
                            past = float(df['Close'].iloc[0, 0])
                        else:
                            past = float(df['Close'].iloc[0])
                        
                        curr_df = yf.Ticker(ticker_symbol).history(period="1d")
                        if curr_df.empty:
                            st.error("현재 가격을 불러올 수 없습니다.")
                            return
                            
                        curr = float(curr_df['Close'].iloc[-1])
                        
                        # 수익 계산
                        coins_bought = amt / past
                        current_value = coins_bought * curr
                        profit = current_value - amt
                        profit_pct = (profit / amt) * 100
                        
                        # 결과 표시
                        st.divider()
                        st.markdown(f"#### 📈 {coin_input} 투자 시뮬레이션 결과")
                        
                        r1, r2, r3 = st.columns(3)
                        r1.metric("매수 당시 가격", f"${past:,.4f}")
                        r2.metric("현재 가격", f"${curr:,.4f}", f"{((curr-past)/past)*100:+.1f}%")
                        r3.metric("보유 수량", f"{coins_bought:,.6f} {coin_input}")
                        
                        st.divider()
                        if profit >= 0:
                            st.success(f"🎉 **${amt:,}** 투자 → 현재 가치: **${current_value:,.2f}** (수익: **${profit:+,.2f}**, **{profit_pct:+.1f}%**)")
                        else:
                            st.error(f"😢 **${amt:,}** 투자 → 현재 가치: **${current_value:,.2f}** (손실: **${profit:,.2f}**, **{profit_pct:.1f}%**)")
                else:
                    st.error("yfinance 라이브러리가 필요합니다.")
            
            else:
                # 업비트 사용 (KRW)
                with st.spinner(f"업비트에서 {coin_input} 데이터 조회 중..."):
                    # 업비트 일봉 API
                    date_str = date.strftime("%Y-%m-%dT09:00:00")
                    url = f"https://api.upbit.com/v1/candles/days?market=KRW-{coin_input}&to={date_str}&count=1"
                    res = requests.get(url, timeout=5)
                    
                    if res.status_code != 200 or not res.json():
                        st.error(f"❌ 업비트에서 '{coin_input}' 데이터를 찾을 수 없습니다.")
                        st.caption("업비트에 상장된 코인인지, 해당 날짜에 상장되어 있었는지 확인해주세요.")
                        return
                    
                    past_data = res.json()[0]
                    past = past_data['trade_price']
                    
                    # 현재가 조회
                    curr_url = f"https://api.upbit.com/v1/ticker?markets=KRW-{coin_input}"
                    curr_res = requests.get(curr_url, timeout=3)
                    
                    if curr_res.status_code != 200 or not curr_res.json():
                        st.error("현재 가격을 불러올 수 없습니다.")
                        return
                        
                    curr = curr_res.json()[0]['trade_price']
                    
                    # 수익 계산 (만원 단위)
                    amt_krw = amt * 10000
                    coins_bought = amt_krw / past
                    current_value = coins_bought * curr
                    profit = current_value - amt_krw
                    profit_pct = (profit / amt_krw) * 100
                    
                    # 결과 표시
                    st.divider()
                    st.markdown(f"#### 📈 {coin_input} 투자 시뮬레이션 결과 (업비트 기준)")
                    
                    r1, r2, r3 = st.columns(3)
                    r1.metric("매수 당시 가격", f"₩{past:,.0f}")
                    r2.metric("현재 가격", f"₩{curr:,.0f}", f"{((curr-past)/past)*100:+.1f}%")
                    r3.metric("보유 수량", f"{coins_bought:,.6f} {coin_input}")
                    
                    st.divider()
                    if profit >= 0:
                        st.success(f"🎉 **{amt}만원** 투자 → 현재 가치: **₩{current_value:,.0f}** (수익: **₩{profit:+,.0f}**, **{profit_pct:+.1f}%**)")
                    else:
                        st.error(f"😢 **{amt}만원** 투자 → 현재 가치: **₩{current_value:,.0f}** (손실: **₩{profit:,.0f}**, **{profit_pct:.1f}%**)")
                        
        except Exception as e:
            st.error(f"오류 발생: {e}")
            st.caption("코인 티커가 올바른지 확인해주세요.")
    
    # 참고 정보
    with st.expander("💡 사용 팁"):
        st.markdown("""
        **코인 티커 예시**
        - 비트코인: `BTC` | 이더리움: `ETH` | 솔라나: `SOL`
        - 리플: `XRP` | 도지코인: `DOGE` | 페페: `PEPE`
        - 시바이누: `SHIB` | 에이다: `ADA` | 폴카닷: `DOT`
        
        **데이터 출처**
        - USD 계산: Yahoo Finance (2014년~ 대부분의 코인 지원)
        - KRW 계산: 업비트 (상장일 이후 데이터)
        
        ⚠️ 실제 거래 수수료, 세금 등은 반영되지 않습니다.
        """)

# -----------------------------------------------------------------------------
# 탭: AI 투자 위원회 (V8.1 - Groq 오픈소스 모델 + 히스토리)
# -----------------------------------------------------------------------------
def render_ai_council_tab(gemini_key, openai_key, claude_key, grok_key, groq_key):
    st.markdown("### 🤖 AI 투자 위원회 V8.1 (다중 모델 Cross-Check)")
    st.caption("다양한 AI 모델들이 각자의 페르소나로 시장을 분석하고 투표합니다. Groq 무료 API로 오픈소스 모델 사용 가능!")

    # 분석 대상 코인 선택
    if not st.session_state.portfolio:
        st.info("👈 먼저 포트폴리오에 자산을 추가해주세요.")
        return
    
    coins = list(set([p['ticker'] for p in st.session_state.portfolio if "Stock" not in p.get('exchange', '')]))
    if not coins:
        st.warning("분석할 코인이 없습니다.")
        return
        
    target_coin = st.selectbox("📋 위원회 안건 상정 (코인 선택)", coins, key="council_coin")
    
    # 프롬프트 데이터 준비
    info = get_coingecko_details(target_coin, gemini_key)
    rate = get_usd_krw_rate()
    cur_price, _ = get_market_price(target_coin, 'Binance')
    price_info = f"현재가: ${cur_price:,.2f}, 시총순위: {info.get('rank', '-')}위"
    
    context_prompt = f"""
    [시장 데이터]
    - 대상 자산: {target_coin} ({price_info})
    - 현재 상황: 비트코인과 시장 전반의 데이터를 참고하여 투자 조언을 해줘.
    - MVRV Z-Score: {st.session_state.manual_data.get('mvrv_zscore', 2.2)}
    
    위 데이터를 바탕으로 투자 의견(매수/매도/관망)을 제시하고, 너의 역할(Persona)에 맞춰서 그 이유를 3줄 이내로 핵심만 한국어로 설명해.
    마지막에 반드시 [결론: 매수/매도/관망] 형태로 표시해.
    """

    # 위원회 현황 - 2줄로 확장
    st.markdown("#### 👥 위원회 구성")
    
    # 1행: 기존 유료 API (Gemini, GPT만 현실적으로 사용 가능)
    st.markdown("**💎 프리미엄 API**")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🧠 Gemini", "📊 퀀트분석" if gemini_key else "❌ 미설정")
    c2.metric("💼 GPT-4o", "🏦 펀드매니저" if openai_key else "❌ 미설정")
    c3.metric("🔮 Claude", "📈 데이터분석" if claude_key else "❌ 미설정", help="유료 API 필요")
    c4.metric("🌍 Grok", "🏛️ 거시경제" if grok_key else "❌ 미설정", help="xAI 유료 API")
    
    # 2행: Groq 오픈소스 모델들 (무료!)
    st.markdown("**🆓 Groq 오픈소스 (무료) - Meta Llama**")
    g1, g2 = st.columns(2)
    g1.metric("🦙 Llama 3.3 70B", "📈 온체인분석" if groq_key else "❌ 미설정")
    g2.metric("🦙 Llama 4 Scout", "🛡️ 리스크분석" if groq_key else "❌ 미설정")
    
    # API 키 상태 안내
    active_count = sum([bool(gemini_key), bool(openai_key), bool(claude_key), bool(grok_key)])
    groq_count = 2 if groq_key else 0  # Groq 하나로 2개 모델 사용 (Llama 3.3 + Llama 4)
    total_members = active_count + groq_count
    
    if total_members == 0:
        st.error("⚠️ 최소 1개 이상의 API 키를 설정해주세요. Groq API는 무료로 발급받을 수 있습니다!")
        st.markdown("[👉 Groq 무료 API 키 발급하기](https://console.groq.com/keys)")
        return
    elif total_members < 3:
        st.warning(f"💡 현재 {total_members}명 위원만 활성화됨. Groq API 추가 시 최대 6명까지 확장 가능!")
    else:
        st.success(f"✅ {total_members}명의 AI 위원이 대기 중입니다.")

    if st.button("🗳️ 위원회 소집 및 투표 시작", type="primary", use_container_width=True):
        with st.spinner("⚡ AI 위원들이 동시에 분석 중입니다... (약 5~10초 소요)"):
            opinions = {}
            
            # 병렬 호출을 위한 작업 정의
            def call_gemini():
                if gemini_key:
                    result = ask_gemini(gemini_key, context_prompt, "당신은 퀀트 분석가입니다. 기술적 지표, 거래량, 변동성 등 정량적 데이터를 기반으로 분석합니다. 한국어로 답변하세요.")
                    return ('🧠 Gemini (퀀트분석)', result)
                return None
            
            def call_chatgpt():
                if openai_key:
                    return ('💼 GPT-4o (펀드매니저)', ask_chatgpt(openai_key, context_prompt))
                return None
            
            def call_claude():
                if claude_key:
                    return ('🔮 Claude (데이터분석)', ask_claude(claude_key, context_prompt))
                return None
            
            def call_grok():
                if grok_key:
                    return ('🌍 Grok (거시경제)', ask_grok(grok_key, context_prompt))
                return None
            
            # Groq 오픈소스 모델들 (Meta Llama - 미국)
            def call_groq_llama():
                if groq_key:
                    return ('🦙 Llama 3.3 70B (온체인분석)', ask_groq_llama(groq_key, context_prompt))
                return None
            
            def call_groq_llama4():
                if groq_key:
                    return ('🦙 Llama 4 Scout (리스크분석)', ask_groq_llama4(groq_key, context_prompt))
                return None
            
            # ThreadPoolExecutor로 병렬 실행 (최대 6개 모델)
            with ThreadPoolExecutor(max_workers=6) as executor:
                futures = [
                    executor.submit(call_gemini),
                    executor.submit(call_chatgpt),
                    executor.submit(call_claude),
                    executor.submit(call_grok),
                    executor.submit(call_groq_llama),
                    executor.submit(call_groq_llama4)
                ]
                
                for future in as_completed(futures):
                    try:
                        result = future.result(timeout=30)
                        if result:  # None이 아닌 경우만
                            name, text = result
                            opinions[name] = text
                    except Exception as e:
                        pass

        # 결과 표시 (카드 형태)
        st.divider()
        st.markdown("#### 💬 위원회 검토 의견서")
        
        buy_vote = 0; sell_vote = 0; hold_vote = 0
        cols = st.columns(2)
        idx = 0
        
        for name, text in opinions.items():
            # 투표 집계
            text_lower = text.lower()
            if "매수" in text or "buy" in text_lower: 
                buy_vote += 1
                box_color = "#d1fae5"  # 초록 배경
                vote_icon = "🟢"
            elif "매도" in text or "sell" in text_lower: 
                sell_vote += 1
                box_color = "#fee2e2"  # 빨강 배경
                vote_icon = "🔴"
            else: 
                hold_vote += 1
                box_color = "#fef3c7"  # 노랑 배경
                vote_icon = "🟡"
            
            with cols[idx % 2]:
                st.markdown(f"""
                <div style="background-color: {box_color}; padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #ccc;">
                    <div style="font-weight: bold; margin-bottom: 5px; color: #1e40af;">{vote_icon} {name}</div>
                    <div style="font-size: 0.9em; line-height: 1.5;">{text}</div>
                </div>
                """, unsafe_allow_html=True)
            idx += 1
        
        # 최종 결론
        total = len(opinions)
        result_color = "#6b7280"
        result_text = "⚪ 판단 보류 (Neutral)"
        
        if buy_vote > sell_vote and buy_vote > hold_vote: 
            result_text = "🟢 매수 우위 (Buy Consensus)"
            result_color = "#22c55e"
        elif sell_vote > buy_vote and sell_vote > hold_vote:
            result_text = "🔴 매도 우위 (Sell Consensus)"
            result_color = "#ef4444"
        elif hold_vote > buy_vote:
            result_text = "🟡 관망 우위 (Hold Consensus)"
            result_color = "#eab308"
            
        st.markdown("---")
        st.markdown(f"### 📢 위원회 최종 결론: <span style='color:{result_color}; font-weight:bold;'>{result_text}</span>", unsafe_allow_html=True)
        
        col_v1, col_v2, col_v3 = st.columns(3)
        col_v1.metric("🟢 매수", f"{buy_vote}표")
        col_v2.metric("🔴 매도", f"{sell_vote}표")
        col_v3.metric("🟡 관망", f"{hold_vote}표")
        
        # 신뢰도 표시
        if total >= 3:
            agreement_rate = max(buy_vote, sell_vote, hold_vote) / total * 100
            if agreement_rate >= 70:
                st.success(f"✅ 높은 합의율! ({agreement_rate:.0f}% 일치, {total}명 참여)")
            elif agreement_rate >= 50:
                st.info(f"📊 보통 합의율 ({agreement_rate:.0f}% 일치, {total}명 참여)")
            else:
                st.warning(f"⚠️ 의견 분분 ({agreement_rate:.0f}% 일치, {total}명 참여) - 신중한 판단 필요")
        else:
            st.caption(f"💡 총 {total}명 위원 참여 - 더 많은 API 키 추가 시 신뢰도 향상")

        # [V8.3] One-Voice 통합 결론 (의장 모델: Gemini or GPT-4)
        st.markdown("---")
        st.markdown("### 👨‍⚖️ 의장(Chairperson) 종합 의견 (One-Voice)")
        
        chair_model = "gemini" if gemini_key else ("openai" if openai_key else None)
        
        if chair_model and opinions:
            with st.spinner("👨‍⚖️ 의장이 위원들의 의견을 종합 중입니다..."):
                # 의견 통합 프롬프트 구성
                all_opinions = "\n".join([f"- {k}: {v}" for k, v in opinions.items()])
                
                synthesis_prompt = f"""
                [위원들의 의견 요약]
                {all_opinions}
                
                [시장 데이터]
                {context_prompt}
                
                당신은 이 위원회의 의장입니다. 위원들의 의견이 갈릴 경우, 다수결과 논리적 타당성을 고려하여 최종 결론을 내려주세요.
                특히 리스크 관리 관점과 수익 추구 관점을 균형있게 종합하여, 사용자에게 명확한 한 가지 행동 지침을 제시하세요.
                
                형식:
                1. 📢 최종 결론: [매수/매도/관망]
                2. ⚖️ 종합 판단 근거 (3가지 핵심 요약)
                3. 💡 구체적 행동 가이드 (진입가/손절가 등 제안 가능하면 포함)
                
                한국어로 답변하세요.
                """
                
                try:
                    final_verdict = ""
                    if chair_model == "gemini":
                        final_verdict = ask_gemini(gemini_key, synthesis_prompt)
                    elif chair_model == "openai":
                        final_verdict = ask_chatgpt(openai_key, synthesis_prompt)
                        
                    if final_verdict:
                        st.info(f"🎙️ **One-Voice 결론 ({'Gemini' if chair_model=='gemini' else 'GPT-4o'} Pro)**")
                        st.markdown(final_verdict)
                except Exception as e:
                    st.error(f"의장 의견 도출 실패: {e}")
        else:
            st.caption("💡 Gemini 또는 OpenAI 키가 설정되어야 의장 의견을 들을 수 있습니다.")
        
        # [V8.1] AI 위원회 결과 히스토리 저장
        try:
            db = init_firebase()
            if db and st.session_state.get('username'):
                # 결과 데이터 구성
                consensus = "buy" if buy_vote > sell_vote and buy_vote > hold_vote else \
                           "sell" if sell_vote > buy_vote and sell_vote > hold_vote else "hold"
                
                council_result = {
                    'coin': target_coin,
                    'date': datetime.now().strftime("%Y-%m-%d"),
                    'time': datetime.now().strftime("%H:%M"),
                    'consensus': consensus,
                    'buy_votes': buy_vote,
                    'sell_votes': sell_vote,
                    'hold_votes': hold_vote,
                    'total_members': total,
                    'agreement_rate': agreement_rate if total >= 3 else 0,
                    'price_at_decision': cur_price,
                    'timestamp': firestore.SERVER_TIMESTAMP
                }
                
                # 저장
                history_ref = db.collection("users").document(st.session_state.username).collection("ai_council_history")
                history_ref.add(council_result)
                st.toast("📝 위원회 결과가 기록되었습니다!", icon="✅")
        except Exception as e:
            pass  # 저장 실패해도 진행
    
    # =========================================================================
    # [V8.1] AI 위원회 히스토리 조회
    # =========================================================================
    st.divider()
    with st.expander("📜 AI 위원회 결과 히스토리", expanded=False):
        try:
            db = init_firebase()
            if db and st.session_state.get('username'):
                history_ref = db.collection("users").document(st.session_state.username).collection("ai_council_history")
                
                # 선택한 코인의 최근 10개 기록
                docs = history_ref.where("coin", "==", target_coin).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(10).stream()
                
                history_list = []
                for doc in docs:
                    data = doc.to_dict()
                    history_list.append({
                        '날짜': data.get('date', '-'),
                        '시간': data.get('time', '-'),
                        '결론': '🟢 매수' if data.get('consensus') == 'buy' else '🔴 매도' if data.get('consensus') == 'sell' else '🟡 관망',
                        '매수표': data.get('buy_votes', 0),
                        '매도표': data.get('sell_votes', 0),
                        '관망표': data.get('hold_votes', 0),
                        '합의율': f"{data.get('agreement_rate', 0):.0f}%",
                        '당시가격': f"${data.get('price_at_decision', 0):,.2f}"
                    })
                
                if history_list:
                    st.markdown(f"**📊 {target_coin} 위원회 기록 (최근 10회)**")
                    df_history = pd.DataFrame(history_list)
                    st.dataframe(df_history, use_container_width=True, hide_index=True)
                    
                    # 통계
                    buy_count = sum(1 for h in history_list if '매수' in h['결론'])
                    sell_count = sum(1 for h in history_list if '매도' in h['결론'])
                    hold_count = sum(1 for h in history_list if '관망' in h['결론'])
                    
                    st.caption(f"📈 누적 통계: 매수 {buy_count}회 | 매도 {sell_count}회 | 관망 {hold_count}회")
                    
                    # 가격 변화 분석 (첫 기록 대비)
                    if len(history_list) > 1:
                        first_price = float(history_list[-1]['당시가격'].replace('$', '').replace(',', ''))
                        if first_price > 0 and cur_price > 0:
                            price_change = (cur_price - first_price) / first_price * 100
                            st.caption(f"💰 첫 기록 대비 가격 변화: {price_change:+.1f}%")
                else:
                    st.info("아직 기록된 위원회 결과가 없습니다. 위원회를 소집해보세요!")
            else:
                st.warning("로그인 후 이용 가능합니다.")
        except Exception as e:
            st.caption(f"히스토리 조회 중 오류: {str(e)[:50]}")


# -----------------------------------------------------------------------------
# 탭: 매도 전략 (Smart Exit Planner) - V7.3 Macro & Tech
# -----------------------------------------------------------------------------
def render_exit_strategy_tab():
    st.markdown("### 📉 종합 매도 타이밍 (Macro & Tech)")
    st.caption("기술적 지표뿐만 아니라 **거시적 이벤트(재료)**를 종합하여 최적의 매도 시점을 판단합니다.")

    if not st.session_state.portfolio:
        st.info("👈 사이드바에서 코인 자산을 추가해주세요.")
        return

    coin_list = [p['ticker'] for p in st.session_state.portfolio if "Stock" not in p.get('exchange', '')]
    if not coin_list:
        st.warning("매도 전략을 세울 코인 자산이 없습니다.")
        return

    # -------------------------------------------------------------------------
    # 1. 매크로 이벤트 체크리스트
    # -------------------------------------------------------------------------
    st.markdown("#### 1️⃣ 매크로 이벤트 반영 (Market Euphoria)")
    st.info("🔔 시장에 큰 영향을 주는 초대형 뉴스가 확정되었나요? 직접 체크해주세요.")

    col_evt1, col_evt2 = st.columns(2)
    
    with col_evt1:
        check_clarity = st.checkbox("🇺🇸 CLARITY 법안(규제 명확화) 통과", help="법적 리스크 해소로 기관 자금 유입 본격화")
        check_trump = st.checkbox("🏛️ 트럼프 '비트코인 전략 비축' 공식 발표", help="국가 차원 매입, 슈퍼 사이클 시작")
    
    with col_evt2:
        check_ripple = st.checkbox("💧 리플(XRP) IPO 확정", help="불장 후반부 신호")
        check_spacex = st.checkbox("🚀 스페이스X IPO 확정", help="금융 시장 유동성 정점 신호")

    # 이벤트 점수 계산
    macro_score = 0
    macro_reasons = []
    if check_clarity: macro_score += 10; macro_reasons.append("🇺🇸 CLARITY 법안 통과")
    if check_trump: macro_score += 20; macro_reasons.append("🏛️ 트럼프 비축 발표 (슈퍼 사이클)")
    if check_ripple: macro_score += 15; macro_reasons.append("💧 리플 IPO (유동성 피크)")
    if check_spacex: macro_score += 15; macro_reasons.append("🚀 스페이스X IPO")

    # -------------------------------------------------------------------------
    # 2. 종합 매도 시그널 (Euphoria Index)
    # -------------------------------------------------------------------------
    st.divider()
    st.markdown("#### 2️⃣ 종합 매도 시그널 (Euphoria Index)")
    
    # 기술적 점수 계산 (BTC 기준)
    w_df = get_weekly_ohlcv("BTC", 60)
    mvrv = st.session_state.manual_data['mvrv_zscore']
    fng = get_fear_greed()
    
    tech_score = 0
    tech_reasons = []
    
    # RSI 점수 (0~40점)
    rsi = 50
    if w_df is not None and TA_AVAILABLE:
        rsi = RSIIndicator(w_df['c'], 14).rsi().iloc[-1]
        if rsi >= 80: tech_score += 40; tech_reasons.append(f"🔥 주봉 RSI {rsi:.0f} (초과열)")
        elif rsi >= 70: tech_score += 30; tech_reasons.append(f"🔥 주봉 RSI {rsi:.0f} (과열)")
        elif rsi >= 60: tech_score += 10
        
    # MVRV 점수 (0~30점)
    if mvrv >= 7.0: tech_score += 30; tech_reasons.append("📉 MVRV 7.0+ (역사적 고점)")
    elif mvrv >= 3.5: tech_score += 20; tech_reasons.append("📉 MVRV 3.5+ (고평가)")
    
    # 공포탐욕 점수 (0~20점)
    if fng >= 90: tech_score += 20; tech_reasons.append(f"😱 극단적 탐욕 ({fng})")
    elif fng >= 75: tech_score += 10; tech_reasons.append(f"😨 탐욕 단계 ({fng})")
    
    # 종합 점수
    total_score = min(tech_score + macro_score, 100)
    
    # 게이지 차트
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=total_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "종합 매도 권장 지수", 'font': {'size': 20}},
        delta={'reference': 50, 'increasing': {'color': "red"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 40], 'color': "#22c55e"},
                {'range': [40, 70], 'color': "#eab308"},
                {'range': [70, 90], 'color': "#f97316"},
                {'range': [90, 100], 'color': "#ef4444"}
            ],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': total_score}
        }
    ))
    fig.update_layout(height=280, margin=dict(t=30, b=10))
    st.plotly_chart(fig, use_container_width=True, key="euphoria_gauge")
    
    # 점수 분석 및 AI 전략 제안
    c_res, c_act = st.columns([2, 1])
    with c_res:
        st.write("##### 📊 점수 분석")
        all_reasons = tech_reasons + macro_reasons
        if all_reasons:
            for r in all_reasons: st.caption(f"• {r}")
        else:
            st.caption("• 특이 신호 없음")
        
    with c_act:
        st.write("##### 🤖 AI 전략 제안")
        if total_score >= 85:
            st.error("🚨 **적극 매도**\n\n기술적 과열 + 매크로 호재. 현금 비중 70%↑ 권장")
        elif total_score >= 60:
            st.warning("⚠️ **분할 매도**\n\n시장 과열 징조. 상승마다 10~20% 청산")
        else:
            st.success("✅ **보유 유지**\n\n아직 과열되지 않음. 추세 유지")

    st.divider()
    
    # -------------------------------------------------------------------------
    # 3. 개별 코인 분할 매도 설정
    # -------------------------------------------------------------------------
    st.markdown("#### 3️⃣ 개별 코인 분할 매도 설정")
    
    selected_coin = st.selectbox("전략을 적용할 코인", coin_list)
    target_asset = next((p for p in st.session_state.portfolio if p['ticker'] == selected_coin), None)
    current_qty = target_asset['quantity']
    avg_price = target_asset['avg_price']
    
    cur_price, currency = get_market_price(selected_coin, target_asset.get('exchange', 'Binance'))
    rate = get_usd_krw_rate()
    k_rate = rate if currency == "USD" else 1
    
    c_set1, c_set2 = st.columns([1, 2])
    with c_set1:
        steps = st.radio("분할 횟수", [3, 4, 5], horizontal=True, key="exit_steps")
        st.info(f"보유: **{current_qty:,.4f} {selected_coin}**")
        st.caption(f"현재가: ₩{cur_price * k_rate:,.0f}")
    
    with c_set2:
        # 슈퍼 사이클 목표가 상향
        boost_price = 1.0
        if check_trump or check_clarity:
            st.caption("✨ **슈퍼 사이클 감지**: 매크로 호재 반영하여 목표가 상향?")
            if st.toggle("목표가 +20% 상향", value=False, key="boost_toggle"):
                boost_price = 1.2
                st.success("목표가가 20% 상향 조정됩니다.")

    # 매도 계획 입력
    exit_plan = []
    total_percent = 0
    total_expected_krw = 0
    
    st.markdown("##### 📝 구간별 목표가 및 비중")
    
    for i in range(1, steps + 1):
        col_price, col_pct, col_result = st.columns([1.5, 1, 2])
        
        with col_price:
            default_price = (cur_price * k_rate) * (1 + (0.25 * i)) * boost_price
            target_p = st.number_input(f"{i}차 (₩)", value=float(int(default_price)), step=10000.0, key=f"exit_v3_p_{i}")
            
        with col_pct:
            default_pct = 100 // steps
            if i == steps: default_pct = 100 - (default_pct * (steps - 1))
            target_pct = st.number_input(f"비중%", value=default_pct, min_value=0, max_value=100, key=f"exit_v3_pct_{i}")
            total_percent += target_pct
            
        with col_result:
            sell_qty = current_qty * (target_pct / 100)
            sell_amt = sell_qty * target_p
            total_expected_krw += sell_amt
            
            cur_price_krw = cur_price * k_rate
            status = "✅" if cur_price_krw >= target_p else "⏳"
            
            st.markdown(f"<div style='margin-top:20px;font-size:0.9em;'>{sell_qty:,.4f}개 / ₩{sell_amt:,.0f} {status}</div>", unsafe_allow_html=True)
            
        exit_plan.append({"차수": f"{i}차", "목표가": target_p, "비중": target_pct, "매도수량": sell_qty, "예상금액": sell_amt})

    st.divider()
    
    # 최종 결과
    if total_percent != 100:
        st.error(f"⚠️ 비중 합계: {total_percent}% (100%가 되어야 함)")
    else:
        total_cost_krw = current_qty * avg_price * k_rate
        expected_profit = total_expected_krw - total_cost_krw
        expected_roi = (expected_profit / total_cost_krw * 100) if total_cost_krw > 0 else 0
        
        m1, m2, m3 = st.columns(3)
        m1.metric("총 매도 예상", f"₩{total_expected_krw:,.0f}")
        m2.metric("예상 순수익", f"₩{expected_profit:+,.0f}")
        m3.metric("예상 ROI", f"{expected_roi:+.1f}%")
        
        df_plan = pd.DataFrame(exit_plan)
        fig = px.bar(df_plan, x='차수', y='예상금액', text='목표가', title=f"{selected_coin} 분할 매도 계획")
        fig.update_traces(texttemplate='₩%{text:,.0f}', textposition='outside')
        fig.update_layout(height=280, margin=dict(t=40, b=10))
        st.plotly_chart(fig, use_container_width=True, key="exit_plan_bar")

# -----------------------------------------------------------------------------
# 탭: 헤지 전략 (V7.0)
# -----------------------------------------------------------------------------
def render_hedge_tab():
    st.markdown("### 🛡️ 현물 헤지 전략 (Safe Haven)")
    st.caption("비트코인(BTC)과 **[추천 안전자산 + 내 보유 주식]** 간의 상관관계를 분석합니다.")
    
    # 내 포트폴리오에서 주식 티커 추출
    my_stocks = [p['ticker'] for p in st.session_state.portfolio if "Stock" in p.get('exchange', '')]
    
    norm_df, corr_data = get_hedge_data(user_stocks=my_stocks)
    
    if norm_df is not None and corr_data is not None:
        st.markdown("#### 📉 최근 6개월 수익률 비교")
        st.plotly_chart(px.line(norm_df, x=norm_df.index, y=norm_df.columns).update_layout(height=350, hovermode="x unified"), use_container_width=True, key="hedge_return_line")
        
        st.divider()
        st.markdown("#### 🔗 비트코인과의 상관관계 (낮을수록 좋음)")
        c1, c2 = st.columns([2, 1])
        with c1: 
            fig = px.bar(x=corr_data.values, y=corr_data.index, orientation='h', labels={'x':'상관계수', 'y':'자산'})
            fig.update_traces(marker_color=['#22c55e' if v < 0.3 else '#f59e0b' if v < 0.6 else '#ef4444' for v in corr_data.values])
            st.plotly_chart(fig.update_layout(height=250), use_container_width=True, key="hedge_corr_bar")
        with c2:
            best = corr_data.idxmin()
            st.success(f"🏆 베스트 헤지 자산:\n\n**{best}**\n\n(상관계수: {corr_data.min():.2f})")
            st.info("상관계수가 낮거나 음수(-)여야 코인 하락 시 방어 효과가 큽니다.")
            if my_stocks: 
                st.caption(f"※ 분석에 포함된 내 주식: {', '.join(my_stocks)}")
        
        with st.expander("💡 헤지 전략 가이드"):
            st.markdown("""
            - **TLT (미국채)**: 금리 하락기에 강함, 경기침체 시 안전자산
            - **GLD (금)**: 인플레이션 헤지, 달러 약세 시 상승
            - **SCHD (배당주)**: 안정적 현금흐름, 하락장에도 배당 수령
            - **VOO (S&P500)**: 시장 전체에 분산 투자
            - **내 주식(My)**: 본인이 추가한 주식의 BTC와의 상관관계 확인
            """)
    else: 
        st.warning("데이터 로딩 실패 (Yahoo Finance 연결 확인)")
        st.info("💡 주식을 추가하려면 사이드바에서 'US Stock' 또는 'KR Stock'을 선택하세요.")

# -----------------------------------------------------------------------------
# 탭 6: 리밸런싱 전략 (V7.1 개선)
# -----------------------------------------------------------------------------
def render_rebalance_tab():
    st.markdown("### ⚖️ 포트폴리오 리밸런싱 (Rebalancing)")
    st.caption("설정한 목표 비중에 맞춰 자산을 매수/매도하여 포트폴리오 균형을 맞춥니다.")

    # 1. 포트폴리오 데이터 준비
    if not st.session_state.portfolio:
        st.info("👈 사이드바에서 먼저 자산을 추가해주세요.")
        return

    data_list = []
    rate = get_usd_krw_rate()
    total_value_krw = 0

    # 현재 가치 계산
    for p in st.session_state.portfolio:
        ticker = p['ticker']
        qty = p['quantity']
        exchange = p.get('exchange', 'Binance')
        
        cur_p, curr = get_market_price(ticker, exchange)
        k_rate = rate if curr == "USD" else 1
        val_krw = qty * cur_p * k_rate
        total_value_krw += val_krw
        
        target = p.get('target_percent', 0.0)
        
        data_list.append({
            "티커": ticker,
            "거래소": exchange,
            "보유수량": qty,
            "현재가(₩)": val_krw / qty if qty > 0 else 0,
            "평가금액(₩)": val_krw,
            "현재비중(%)": 0.0,
            "목표비중(%)": target
        })

    df = pd.DataFrame(data_list)
    
    if total_value_krw > 0:
        df["현재비중(%)"] = (df["평가금액(₩)"] / total_value_krw) * 100
    else:
        st.warning("포트폴리오 평가금액이 0입니다.")
        return
    
    # -------------------------------------------------------------------------
    # 2. 목표 비중 설정 (데이터 에디터)
    # -------------------------------------------------------------------------
    st.markdown("#### 1️⃣ 목표 비중 설정")
    st.caption("아래 표에서 **'목표비중(%)'** 값을 직접 수정하세요. (합계가 100%가 되도록 설정)")

    edited_df = st.data_editor(
        df[["티커", "현재비중(%)", "목표비중(%)"]],
        column_config={
            "현재비중(%)": st.column_config.NumberColumn(format="%.1f%%", disabled=True),
            "목표비중(%)": st.column_config.NumberColumn(format="%.1f%%", min_value=0, max_value=100, step=1)
        },
        use_container_width=True,
        hide_index=True,
        key="rebalance_editor"
    )

    # 목표 비중 합계 검증
    total_target = edited_df["목표비중(%)"].sum()
    c1, c2 = st.columns(2)
    c1.metric("현재 총 자산", f"₩{total_value_krw:,.0f}")
    
    if abs(total_target - 100) > 0.1:
        c2.metric("목표 비중 합계", f"{total_target:.1f}%", delta=f"{100-total_target:.1f}% 차이", delta_color="inverse")
        st.warning(f"⚠️ 목표 비중의 합이 100%가 아닙니다. (현재: {total_target:.1f}%)")
    else:
        c2.metric("목표 비중 합계", f"{total_target:.1f}%", delta="완벽!", delta_color="normal")

    # -------------------------------------------------------------------------
    # 3. 리밸런싱 계산 및 가이드
    # -------------------------------------------------------------------------
    st.divider()
    st.markdown("#### 2️⃣ 매매 가이드 (Action Plan)")
    st.caption("💡 정확한 매매 수량을 확인하세요. 양수(+)는 매수, 음수(-)는 매도입니다.")
    
    plan_list = []
    
    for index, row in df.iterrows():
        ticker = row['티커']
        # 에디터에서 수정한 목표 비중 가져오기
        target_pct = edited_df.loc[edited_df['티커'] == ticker, "목표비중(%)"].values[0]
        
        # 세션 상태 업데이트
        st.session_state.portfolio[index]['target_percent'] = target_pct
        
        # 리밸런싱 계산
        current_val = row['평가금액(₩)']
        target_val = total_value_krw * (target_pct / 100)
        diff_val = target_val - current_val
        
        # 매매 수량 계산
        price_krw = row['현재가(₩)']
        action_qty = diff_val / price_krw if price_krw > 0 else 0
        
        if diff_val > 1000:
            action = "🔵 매수 (Buy)"
        elif diff_val < -1000:
            action = "🔴 매도 (Sell)"
        else:
            action = "✅ 유지"
            
        plan_list.append({
            "종목": ticker,
            "현재비중": f"{row['현재비중(%)']:.1f}%",
            "목표비중": f"{target_pct:.1f}%",
            "조정금액(₩)": diff_val,
            "매매수량": action_qty,
            "Action": action
        })

    plan_df = pd.DataFrame(plan_list)
    
    st.dataframe(
        plan_df.style.format({
            "조정금액(₩)": "{:+,.0f}",
            "매매수량": "{:+,.4f}"
        }),
        column_config={
            "Action": st.column_config.TextColumn("주문 유형", help="리밸런싱을 위한 행동 지침")
        },
        use_container_width=True,
        hide_index=True
    )

    # -------------------------------------------------------------------------
    # 4. Before & After 시각화
    # -------------------------------------------------------------------------
    st.divider()
    st.markdown("#### 3️⃣ 포트폴리오 변화 시뮬레이션")
    
    col_before, col_after = st.columns(2)
    
    with col_before:
        st.markdown("**Before (현재 비중)**")
        fig_cur = px.pie(df, values='평가금액(₩)', names='티커', hole=0.4)
        fig_cur.update_layout(height=250, margin=dict(t=20, b=20, l=20, r=20), showlegend=True)
        st.plotly_chart(fig_cur, use_container_width=True, key="rebalance_before_pie")
        
    with col_after:
        st.markdown("**After (목표 비중)**")
        target_data = edited_df[edited_df['목표비중(%)'] > 0].copy()
        if not target_data.empty:
            fig_target = px.pie(target_data, values='목표비중(%)', names='티커', hole=0.4)
            fig_target.update_layout(height=250, margin=dict(t=20, b=20, l=20, r=20), showlegend=True)
            st.plotly_chart(fig_target, use_container_width=True, key="rebalance_after_pie")

    # 저장 버튼
    if st.button("💾 목표 비중 저장하기", use_container_width=True):
        st.success("✅ 목표 비중이 저장되었습니다! (세션 유지)")

# -----------------------------------------------------------------------------
# 메인 실행
# -----------------------------------------------------------------------------
def main():
    # [V7.9] 모바일 친화적 로그인 화면 (메인 화면에 배치)
    if not st.session_state.get('is_logged_in', False):
        render_mobile_login()
        return  # 로그인 전에는 대시보드를 표시하지 않음
    
    gemini_key, openai_key, claude_key, grok_key, groq_key, auto = render_sidebar()
    st.markdown("<h1 style='text-align: center; color: #3b82f6;'>🐋 크립토 인사이트 V8.1</h1>", unsafe_allow_html=True)
    
    tabs = st.tabs(["📊 대시보드", "🔮 사이클/매크로", "🛡️ 헤지", "⚖️ 리밸런싱", "📉 매도 전략", "🤖 AI 위원회", "🔎 심층 분석", "📰 뉴스", "🧮 도구"])
    
    # FRED key는 세션에서 가져오거나 gemini_key 사용
    fred_key = st.session_state.get("fred_key", gemini_key)
    
    with tabs[0]: render_dashboard_tab(gemini_key)
    with tabs[1]: render_macro_tab(fred_key)
    with tabs[2]: render_hedge_tab()
    with tabs[3]: render_rebalance_tab()
    with tabs[4]: render_exit_strategy_tab()
    with tabs[5]: render_ai_council_tab(gemini_key, openai_key, claude_key, grok_key, groq_key)
    with tabs[6]: render_deep_tab()
    with tabs[7]: render_news_tab(gemini_key)
    with tabs[8]: render_tools_tab()
    
    # [V7.1] 텔레그램 알림 체크 (실시간 갱신 활성화 시)
    if auto and st.session_state.telegram.get('enabled'):
        rate = get_usd_krw_rate()
        mvrv = st.session_state.manual_data.get('mvrv_zscore', 0)
        check_and_send_alerts(st.session_state.portfolio, rate, mvrv)
    
    if auto: time.sleep(10); st.rerun()

# [V7.9] 모바일 친화적 로그인 화면
def render_mobile_login():
    """메인 화면 중앙에 로그인 UI 배치 (모바일 사용자 고려)"""
    st.markdown("""
    <style>
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 40px 20px;
            text-align: center;
        }
        .login-title {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        .login-subtitle {
            color: #64748b;
            margin-bottom: 30px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # 중앙 정렬을 위한 컬럼
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        st.markdown("<div class='login-title'>🐋</div>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center; margin-bottom:5px;'>크립토 인사이트</h1>", unsafe_allow_html=True)
        st.markdown("<p class='login-subtitle'>암호화폐 포트폴리오 & AI 분석 대시보드</p>", unsafe_allow_html=True)
        
        with st.form("main_login_form", clear_on_submit=False):
            user_id = st.text_input(
                "사용자 ID", 
                placeholder="닉네임을 입력하세요 (영문/숫자)",
                help="처음 접속 시 자동으로 계정이 생성됩니다."
            )
            
            submitted = st.form_submit_button("🚀 시작하기", use_container_width=True, type="primary")
            
            if submitted:
                if user_id and len(user_id) >= 2:
                    st.session_state.username = user_id
                    st.session_state.is_logged_in = True
                    
                    # DB에서 데이터 불러오기
                    saved_data = load_user_data(user_id)
                    if saved_data:
                        st.session_state.portfolio = saved_data.get("portfolio", [])
                        
                        # 저장된 API 키 불러오기
                        api_keys = saved_data.get("api_keys", {})
                        st.session_state.gemini_key = api_keys.get("gemini", "")
                        st.session_state.openai_key = api_keys.get("openai", "")
                        st.session_state.claude_key = api_keys.get("claude", "")
                        st.session_state.grok_key = api_keys.get("grok", "")
                        st.session_state.groq_key = api_keys.get("groq", "")  # [V8.0] Groq 오픈소스
                        st.session_state.telegram_id = saved_data.get("telegram_id", "")
                        
                        # 텔레그램 봇 토큰
                        tg_data = saved_data.get("telegram", {})
                        if 'bot_token' in tg_data:
                            st.session_state.telegram['bot_token'] = tg_data['bot_token']
                    
                    st.rerun()
                else:
                    st.error("⚠️ ID는 2자 이상 입력해주세요.")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # 하단 정보
        st.markdown("---")
        st.caption("💡 **주요 기능**: AI 투자 위원회 | 김치 프리미엄 | 목표가 알림 | 리밸런싱")
        st.caption("📱 **모바일 지원**: 사이드바 메뉴(☰)에서 자산 추가 및 설정")


if __name__ == "__main__":
    main()
