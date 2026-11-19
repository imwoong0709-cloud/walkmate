
import math
from datetime import datetime, timedelta

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(
    page_title="WalkMate | 나만의 도보 경로",
    page_icon="🚶",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Style ----------
st.markdown("""
<style>
    .stApp {
        background: #f7f9fc;
    }

    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
    }

    /* 상단 제목 배너 */
    .hero {
        padding: 2rem 2.2rem;
        border-radius: 22px;
        background: linear-gradient(120deg, #123b35, #247b68);
        color: white;
        margin-bottom: 1.5rem;
    }

    .hero h1 {
        color: white !important;
        font-size: 2.5rem;
        margin: 0;
    }

    .hero p {
        color: #d9eee8 !important;
        margin: .5rem 0 0 0;
    }

    .small-note {
        color: #64748b !important;
        font-size: .88rem;
    }

    /* 일반 글자와 항목 이름 */
    .stApp p,
    .stApp label,
    .stApp li,
    .stApp [data-testid="stWidgetLabel"],
    .stApp [data-testid="stMarkdownContainer"] {
        color: #111111;
    }

    .stApp h1,
    .stApp h2,
    .stApp h3 {
        color: #111111;
    }

    /* 숫자 및 텍스트 입력창 */
    .stApp div[data-baseweb="input"] > div,
    .stApp div[data-baseweb="textarea"] > div {
        background-color: #ffffff !important;
        border: 1.5px solid #222222 !important;
        border-radius: 7px !important;
        box-shadow: none !important;
    }

    /* 입력창 내부 글자 */
    .stApp input,
    .stApp textarea {
        background-color: #ffffff !important;
        color: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
    }

    /* 입력창 포커스 상태 */
    .stApp div[data-baseweb="input"] > div:focus-within,
    .stApp div[data-baseweb="textarea"] > div:focus-within {
        border: 2px solid #111111 !important;
        box-shadow: none !important;
    }

    /* 입력창 안내 문구 */
    .stApp input::placeholder,
    .stApp textarea::placeholder {
        color: #888888 !important;
        -webkit-text-fill-color: #888888 !important;
        opacity: 1;
    }

    /* 선택 상자 */
    .stApp div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1.5px solid #222222 !important;
        border-radius: 7px !important;
        box-shadow: none !important;
    }

    /* 선택 상자 내부 글자 */
    .stApp div[data-baseweb="select"] span {
        color: #111111 !important;
    }

    /* 선택 상자 포커스 */
    .stApp div[data-baseweb="select"] > div:focus-within {
        border: 2px solid #111111 !important;
        box-shadow: none !important;
    }

    /* 버튼 */
    .stApp button {
        border-radius: 8px;
    }

    /* 결과 카드 */
    div[data-testid="stMetric"] {
        background: white;
        padding: 1rem;
        border-radius: 14px;
        border: 1px solid #e5eaf0;
    }

</style>
""", unsafe_allow_html=True)


# ---------- Header ----------
st.markdown("""
<div class="hero">
    <h1>🚶 WalkMate</h1>
    <p>내 걸음에 맞춰 계산하는 도보 경로와 예상 도착시간</p>
</div>
""", unsafe_allow_html=True)


# ---------- Secrets ----------
api_key = st.secrets.get("KAKAO_REST_API_KEY", "")

if not api_key:
    st.warning(
        "카카오 REST API 키가 아직 설정되지 않았어요. "
        "프로젝트의 .streamlit/secrets.toml 파일에 키를 입력해 주세요."
    )

HEADERS = {
    "User-Agent": "WalkMate-Web-App/1.0"
}


# ---------- Kakao Search ----------
@st.cache_data(ttl=300, show_spinner=False)
def kakao_search(place: str, key: str):

    response = requests.get(
        "https://dapi.kakao.com/v2/local/search/keyword.json",
        params={
            "query": place,
            "size": 5
        },
        headers={
            "Authorization": f"KakaoAK {key}"
        },
        timeout=12,
    )

    if response.status_code == 401:
        raise ValueError("카카오 API 키가 올바르지 않습니다.")

    if response.status_code == 403:
        raise ValueError(
            "카카오 API 사용 권한 또는 앱 설정을 확인해 주세요."
        )

    response.raise_for_status()

    docs = response.json().get("documents", [])

    if not docs:
        raise ValueError(
            f"'{place}' 검색 결과가 없습니다. 다른 검색어를 입력해 주세요."
        )

    return docs


# ---------- Walking Route ----------
def walking_route(lat1, lon1, lat2, lon2):

    url = (
        "https://routing.openstreetmap.de/"
        f"routed-foot/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
    )

    response = requests.get(
        url,
        params={
            "overview": "full",
            "geometries": "geojson"
        },
        headers=HEADERS,
        timeout=25,
    )

    response.raise_for_status()

    data = response.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError("도보 경로를 찾지 못했습니다.")

    route = data["routes"][0]

    path = [
        (lat, lon)
        for lon, lat in route["geometry"]["coordinates"]
    ]

    if not path:
        raise ValueError("경로 좌표를 가져오지 못했습니다.")

    return route["distance"], path


# ---------- Walking Calculation ----------
def my_walk(height_cm, age, sex, distance_m):

    H = height_cm / 100

    leg = 0.53 * H

    step = H * (0.415 if sex == "남" else 0.413)

    v = math.sqrt(0.25 * 9.81 * leg)

    if age >= 60:
        v *= max(0.6, 1 - 0.006 * (age - 60))

    cadence = v / step * 60

    seconds = distance_m / v

    steps = distance_m / step

    return leg, step, v, cadence, seconds, steps


# ---------- Place Label ----------
def place_label(d):

    address = (
        d.get("road_address_name")
        or d.get("address_name")
        or "주소 정보 없음"
    )

    return f"{d['place_name']} · {address}"


# ---------- Personal Information ----------
st.markdown("### 1. 내 신체 정보")

with st.container(border=True):

    c1, c2, c3 = st.columns(3)

    with c1:
        height = st.number_input(
            "키 (cm)",
            min_value=100.0,
            max_value=230.0,
            value=175.0,
            step=1.0
        )

    with c2:
        age = st.number_input(
            "나이",
            min_value=1,
            max_value=120,
            value=20,
            step=1
        )

    with c3:
        sex = st.selectbox(
            "성별",
            ["남", "여"]
        )


# ---------- Movement Information ----------
st.markdown("### 2. 이동 정보")

with st.container(border=True):

    c1, c2 = st.columns(2)

    with c1:
        start_query = st.text_input(
            "출발지",
            placeholder="예: 부산대학교 정문"
        )

    with c2:
        end_query = st.text_input(
            "도착지",
            placeholder="예: 부산대역"
        )

    search_clicked = st.button(
        "장소 검색하기",
        type="primary",
        use_container_width=True
    )


# ---------- Search Places ----------
if search_clicked:

    if not api_key:
        st.error("먼저 카카오 REST API 키를 설정해 주세요.")

    elif not start_query.strip() or not end_query.strip():
        st.error("출발지와 도착지를 모두 입력해 주세요.")

    else:

        try:

            with st.spinner("카카오에서 장소를 검색하고 있어요..."):

                st.session_state["start_docs"] = kakao_search(
                    start_query.strip(),
                    api_key
                )

                st.session_state["end_docs"] = kakao_search(
                    end_query.strip(),
                    api_key
                )

                st.session_state.pop("route_result", None)

        except Exception as exc:
            st.error(str(exc))


# ---------- Select Places ----------
if (
    "start_docs" in st.session_state
    and "end_docs" in st.session_state
):

    st.markdown("### 3. 검색된 장소 선택")

    with st.container(border=True):

        c1, c2 = st.columns(2)

        with c1:

            start_idx = st.selectbox(
                "출발 장소 선택",
                range(len(st.session_state["start_docs"])),
                format_func=lambda i: place_label(
                    st.session_state["start_docs"][i]
                ),
                key="start_choice",
            )

        with c2:

            end_idx = st.selectbox(
                "도착 장소 선택",
                range(len(st.session_state["end_docs"])),
                format_func=lambda i: place_label(
                    st.session_state["end_docs"][i]
                ),
                key="end_choice",
            )

        calculate_clicked = st.button(
            "🚶 도보 경로 계산하기",
            type="primary",
            use_container_width=True
        )


    # ---------- Calculate Route ----------
    if calculate_clicked:

        start = st.session_state["start_docs"][start_idx]

        end = st.session_state["end_docs"][end_idx]

        try:

            with st.spinner(
                "도보 경로와 예상 시간을 계산하고 있어요..."
            ):

                lat1 = float(start["y"])
                lon1 = float(start["x"])

                lat2 = float(end["y"])
                lon2 = float(end["x"])

                distance, path = walking_route(
                    lat1,
                    lon1,
                    lat2,
                    lon2
                )

                leg, step, speed, cadence, seconds, steps = my_walk(
                    height,
                    age,
                    sex,
                    distance
                )

                arrival = datetime.now() + timedelta(
                    seconds=seconds
                )

                st.session_state["route_result"] = {
                    "start": start,
                    "end": end,
                    "lat1": lat1,
                    "lon1": lon1,
                    "lat2": lat2,
                    "lon2": lon2,
                    "distance": distance,
                    "path": path,
                    "leg": leg,
                    "step": step,
                    "speed": speed,
                    "cadence": cadence,
                    "seconds": seconds,
                    "steps": steps,
                    "arrival": arrival,
                }

        except requests.RequestException:

            st.error(
                "외부 경로 서비스에 연결하지 못했습니다. "
                "잠시 후 다시 시도해 주세요."
            )

        except Exception as exc:

            st.error(f"계산 중 문제가 발생했습니다: {exc}")


# ---------- Results ----------
result = st.session_state.get("route_result")

if result:

    st.markdown("---")

    st.markdown("### 4. 나의 도보 경로")

    st.write(
        f"**{result['start']['place_name']}** "
        f"→ **{result['end']['place_name']}**"
    )

    total_seconds = round(result["seconds"])

    hours, remainder = divmod(total_seconds, 3600)

    minutes, seconds = divmod(remainder, 60)

    duration = (
        f"{hours}시간 {minutes}분"
        if hours
        else f"{minutes}분"
    )

    if hours == 0 and minutes == 0:
        duration = f"{seconds}초"


    # ---------- Main Metrics ----------
    m1, m2, m3 = st.columns(3)

    m1.metric(
        "이동 거리",
        f"{result['distance']/1000:.2f} km"
    )

    m2.metric(
        "예상 소요 시간",
        duration
    )

    m3.metric(
        "예상 걸음 수",
        f"{result['steps']:,.0f}보"
    )


    st.success(
        f"예상 도착 시각 · {result['arrival'].strftime('%H:%M')}"
    )


    # ---------- Additional Metrics ----------
    a, b, c = st.columns(3)

    a.metric(
        "예상 보행속도",
        f"{result['speed']*3.6:.2f} km/h"
    )

    b.metric(
        "예상 보폭",
        f"{result['step']*100:.1f} cm"
    )

    c.metric(
        "분당 걸음 수",
        f"{result['cadence']:.0f}보"
    )


    # ---------- Map ----------
    route_map = folium.Map(
        location=result["path"][len(result["path"]) // 2],
        zoom_start=15
    )

    folium.PolyLine(
        result["path"],
        color="#247bda",
        weight=6,
        opacity=0.85
    ).add_to(route_map)

    folium.Marker(
        [result["lat1"], result["lon1"]],
        tooltip=f"출발: {result['start']['place_name']}",
        icon=folium.Icon(
            color="green",
            icon="play"
        ),
    ).add_to(route_map)

    folium.Marker(
        [result["lat2"], result["lon2"]],
        tooltip=f"도착: {result['end']['place_name']}",
        icon=folium.Icon(
            color="red",
            icon="flag"
        ),
    ).add_to(route_map)

    route_map.fit_bounds(result["path"])

    st_folium(
        route_map,
        height=520,
        use_container_width=True,
        returned_objects=[]
    )


    # ---------- Notice ----------
    st.caption(
        "※ 이동 시간과 걸음 수는 입력한 신체 정보 및 "
        "기존 노트북의 보행 추정식에 따른 값입니다. "
        "실제 보행 속도, 신호 대기, 경사, 혼잡도 등에 따라 "
        "달라질 수 있습니다. "
        "경로는 OpenStreetMap 기반 외부 도보 경로 서비스에서 가져옵니다."
    )


# ---------- Footer ----------
st.markdown("---")

st.markdown(
    '<p class="small-note">'
    'WalkMate · 개인별 보행 특성을 반영한 도보 경로 예측 서비스'
    '</p>',
    unsafe_allow_html=True,
)
