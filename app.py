"""
주간업무 관리 — Streamlit 버전

데이터는 구글 스프레드시트에 저장되고, Apps Script 웹앱이 그 앞단의 API 역할을 합니다.
이 파일은 Apps Script URL 하나와 공유 토큰만 알면 되므로 별도의 인증 설정이 없습니다.

Secrets (.streamlit/secrets.toml 또는 Streamlit Cloud 설정):
    APPS_SCRIPT_URL = "https://script.google.com/macros/s/.../exec"
    API_TOKEN       = "Code.gs 에 넣은 것과 같은 값"
"""

from __future__ import annotations

import io
import json
from datetime import date, datetime, timedelta

import pandas as pd
import requests
import streamlit as st

# ============================================================
# 기본 설정
# ============================================================

st.set_page_config(page_title="주간업무 관리", page_icon="📋", layout="wide")

CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css');

:root{
  --blue:#0054FF; --blue-deep:#0042CC; --blue-tint:#EDF3FF;
  --ink:#0B1526; --mute:#6B7684; --line:#E5E8EB; --bg:#F8F9FB;
  --moss:#0F7B4F; --moss-soft:#E4F5EC;
  --amber:#9A6B00; --amber-soft:#FDF2DC;
  --rose:#C0303C; --rose-soft:#FDECEE;
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"]{
  font-family:'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont,
              system-ui, 'Malgun Gothic', sans-serif;
  -webkit-font-smoothing:antialiased;
}
[data-testid="stAppViewContainer"]{background:var(--bg)}
.block-container{padding-top:2.4rem;padding-bottom:4rem;max-width:1320px}
h1,h2,h3,h4{letter-spacing:-.025em;color:var(--ink)}
[data-testid="stHeader"]{background:transparent}

/* ============ 사이드바 ============ */
[data-testid="stSidebar"]{
  background:linear-gradient(180deg, var(--blue) 0%, var(--blue-deep) 100%);
  border-right:none;
}
[data-testid="stSidebar"] > div:first-child{padding-top:1.5rem}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,[data-testid="stSidebar"] .stMarkdown{color:#fff}

/* Streamlit 기본 1rem 간격을 걷어내 항목을 촘촘하게 */
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.3rem}
[data-testid="stSidebar"] .stButton{margin:0}
/* 마크다운 컨테이너가 내용 높이보다 작게 잡히는 것을 막는다 */
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"]{
  height:auto;overflow:visible;
}

.side-brand{
  display:flex;align-items:center;gap:9px;color:#fff;
  font-size:15px;font-weight:700;letter-spacing:-.02em;padding-bottom:18px;
}
.side-brand i{
  width:22px;height:22px;border-radius:6px;background:#fff;color:var(--blue);
  font-style:normal;font-size:12px;font-weight:800;
  display:flex;align-items:center;justify-content:center;flex:0 0 auto;
}
.side-user{line-height:1.45;color:#fff;padding-bottom:14px;
  border-bottom:1px solid rgba(255,255,255,.18)}
.side-user b{font-size:14.5px;font-weight:700;letter-spacing:-.01em}
.side-meta{font-size:11.5px;color:rgba(255,255,255,.62) !important;line-height:1.6}

/* 그룹 라벨 — 실제 간격은 render_nav 의 인라인 스타일에서 지정 */
.navgroup{
  font-size:10.5px;font-weight:700;letter-spacing:.11em;text-transform:uppercase;
  color:rgba(255,255,255,.55) !important;
}

[data-testid="stSidebar"] .stButton>button{
  border:none;box-shadow:none;background:transparent;
  border-radius:8px;padding:7px 11px;min-height:34px;
  display:flex;justify-content:flex-start;
  font-size:13.5px;font-weight:500;letter-spacing:-.01em;
  transition:background .12s ease;
}
/* 버튼 라벨은 실제로 내부 <p> 에 들어가므로 색·정렬을 여기서 잡아준다 */
[data-testid="stSidebar"] .stButton>button p,
[data-testid="stSidebar"] .stButton>button div,
[data-testid="stSidebar"] .stButton>button span{
  color:inherit !important;text-align:left;width:100%;margin:0;
  font-size:inherit;font-weight:inherit;
}
[data-testid="stSidebar"] .stButton>button[kind="secondary"]{
  color:rgba(255,255,255,.82) !important;
}
[data-testid="stSidebar"] .stButton>button[kind="secondary"]:hover{
  background:rgba(255,255,255,.13);color:#fff !important;
}
/* 선택 상태 — 흰 알약 + 파란 글씨 */
[data-testid="stSidebar"] .stButton>button[kind="primary"],
[data-testid="stSidebar"] .stButton>button[kind="primary"] p,
[data-testid="stSidebar"] .stButton>button[kind="primary"] div,
[data-testid="stSidebar"] .stButton>button[kind="primary"] span{
  color:var(--blue) !important;
}
[data-testid="stSidebar"] .stButton>button[kind="primary"]{
  background:#fff !important;font-weight:700;box-shadow:0 1px 3px rgba(0,0,0,.10);
}
[data-testid="stSidebar"] .stButton>button[kind="primary"]:hover{
  background:#fff !important;
}
.side-foot{
  color:#fff;margin-top:20px;padding-top:14px;
  border-top:1px solid rgba(255,255,255,.18);
}
/* 하단 새로고침·로그아웃 — 윤곽선을 줘서 버튼으로 읽히게 */
[data-testid="stSidebar"] [data-testid="stColumn"] .stButton>button{
  border:1px solid rgba(255,255,255,.35);justify-content:center;
  font-size:12.5px;min-height:32px;
}
[data-testid="stSidebar"] [data-testid="stColumn"] .stButton>button p{text-align:center}

/* ============ 본문 ============ */
.pagehead{margin-bottom:20px}
.pagehead h2{font-size:22px;font-weight:800;margin:0 0 3px}
.pagehead p{font-size:13px;color:var(--mute);margin:0}

.tag{display:inline-block;padding:2px 9px;border-radius:6px;font-size:11.5px;
     font-weight:700;line-height:1.75;white-space:nowrap;letter-spacing:-.01em}
.tag-ink{background:var(--blue-tint);color:var(--blue)}
.tag-moss{background:var(--moss-soft);color:var(--moss)}
.tag-amber{background:var(--amber-soft);color:var(--amber)}
.tag-rose{background:var(--rose-soft);color:var(--rose)}
.tag-grey{background:#F2F4F6;color:var(--mute)}
.chip{display:inline-block;padding:1px 7px;border-radius:5px;background:#F2F4F6;
      font-size:11px;color:var(--mute);font-family:ui-monospace,monospace}
.pre{white-space:pre-wrap;line-height:1.68;font-size:13.5px}
.mute{color:var(--mute)}
.rblock{border-left:2px solid var(--line);padding:2px 0 2px 13px;margin-bottom:14px}

div[data-testid="stMetric"]{
  background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 18px 12px;
}
div[data-testid="stMetricLabel"] p{font-size:12.5px;color:var(--mute);font-weight:600}
div[data-testid="stMetricValue"]{font-size:25px;font-weight:800;color:var(--ink);
  letter-spacing:-.03em}

[data-testid="stVerticalBlockBorderWrapper"]{border-radius:14px}
[data-testid="stExpander"]{border:1px solid var(--line);border-radius:12px;background:#fff}
[data-testid="stExpander"] summary{font-size:13.5px;font-weight:600}
[data-testid="stDataFrame"]{border-radius:10px}

[data-testid="stMain"] .stButton>button[kind="primary"],
.main .stButton>button[kind="primary"]{
  background:var(--blue);border-color:var(--blue);border-radius:8px;font-weight:600;
}
[data-testid="stMain"] .stButton>button[kind="primary"]:hover,
.main .stButton>button[kind="primary"]:hover{
  background:var(--blue-deep);border-color:var(--blue-deep);
}
[data-testid="stMain"] .stButton>button[kind="secondary"]{
  border-radius:8px;border-color:var(--line);
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

PSTATUS = ["진행중", "준비", "보류", "완료"]
DAYS = ["월", "화", "수", "목", "금", "토", "일"]


# ============================================================
# API 연결
# ============================================================

class ApiError(Exception):
    pass


def _secret(key: str, default: str = "") -> str:
    try:
        return str(st.secrets[key])
    except Exception:
        return default


API_URL = _secret("APPS_SCRIPT_URL")
API_TOKEN = _secret("API_TOKEN")


def api(action: str, timeout: int = 45, **payload):
    """Apps Script 웹앱을 호출합니다."""
    if not API_URL:
        raise ApiError(
            "APPS_SCRIPT_URL 이 비어 있습니다. Streamlit Secrets 를 설정하세요."
        )
    try:
        res = requests.post(
            API_URL,
            json={"token": API_TOKEN, "action": action, "payload": payload},
            timeout=timeout,
        )
        res.raise_for_status()
    except requests.RequestException as e:
        raise ApiError(f"서버에 연결하지 못했습니다: {e}") from e

    try:
        body = res.json()
    except ValueError:
        raise ApiError(
            "서버 응답을 해석할 수 없습니다. 웹앱 배포의 액세스 권한이 "
            "'모든 사용자'인지 확인하세요."
        )
    if not body.get("ok"):
        raise ApiError(body.get("error") or "알 수 없는 오류가 발생했습니다.")
    return body.get("data")


@st.cache_data(ttl=180, show_spinner="스프레드시트에서 데이터를 읽는 중…")
def _snapshot(version: int):
    return api("snapshot")


def db() -> dict:
    return _snapshot(st.session_state.get("_ver", 0))


def refresh():
    """다음 렌더에서 스프레드시트를 다시 읽도록 합니다."""
    st.session_state["_ver"] = st.session_state.get("_ver", 0) + 1


def run(action: str, ok_msg: str | None = None, **payload):
    """쓰기 작업 실행 → 캐시 무효화 → 재실행. 실패 시 메시지만 띄웁니다."""
    try:
        result = api(action, **payload)
    except ApiError as e:
        st.error(str(e))
        return None
    refresh()
    if ok_msg:
        st.session_state["_toast"] = ok_msg
    st.rerun()
    return result


# ============================================================
# 날짜 · 주차 유틸 (기존 core.js 와 동일한 규칙)
# ============================================================

def wed_of(d: date) -> date:
    """그 날짜가 속한 주(월~일)의 수요일."""
    return d - timedelta(days=d.weekday()) + timedelta(days=2)


def week_info(d: date) -> dict:
    w = wed_of(d)
    y, wk, _ = w.isocalendar()
    return {
        "key": f"{y}-W{wk:02d}",
        "year": y,
        "week": wk,
        "wed": w,
        "start": w - timedelta(days=2),
        "end": w + timedelta(days=4),
    }


def cur_week() -> dict:
    return week_info(date.today())


def week_options(back: int = 16, fwd: int = 2) -> list[dict]:
    base = wed_of(date.today())
    return [week_info(base + timedelta(weeks=i)) for i in range(fwd, -back - 1, -1)]


def week_by_key(key: str) -> dict:
    for w in week_options(200, 8):
        if w["key"] == key:
            return w
    return {"key": key, "year": "", "week": "", "wed": None, "start": None, "end": None}


def week_label(w: dict) -> str:
    if not w.get("wed"):
        return w["key"]
    return f"{w['year']}년 {w['week']}주차 · {fmt_md(w['start'])}~{fmt_md(w['end'])}"


def fmt_md(d) -> str:
    if not d:
        return "-"
    if isinstance(d, str):
        d = parse_date(d)
        if not d:
            return "-"
    return f"{d.month}/{d.day}"


def parse_date(s: str):
    try:
        return date.fromisoformat(str(s)[:10])
    except Exception:
        return None


def fmt_full(s) -> str:
    d = parse_date(s) if isinstance(s, str) else s
    return d.strftime("%Y.%m.%d") if d else "-"


def fmt_ts(ms) -> str:
    try:
        return datetime.fromtimestamp(int(ms) / 1000).strftime("%m.%d %H:%M")
    except Exception:
        return "-"


def dday(due) -> int | None:
    d = parse_date(due)
    return None if not d else (d - date.today()).days


def to_int(v):
    try:
        s = str(v).strip()
        return int(float(s)) if s != "" else None
    except Exception:
        return None


# ============================================================
# 표시 헬퍼
# ============================================================

def tag(text: str, kind: str = "grey") -> str:
    return f'<span class="tag tag-{kind}">{text}</span>'


def status_tag(s: str) -> str:
    kind = {"진행중": "ink", "준비": "grey", "보류": "amber", "완료": "moss"}.get(s, "grey")
    return tag(s or "-", kind)


def dday_tag(due, status: str = "") -> str:
    if status == "완료":
        return tag("완료", "moss")
    d = dday(due)
    if d is None:
        return ""
    if d < 0:
        return tag(f"지연 {-d}일", "rose")
    if d <= 7:
        return tag(f"D-{d}", "amber")
    return tag(f"D-{d}", "grey")


def esc(s) -> str:
    return (
        str(s if s is not None else "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def nl2(s) -> str:
    return esc(s).replace("\n", "<br>")


def empty(big: str, sub: str = ""):
    st.info(f"**{big}**" + (f"\n\n{sub}" if sub else ""))


def page_head(title: str, desc: str = ""):
    st.markdown(
        f"<div class='pagehead'><h2>{esc(title)}</h2>"
        + (f"<p>{esc(desc)}</p>" if desc else "")
        + "</div>",
        unsafe_allow_html=True,
    )


# ============================================================
# 데이터 조회 헬퍼
# ============================================================

def users() -> list[dict]:
    return db()["users"]


def projects() -> list[dict]:
    return db()["projects"]


def reports() -> list[dict]:
    return db()["reports"]


def user_by_id(uid):
    return next((u for u in users() if u["id"] == uid), None)


def proj_by_id(pid):
    return next((p for p in projects() if p["id"] == pid), None)


def user_name(uid) -> str:
    u = user_by_id(uid)
    return u["name"] if u else "(삭제된 사용자)"


def user_team(uid) -> str:
    u = user_by_id(uid)
    return u["team"] if u else ""


def proj_name(pid) -> str:
    p = proj_by_id(pid)
    return p["name"] if p else "(삭제된 프로젝트)"


def proj_code(pid) -> str:
    p = proj_by_id(pid)
    return p["code"] if p else "-"


def active_projects() -> list[dict]:
    return [p for p in projects() if p["status"] not in ("완료", "보류")]


def reports_of_week(key: str) -> list[dict]:
    return [r for r in reports() if r["week"] == key]


def my_reports() -> list[dict]:
    return [r for r in reports() if r["userId"] == ME["id"]]


def is_admin() -> bool:
    return ME.get("role") == "admin"


def sort_projects(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda p: (p["status"] == "완료", p.get("dueDate") or "9999"))


# ============================================================
# CSV
# ============================================================

CSV_HEAD = [
    "주차", "기준수요일", "프로젝트코드", "프로젝트명", "완료예정일",
    "팀", "작성자", "금주진행사항", "차주진행계획", "진척률", "이슈", "최종수정",
]


def reports_df(rows: list[dict]) -> pd.DataFrame:
    data = []
    for r in rows:
        p = proj_by_id(r["projectId"]) or {}
        w = week_by_key(r["week"])
        data.append([
            r["week"],
            w["wed"].isoformat() if w.get("wed") else "",
            p.get("code", ""), p.get("name", ""), p.get("dueDate", ""),
            user_team(r["userId"]), user_name(r["userId"]),
            r["thisWeek"], r["nextWeek"],
            r.get("progress", ""), r.get("issue", ""),
            fmt_ts(r.get("updatedAt")),
        ])
    return pd.DataFrame(data, columns=CSV_HEAD)


def csv_button(rows: list[dict], filename: str, label: str = "CSV 내보내기", key: str = ""):
    if not rows:
        st.button(label, disabled=True, key=f"csvoff_{key}", help="내보낼 데이터가 없습니다.")
        return
    buf = io.StringIO()
    reports_df(rows).to_csv(buf, index=False)
    st.download_button(
        label,
        data=buf.getvalue().encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        key=f"csv_{key}",
    )


# ============================================================
# 인증 화면
# ============================================================

def auth_screens():
    st.markdown("## 주간업무 관리")
    st.caption("수요일마다, 한 장으로 정리되는 우리 팀의 한 주.")

    if not API_URL or not API_TOKEN:
        st.error(
            "연결 정보가 없습니다. Streamlit Secrets 에 `APPS_SCRIPT_URL` 과 "
            "`API_TOKEN` 을 등록한 뒤 앱을 다시 시작하세요."
        )
        st.stop()

    try:
        snap = db()
    except ApiError as e:
        st.error(str(e))
        st.caption(
            "Apps Script 에서 setup 함수를 실행했는지, 웹앱을 '모든 사용자' 접근으로 "
            "배포했는지, 토큰이 서로 같은지 확인하세요."
        )
        if st.button("다시 시도"):
            refresh()
            st.rerun()
        st.stop()

    first_run = len(snap["users"]) == 0

    if first_run:
        st.info("아직 계정이 없습니다. 첫 계정은 자동으로 **관리자** 권한을 받습니다.")
        _signup_form(admin=True)
        return

    tab_login, tab_signup = st.tabs(["로그인", "가입하기"])
    with tab_login:
        with st.form("login"):
            emp = st.text_input("사번", placeholder="예: 20240115")
            pw = st.text_input("비밀번호", type="password")
            if st.form_submit_button("로그인", type="primary", width="stretch"):
                try:
                    me = api("login", empNo=emp.strip(), pw=pw)
                except ApiError as e:
                    st.error(str(e))
                else:
                    st.session_state["me"] = me
                    refresh()
                    st.rerun()
    with tab_signup:
        _signup_form(admin=False)


def _signup_form(admin: bool):
    teams = sorted({u["team"] for u in db()["users"] if u.get("team")})
    with st.form("signup_admin" if admin else "signup"):
        c1, c2 = st.columns(2)
        name = c1.text_input("이름")
        emp = c2.text_input("사번")
        team = st.text_input("팀명", help=("기존 팀: " + ", ".join(teams)) if teams else None)
        c3, c4 = st.columns(2)
        pw = c3.text_input("비밀번호", type="password",
                           placeholder="8자 이상" if admin else "6자 이상")
        pw2 = c4.text_input("비밀번호 확인", type="password")
        label = "관리자 계정 만들기" if admin else "가입하기"
        if st.form_submit_button(label, type="primary", width="stretch"):
            if pw != pw2:
                st.error("비밀번호 확인이 일치하지 않습니다.")
                return
            try:
                me = api("signup", name=name, empNo=emp, team=team, pw=pw)
            except ApiError as e:
                st.error(str(e))
            else:
                st.session_state["me"] = me
                refresh()
                st.rerun()


# ============================================================
# 페이지 — 입력자
# ============================================================

def page_my_home():
    wk = cur_week()
    page_head("대시보드", f"{week_label(wk)} · 기준일 {fmt_md(wk['wed'])}(수)")

    mine = my_reports()
    this_wk = [r for r in mine if r["week"] == wk["key"]]
    my_pids = {r["projectId"] for r in mine}
    late = [p for p in projects()
            if p["id"] in my_pids and p["status"] != "완료" and (dday(p["dueDate"]) or 0) < 0]
    soon = [p for p in projects()
            if p["id"] in my_pids and p["status"] != "완료"
            and dday(p["dueDate"]) is not None and 0 <= dday(p["dueDate"]) <= 14]

    c = st.columns(4)
    c[0].metric("이번 주 작성", f"{len(this_wk)} 건",
                help="작성 완료" if this_wk else "아직 작성 전입니다")
    c[1].metric("담당 프로젝트", f"{len(my_pids)} 개")
    c[2].metric("누적 작성", f"{len(mine)} 건")
    c[3].metric("기한 임박·지연", f"{len(late) + len(soon)} 개",
                help=f"지연 {len(late)}건 포함" if late else "2주 이내 마감")

    st.markdown("#### 이번 주 내 작성 내역")
    if this_wk:
        for r in this_wk:
            render_my_report(r, key_prefix="home")
    else:
        empty("이번 주 작성 내역이 없습니다", "‘주간업무 입력’에서 프로젝트를 불러와 작성하세요.")

    st.markdown("#### 마감 임박 프로젝트")
    attn = sorted(late + soon, key=lambda p: dday(p["dueDate"]) or 0)
    if attn:
        st.dataframe(
            pd.DataFrame([{
                "프로젝트": p["name"], "코드": p["code"], "상태": p["status"],
                "완료 예정일": p["dueDate"],
                "잔여": f"지연 {-dday(p['dueDate'])}일" if dday(p["dueDate"]) < 0 else f"D-{dday(p['dueDate'])}",
            } for p in attn]),
            hide_index=True, width="stretch",
        )
    else:
        empty("임박한 마감이 없습니다")


def render_my_report(r: dict, key_prefix: str = ""):
    p = proj_by_id(r["projectId"]) or {}
    pg = to_int(r.get("progress"))
    title = f"{p.get('name', '(삭제됨)')} · {p.get('code', '-')}"
    if pg is not None:
        title += f" — {pg}%"
    with st.expander(title + f"   ({fmt_ts(r.get('updatedAt'))})"):
        c1, c2 = st.columns(2)
        c1.markdown(f"**금주 진행사항**<div class='pre'>{nl2(r['thisWeek'])}</div>",
                    unsafe_allow_html=True)
        c2.markdown(f"**차주 진행계획**<div class='pre'>{nl2(r['nextWeek'])}</div>",
                    unsafe_allow_html=True)
        if r.get("issue"):
            st.markdown(f"**이슈 / 요청사항**<div class='pre'>{nl2(r['issue'])}</div>",
                        unsafe_allow_html=True)
        edit_report_form(r, key=f"{key_prefix}_{r['id']}")


def edit_report_form(r: dict, key: str):
    """수정·삭제 UI. 관리자이거나 본인 글일 때만 노출합니다."""
    if not (is_admin() or r["userId"] == ME["id"]):
        return
    c1, c2 = st.columns([1, 6])
    if c1.button("수정", key=f"edit_{key}"):
        st.session_state["editing"] = r["id"]
    if c2.button("삭제", key=f"del_{key}"):
        st.session_state["deleting"] = r["id"]

    if st.session_state.get("deleting") == r["id"]:
        st.warning("이 진행사항을 삭제할까요? 되돌릴 수 없습니다.")
        d1, d2 = st.columns([1, 6])
        if d1.button("삭제 확정", key=f"delok_{key}", type="primary"):
            st.session_state.pop("deleting", None)
            run("deleteReport", "삭제되었습니다.", reportId=r["id"], userId=ME["id"])
        if d2.button("취소", key=f"delno_{key}"):
            st.session_state.pop("deleting", None)
            st.rerun()

    if st.session_state.get("editing") == r["id"]:
        with st.form(f"editform_{key}"):
            tw = st.text_area("금주 진행사항", value=r["thisWeek"], height=110)
            nw = st.text_area("차주 진행계획", value=r["nextWeek"], height=110)
            e1, e2 = st.columns(2)
            pgv = to_int(r.get("progress"))
            pg = e1.number_input("진척률 (%)", 0, 100, value=pgv if pgv is not None else 0, step=5)
            use_pg = e1.checkbox("진척률 기록", value=pgv is not None, key=f"upg_{key}")
            issue = e2.text_input("이슈 / 협조 요청", value=r.get("issue", ""))
            s1, s2 = st.columns(2)
            if s1.form_submit_button("변경사항 저장", type="primary"):
                st.session_state.pop("editing", None)
                run("updateReport", "수정되었습니다.",
                    reportId=r["id"], thisWeek=tw, nextWeek=nw,
                    progress=pg if use_pg else None, issue=issue,
                    actorId=ME["id"], actorRole=ME["role"])
            if s2.form_submit_button("취소"):
                st.session_state.pop("editing", None)
                st.rerun()


def page_my_input():
    page_head("주간업무 입력", "프로젝트별로 금주 진행사항과 차주 계획을 작성합니다. "
               "같은 프로젝트에 여러 명이 각자 입력할 수 있습니다.")

    wks = week_options(12, 1)
    keys = [w["key"] for w in wks]
    default = keys.index(cur_week()["key"]) if cur_week()["key"] in keys else 0

    c1, c2 = st.columns([3, 2])
    week_key = c1.selectbox(
        "작성 주차", keys, index=default,
        format_func=lambda k: week_label(week_by_key(k))
        + (" — 이번 주" if k == cur_week()["key"] else ""),
    )
    only_mine = c2.checkbox("내가 작성한 항목만 보기")

    projs = sort_projects(projects())
    if not projs:
        empty("등록된 프로젝트가 없습니다", "‘프로젝트 목록’ 메뉴에서 먼저 추가하세요.")
        return

    prev_key = None
    idx = keys.index(week_key)
    if idx + 1 < len(keys):
        prev_key = keys[idx + 1]

    for p in projs:
        mine = next((r for r in reports()
                     if r["week"] == week_key and r["projectId"] == p["id"]
                     and r["userId"] == ME["id"]), None)
        others = [r for r in reports()
                  if r["week"] == week_key and r["projectId"] == p["id"]
                  and r["userId"] != ME["id"]]
        if only_mine and not mine:
            continue

        badge = "작성함" if mine else "미작성"
        head = f"{'✅' if mine else '⬜'} {p['name']} · {p['code']} · {p['status']} · {badge}"
        if others:
            head += f" · 동료 {len(others)}명"

        with st.expander(head, expanded=bool(mine)):
            st.markdown(
                f"{status_tag(p['status'])} {dday_tag(p['dueDate'], p['status'])} "
                f"<span class='mute'>완료 예정 {fmt_full(p['dueDate'])}</span>",
                unsafe_allow_html=True,
            )

            prefill = ""
            if not mine and prev_key:
                prev = next((r for r in reports()
                             if r["week"] == prev_key and r["projectId"] == p["id"]
                             and r["userId"] == ME["id"]), None)
                if prev and prev.get("nextWeek"):
                    if st.checkbox("지난주 차주계획을 금주 진행사항에 채우기",
                                   key=f"prefill_{p['id']}_{week_key}"):
                        prefill = prev["nextWeek"]

            with st.form(f"input_{p['id']}_{week_key}"):
                c1, c2 = st.columns(2)
                tw = c1.text_area("금주 진행사항 *",
                                  value=mine["thisWeek"] if mine else prefill, height=140,
                                  placeholder="이번 주에 실제로 진행한 내용을 적어주세요.")
                nw = c2.text_area("차주 진행계획 *",
                                  value=mine["nextWeek"] if mine else "", height=140,
                                  placeholder="다음 주에 진행할 계획을 적어주세요.")
                c3, c4, c5 = st.columns([1, 1, 3])
                pgv = to_int(mine.get("progress")) if mine else None
                use_pg = c3.checkbox("진척률 기록", value=pgv is not None,
                                     key=f"usepg_{p['id']}_{week_key}")
                pg = c4.number_input("진척률 (%)", 0, 100,
                                     value=pgv if pgv is not None else 0, step=5)
                issue = c5.text_input("이슈 / 협조 요청",
                                      value=mine.get("issue", "") if mine else "",
                                      placeholder="없으면 비워두세요")
                if st.form_submit_button("저장", type="primary"):
                    if not tw.strip() or not nw.strip():
                        st.error("금주 진행사항과 차주 진행계획을 모두 입력하세요.")
                    else:
                        run("upsertReport", "저장되었습니다.",
                            week=week_key, projectId=p["id"], userId=ME["id"],
                            thisWeek=tw, nextWeek=nw,
                            progress=pg if use_pg else None, issue=issue)

            if mine:
                st.caption(f"최종 수정 {fmt_ts(mine.get('updatedAt'))}")
                if st.button("이 항목 삭제", key=f"delin_{p['id']}_{week_key}"):
                    run("deleteReport", "삭제되었습니다.",
                        reportId=mine["id"], userId=ME["id"])

            if others:
                st.markdown("---")
                st.markdown("**같은 프로젝트 동료 작성 내용**")
                for o in others:
                    st.markdown(
                        f"<div class='rblock'><b>{esc(user_name(o['userId']))}</b> "
                        f"<span class='mute'>{esc(user_team(o['userId']))} · "
                        f"{fmt_ts(o.get('updatedAt'))}</span><br>"
                        f"<span class='mute'>금주 ·</span> {nl2(o['thisWeek'])}<br>"
                        f"<span class='mute'>차주 ·</span> {nl2(o['nextWeek'])}</div>",
                        unsafe_allow_html=True,
                    )


def page_my_works():
    page_head("내 진행사항 관리", "내가 작성한 모든 주간업무를 한곳에서 확인하고 수정합니다.")

    rows = sorted(my_reports(), key=lambda r: (r["week"], r.get("updatedAt", "")), reverse=True)
    all_weeks = sorted({r["week"] for r in rows}, reverse=True)
    all_projs = list({r["projectId"] for r in rows})

    c1, c2, c3, c4 = st.columns([2, 2, 2, 3])
    view = c1.radio("보기", ["테이블", "프로젝트별", "주차별"], horizontal=True,
                    label_visibility="collapsed")
    fp = c2.selectbox("프로젝트", ["전체"] + all_projs,
                      format_func=lambda x: "전체 프로젝트" if x == "전체" else proj_name(x))
    fw = c3.selectbox("주차", ["전체"] + all_weeks,
                      format_func=lambda x: "전체 주차" if x == "전체" else x)
    q = c4.text_input("내용 검색", placeholder="내용 검색", label_visibility="collapsed")

    if fp != "전체":
        rows = [r for r in rows if r["projectId"] == fp]
    if fw != "전체":
        rows = [r for r in rows if r["week"] == fw]
    if q:
        ql = q.lower()
        rows = [r for r in rows
                if ql in (r["thisWeek"] + r["nextWeek"] + r.get("issue", "")
                          + proj_name(r["projectId"])).lower()]

    csv_button(rows, f"내주간업무_{ME['name']}.csv", key="myworks")
    st.caption(f"{len(rows)}건")

    if not rows:
        empty("표시할 진행사항이 없습니다", "필터를 바꾸거나 새 업무를 입력하세요.")
        return

    if view == "테이블":
        st.dataframe(reports_df(rows).drop(columns=["팀", "작성자"]),
                     hide_index=True, width="stretch")
        st.caption("내용을 고치려면 ‘프로젝트별’ 또는 ‘주차별’ 보기에서 항목을 펼치세요.")
    elif view == "프로젝트별":
        for pid in sorted({r["projectId"] for r in rows}, key=proj_name):
            p = proj_by_id(pid) or {}
            st.markdown(
                f"##### {esc(p.get('name', '(삭제됨)'))} "
                f"<span class='chip'>{esc(p.get('code', '-'))}</span> "
                f"{status_tag(p.get('status', '-'))} {dday_tag(p.get('dueDate'), p.get('status'))}",
                unsafe_allow_html=True)
            for r in [x for x in rows if x["projectId"] == pid]:
                render_my_report(r, key_prefix="mwp")
    else:
        for wk in sorted({r["week"] for r in rows}, reverse=True):
            st.markdown(f"##### {wk} · {week_label(week_by_key(wk))}")
            for r in [x for x in rows if x["week"] == wk]:
                render_my_report(r, key_prefix="mww")


def page_my_acc():
    page_head("내 정보", "계정 정보와 비밀번호를 관리합니다.")

    c1, c2 = st.columns(2)
    with c1:
        with st.form("acc"):
            st.markdown("**계정**")
            name = st.text_input("이름", value=ME["name"])
            st.text_input("사번", value=ME["empNo"], disabled=True,
                          help="사번은 변경할 수 없습니다.")
            team = st.text_input("팀명", value=ME["team"])
            st.text_input("권한", value="관리자" if is_admin() else "입력자", disabled=True)
            if st.form_submit_button("계정 정보 저장", type="primary"):
                try:
                    me = api("saveAccount", userId=ME["id"], name=name, team=team)
                except ApiError as e:
                    st.error(str(e))
                else:
                    st.session_state["me"] = me
                    refresh()
                    st.session_state["_toast"] = "계정 정보를 저장했습니다."
                    st.rerun()
    with c2:
        with st.form("pw"):
            st.markdown("**비밀번호 변경**")
            old = st.text_input("현재 비밀번호", type="password")
            new = st.text_input("새 비밀번호", type="password", placeholder="6자 이상")
            new2 = st.text_input("새 비밀번호 확인", type="password")
            if st.form_submit_button("비밀번호 변경", type="primary"):
                if new != new2:
                    st.error("새 비밀번호 확인이 일치하지 않습니다.")
                else:
                    run("changePw", "비밀번호가 변경되었습니다.",
                        userId=ME["id"], oldPw=old, newPw=new)
        st.caption("비밀번호는 개인 솔트를 붙여 SHA-256으로 해시 저장되며, "
                   "평문은 어디에도 남지 않습니다.")


# ============================================================
# 페이지 — 기준 정보
# ============================================================

@st.dialog("프로젝트 추가")
def _dialog_add_project():
    _project_form(None)


@st.dialog("프로젝트 수정")
def _dialog_edit_project(p: dict):
    _project_form(p)


def _project_form(p):
    """프로젝트 추가·수정 다이얼로그 내용. p 가 None 이면 추가 모드."""
    with st.form(f"projform_{p['id'] if p else 'new'}"):
        c1, c2 = st.columns(2)
        code = c1.text_input("프로젝트 코드 *", value=p["code"] if p else "",
                             placeholder="예: PRJ-2026-01")
        status = c2.selectbox("상태", PSTATUS,
                              index=PSTATUS.index(p["status"]) if p and p["status"] in PSTATUS else 0)
        name = st.text_input("프로젝트명 *", value=p["name"] if p else "",
                             placeholder="예: 차세대 포털 구축")
        c3, c4 = st.columns(2)
        team = c3.text_input("주관팀", value=p.get("team", "") if p else "")
        owner = c4.text_input("PM / 책임자", value=p.get("owner", "") if p else "")
        c5, c6 = st.columns(2)
        sd = c5.date_input("시작일",
                           value=parse_date(p.get("startDate")) if p and p.get("startDate") else date.today())
        dd = c6.date_input("완료 예정일 *",
                           value=parse_date(p["dueDate"]) if p and p.get("dueDate") else date.today())
        desc = st.text_area("설명", value=p.get("desc", "") if p else "", height=80,
                            placeholder="선택 입력")

        if st.form_submit_button("변경사항 저장" if p else "프로젝트 추가",
                                  type="primary", width="stretch"):
            run("saveProject",
                "프로젝트를 수정했습니다." if p else "프로젝트를 추가했습니다.",
                id=p["id"] if p else "", code=code, name=name, team=team, owner=owner,
                status=status, startDate=sd.isoformat(), dueDate=dd.isoformat(), desc=desc,
                actorId=ME["id"], actorRole=ME["role"])


def page_ref_proj():
    admin = is_admin()
    page_head("프로젝트 목록", "누구나 새 프로젝트를 등록할 수 있습니다. 기존 프로젝트 수정·삭제는 관리자만 할 수 있습니다.")

    c1, c2, c3 = st.columns([2, 3, 2])
    fs = c1.selectbox("상태", ["전체"] + PSTATUS, label_visibility="collapsed")
    q = c2.text_input("검색", placeholder="🔍 프로젝트·담당·팀 검색", label_visibility="collapsed")
    if c3.button("＋ 새 프로젝트 등록", type="primary", width="stretch"):
        _dialog_add_project()

    rows = projects()
    if fs != "전체":
        rows = [p for p in rows if p["status"] == fs]
    if q:
        ql = q.lower()
        rows = [p for p in rows
                if ql in (p["name"] + p["code"] + p.get("owner", "") + p.get("team", "")).lower()]
    rows = sort_projects(rows)

    if not rows:
        empty("표시할 프로젝트가 없습니다",
              "필터를 바꾸거나 ‘＋ 새 프로젝트 등록’으로 첫 프로젝트를 만들어 보세요.")
        return

    st.caption(f"{len(rows)} / {len(projects())}개")
    wk = cur_week()["key"]

    for p in rows:
        n_input = len([r for r in reports() if r["week"] == wk and r["projectId"] == p["id"]])
        with st.container(border=True):
            widths = [5, 2, 2, 2] + ([2] if admin else [])
            top = st.columns(widths)
            top[0].markdown(
                f"**{esc(p['name'])}** <span class='chip'>{esc(p['code'])}</span>",
                unsafe_allow_html=True)
            top[0].caption(p.get("desc") or "—")
            top[1].markdown(status_tag(p["status"]) + " " + dday_tag(p["dueDate"], p["status"]),
                            unsafe_allow_html=True)
            top[1].caption(f"완료 예정 {fmt_full(p['dueDate'])}")
            top[2].markdown(f"**{esc(p.get('team') or '-')}**")
            top[2].caption(f"PM {esc(p.get('owner') or '-')}")
            top[3].markdown(tag(f"이번 주 {n_input}명", "moss" if n_input else "grey"),
                            unsafe_allow_html=True)
            if admin:
                with top[4]:
                    bcol1, bcol2 = st.columns(2)
                    if bcol1.button("✎", key=f"editp_{p['id']}", help="수정"):
                        _dialog_edit_project(p)
                    if bcol2.button("🗑", key=f"delp_{p['id']}", help="삭제"):
                        st.session_state["delproj"] = p["id"]

        if admin and st.session_state.get("delproj") == p["id"]:
            n = len([r for r in reports() if r["projectId"] == p["id"]])
            st.warning(f"‘{p['name']}’ 프로젝트를 삭제할까요?"
                       + (f" 연결된 주간업무 {n}건도 함께 삭제됩니다." if n else ""))
            d1, d2 = st.columns([1, 6])
            if d1.button("삭제 확정", type="primary", key=f"delok_{p['id']}"):
                st.session_state.pop("delproj", None)
                run("deleteProject", "삭제되었습니다.", projectId=p["id"], actorRole=ME["role"])
            if d2.button("취소", key=f"delno_{p['id']}"):
                st.session_state.pop("delproj", None)
                st.rerun()


# ============================================================
# 페이지 — 관리자
# ============================================================

def week_picker(label: str, key: str, back: int = 20) -> str:
    wks = week_options(back, 1)
    keys = [w["key"] for w in wks]
    cur = cur_week()["key"]
    saved = st.session_state.get(key, cur)
    idx = keys.index(saved) if saved in keys else keys.index(cur)
    chosen = st.selectbox(
        label, keys, index=idx,
        format_func=lambda k: week_label(week_by_key(k)) + (" — 이번 주" if k == cur else ""),
        key=f"sel_{key}",
    )
    st.session_state[key] = chosen
    return chosen


def render_report_block(r: dict, show_user: bool = True):
    bits = []
    if show_user:
        bits.append(f"<b>{esc(user_name(r['userId']))}</b> "
                    f"<span class='mute'>{esc(user_team(r['userId']))}</span>")
    pg = to_int(r.get("progress"))
    if pg is not None:
        bits.append(tag(f"{pg}%", "ink"))
    if r.get("issue"):
        bits.append(tag("이슈", "amber"))
    bits.append(f"<span class='mute'>{fmt_ts(r.get('updatedAt'))}</span>")
    st.markdown(
        f"<div class='rblock'>{' '.join(bits)}<br>"
        f"<span class='mute'>금주 ·</span> {nl2(r['thisWeek'])}<br>"
        f"<span class='mute'>차주 ·</span> {nl2(r['nextWeek'])}"
        + (f"<br><span class='mute'>이슈 ·</span> {nl2(r['issue'])}" if r.get("issue") else "")
        + "</div>",
        unsafe_allow_html=True,
    )


def page_adm_week():
    page_head("금주 모니터링")
    c1, c2 = st.columns([3, 3])
    with c1:
        wk = week_picker("조회 주차", "aw_week")
    with c2:
        group = st.radio("묶음", ["프로젝트별", "팀별", "전체 목록"], horizontal=True,
                         label_visibility="collapsed")

    rows = reports_of_week(wk)
    submitters = {r["userId"] for r in rows}
    not_yet = [u for u in users() if u["id"] not in submitters]
    covered = {r["projectId"] for r in rows}
    act = active_projects()
    no_update = [p for p in act if p["id"] not in covered]
    issues = [r for r in rows if r.get("issue")]
    rate = round(len(submitters) / len(users()) * 100) if users() else 0

    m = st.columns(4)
    m[0].metric("제출 인원", f"{len(submitters)} / {len(users())}명", f"{rate}%")
    m[1].metric("작성 건수", f"{len(rows)} 건")
    m[2].metric("업데이트된 프로젝트", f"{len(covered)} / {len(act)}개")
    m[3].metric("이슈 제기", f"{len(issues)} 건")

    csv_button(rows, f"주간업무_{wk}.csv", key="admweek")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"##### 미제출자 {tag(f'{len(not_yet)}명', 'rose' if not_yet else 'moss')}",
                    unsafe_allow_html=True)
        if not_yet:
            st.dataframe(pd.DataFrame([{"이름": u["name"], "팀": u["team"], "사번": u["empNo"]}
                                       for u in not_yet]),
                         hide_index=True, width="stretch")
        else:
            st.success("전원 제출했습니다.")
    with c2:
        st.markdown(f"##### 업데이트 없는 진행 프로젝트 "
                    f"{tag(f'{len(no_update)}개', 'amber' if no_update else 'moss')}",
                    unsafe_allow_html=True)
        if no_update:
            st.dataframe(pd.DataFrame([{"프로젝트": p["name"], "코드": p["code"],
                                        "완료 예정일": p["dueDate"]} for p in no_update]),
                         hide_index=True, width="stretch")
        else:
            st.success("모든 진행 프로젝트가 업데이트되었습니다.")

    if issues:
        st.markdown("##### 이슈 · 협조 요청")
        st.dataframe(pd.DataFrame([{"프로젝트": proj_name(r["projectId"]),
                                    "작성자": user_name(r["userId"]),
                                    "팀": user_team(r["userId"]),
                                    "내용": r["issue"]} for r in issues]),
                     hide_index=True, width="stretch")

    if not rows:
        empty("해당 주차에 제출된 주간업무가 없습니다")
        return

    st.markdown("---")
    if group == "전체 목록":
        st.dataframe(reports_df(rows), hide_index=True, width="stretch")
    elif group == "프로젝트별":
        for pid in sorted({r["projectId"] for r in rows}, key=proj_name):
            p = proj_by_id(pid) or {}
            lst = [r for r in rows if r["projectId"] == pid]
            pgs = [to_int(r.get("progress")) for r in lst if to_int(r.get("progress")) is not None]
            avg = round(sum(pgs) / len(pgs)) if pgs else None
            st.markdown(
                f"##### {esc(p.get('name', '(삭제됨)'))} "
                f"<span class='chip'>{esc(p.get('code', '-'))}</span> "
                f"{status_tag(p.get('status', '-'))} {dday_tag(p.get('dueDate'), p.get('status'))} "
                f"{tag(f'{len(lst)}명 작성')}"
                + (f" {tag(f'평균 {avg}%', 'ink')}" if avg is not None else ""),
                unsafe_allow_html=True)
            for r in lst:
                render_report_block(r, True)
    else:
        for team in sorted({user_team(r["userId"]) or "미지정" for r in rows}):
            lst = [r for r in rows if (user_team(r["userId"]) or "미지정") == team]
            st.markdown(f"##### {esc(team)} "
                        f"<span class='mute'>{len({r['userId'] for r in lst})}명 · {len(lst)}건</span>",
                        unsafe_allow_html=True)
            for r in lst:
                st.markdown(f"**{esc(proj_name(r['projectId']))}** · {esc(user_name(r['userId']))}",
                            unsafe_allow_html=True)
                render_report_block(r, False)


def page_adm_proj():
    page_head("프로젝트별 모니터링", "프로젝트 하나를 골라 주차별·담당자별 진행 이력을 추적합니다.")

    projs = sorted(projects(), key=lambda p: p["name"])
    if not projs:
        empty("등록된 프로젝트가 없습니다", "기준 정보에서 먼저 프로젝트를 추가하세요.")
        return

    pid = st.selectbox("프로젝트", [p["id"] for p in projs],
                       format_func=lambda x: f"{proj_code(x)} · {proj_name(x)}")
    p = proj_by_id(pid)
    rows = [r for r in reports() if r["projectId"] == pid]
    weeks = sorted({r["week"] for r in rows}, reverse=True)
    people = list({r["userId"] for r in rows})
    with_pg = sorted([r for r in rows if to_int(r.get("progress")) is not None],
                     key=lambda r: r["week"], reverse=True)
    latest = to_int(with_pg[0]["progress"]) if with_pg else None

    m = st.columns(4)
    m[0].metric("상태", p["status"], f"{p.get('team', '-')} · PM {p.get('owner', '-')}")
    m[1].metric("완료 예정일", fmt_full(p["dueDate"]),
                (lambda d: "-" if d is None else (f"지연 {-d}일" if d < 0 else f"D-{d}"))(dday(p["dueDate"])))
    m[2].metric("최근 진척률", f"{latest}%" if latest is not None else "미기록")
    m[3].metric("참여 인원 / 기록 주차", f"{len(people)}명 · {len(weeks)}주", f"총 {len(rows)}건")

    csv_button(rows, f"프로젝트_{p['code']}.csv", key="admproj")

    if not rows:
        empty("이 프로젝트에 작성된 주간업무가 없습니다")
        return

    st.markdown("##### 주차 × 담당자 진척률")
    grid = []
    for wk in weeks:
        row = {"주차": wk}
        for u in people:
            r = next((x for x in rows if x["week"] == wk and x["userId"] == u), None)
            pg = to_int(r.get("progress")) if r else None
            row[user_name(u)] = ("-" if not r else (f"{pg}%" if pg is not None else "작성"))
        grid.append(row)
    st.dataframe(pd.DataFrame(grid), hide_index=True, width="stretch")

    for wk in weeks:
        st.markdown(f"##### {wk} · {week_label(week_by_key(wk))}")
        for r in [x for x in rows if x["week"] == wk]:
            render_report_block(r, True)


def page_adm_person():
    page_head("사람별 모니터링", "구성원별 제출 이력과 담당 프로젝트를 확인합니다.")

    us = sorted(users(), key=lambda u: (u.get("team", ""), u["name"]))
    uid = st.selectbox("구성원", [u["id"] for u in us],
                       format_func=lambda x: f"{user_team(x)} · {user_name(x)}")
    u = user_by_id(uid)
    rows = sorted([r for r in reports() if r["userId"] == uid],
                  key=lambda r: r["week"], reverse=True)
    weeks = {r["week"] for r in rows}
    projs = {r["projectId"] for r in rows}
    recent = [w["key"] for w in week_options(7, 0)]
    done = len([k for k in recent if any(r["week"] == k for r in rows)])

    m = st.columns(4)
    m[0].metric("구성원", u["name"],
                f"{u['team']} · {'관리자' if u['role'] == 'admin' else '입력자'}")
    m[1].metric("최근 8주 제출률", f"{round(done / len(recent) * 100)}%")
    m[2].metric("담당 프로젝트", f"{len(projs)} 개")
    m[3].metric("누적 작성", f"{len(rows)} 건", f"{len(weeks)}개 주차")

    csv_button(rows, f"개인_{u['name']}.csv", key="admperson")

    st.markdown("##### 최근 8주 제출 현황")
    st.dataframe(
        pd.DataFrame([{w: len([r for r in rows if r["week"] == w]) for w in reversed(recent)}]),
        hide_index=True, width="stretch",
    )

    if not rows:
        empty("작성 이력이 없습니다")
        return

    for wk in sorted(weeks, reverse=True):
        st.markdown(f"##### {wk} · {week_label(week_by_key(wk))}")
        for r in [x for x in rows if x["week"] == wk]:
            st.markdown(f"**{esc(proj_name(r['projectId']))}** "
                        f"<span class='chip'>{esc(proj_code(r['projectId']))}</span>",
                        unsafe_allow_html=True)
            render_report_block(r, False)


def page_adm_team():
    page_head("팀별 모니터링", "팀 단위 제출률과 작성량을 비교합니다.")
    wk = week_picker("조회 주차", "aw_week")

    rows = reports_of_week(wk)
    teams = sorted({u.get("team") or "미지정" for u in users()})
    data = []
    for t in teams:
        mem = [u for u in users() if (u.get("team") or "미지정") == t]
        mids = {u["id"] for u in mem}
        sub = [u for u in mem if any(r["userId"] == u["id"] for r in rows)]
        cnt = len([r for r in rows if r["userId"] in mids])
        iss = len([r for r in rows if r.get("issue") and r["userId"] in mids])
        data.append({
            "팀": t, "인원": len(mem), "제출": len(sub),
            "제출률": round(len(sub) / len(mem) * 100) if mem else 0,
            "작성 건수": cnt, "이슈": iss,
            "미제출자": ", ".join(u["name"] for u in mem if u not in sub) or "없음",
        })
    st.dataframe(
        pd.DataFrame(data),
        hide_index=True, width="stretch",
        column_config={"제출률": st.column_config.ProgressColumn(
            "제출률", format="%d%%", min_value=0, max_value=100)},
    )

    st.markdown("##### 프로젝트 상태 요약")
    cols = st.columns(len(PSTATUS) + 1)
    for i, s in enumerate(PSTATUS):
        cols[i].metric(s, f"{len([p for p in projects() if p['status'] == s])} 개")
    over = len([p for p in projects()
                if p["status"] != "완료" and (dday(p["dueDate"]) or 0) < 0])
    cols[-1].metric("기한 초과", f"{over} 개")


def page_adm_report():
    page_head("보고서 취합", "주차별 내용을 하나의 보고 문서로 묶습니다. 마크다운으로 내려받아 그대로 붙여넣을 수 있습니다.")

    c1, c2 = st.columns([3, 3])
    with c1:
        wk = week_picker("조회 주차", "adr_week")
    with c2:
        by = st.radio("기준", ["프로젝트", "팀", "개인"], horizontal=True,
                      label_visibility="collapsed")
    c3, c4 = st.columns(2)
    show_issue = c3.checkbox("이슈 포함", value=True)
    show_owner = c4.checkbox("작성자 표기", value=True)

    rows = reports_of_week(wk)
    if not rows:
        empty("해당 주차에 취합할 내용이 없습니다")
        return

    groups: dict[str, list[dict]] = {}
    for r in rows:
        if by == "프로젝트":
            k = proj_name(r["projectId"])
        elif by == "팀":
            k = user_team(r["userId"]) or "미지정"
        else:
            k = user_name(r["userId"])
        groups.setdefault(k, []).append(r)

    w = week_by_key(wk)
    md = [f"# 주간업무 보고", "",
          f"{week_label(w)} · 기준일 {fmt_full(w['wed'])}(수)",
          f"작성 {len(rows)}건 · 참여 {len({r['userId'] for r in rows})}명", ""]

    for name in sorted(groups):
        p = next((x for x in projects() if x["name"] == name), None) if by == "프로젝트" else None
        md.append(f"## {name}" + (f" ({p['code']})" if p else ""))
        if p:
            late = dday(p["dueDate"])
            extra = f" (지연 {-late}일)" if late is not None and late < 0 and p["status"] != "완료" else ""
            md.append(f"> 상태 {p['status']} · 주관 {p.get('team') or '-'} · "
                      f"PM {p.get('owner') or '-'} · 완료 예정 {fmt_full(p['dueDate'])}{extra}")
        for r in groups[name]:
            label = user_name(r["userId"]) if by == "프로젝트" else proj_name(r["projectId"])
            if by == "프로젝트" and not show_owner:
                label = "진행사항"
            pg = to_int(r.get("progress"))
            md.append("")
            md.append(f"### {label}" + (f" ({pg}%)" if pg is not None else ""))
            md.append(f"- **금주**: {r['thisWeek'].replace(chr(10), ' / ')}")
            md.append(f"- **차주**: {r['nextWeek'].replace(chr(10), ' / ')}")
            if show_issue and r.get("issue"):
                md.append(f"- **이슈**: {r['issue']}")
        md.append("")

    text = "\n".join(md)
    c5, c6 = st.columns([1, 1])
    c5.download_button("마크다운 내려받기", data=text.encode("utf-8"),
                       file_name=f"주간보고_{wk}.md", mime="text/markdown")
    with c6:
        csv_button(rows, f"주간보고_{wk}.csv", key="admreport")

    ai_summary_section(text, wk)

    st.markdown("---")
    st.markdown(text)
    with st.expander("마크다운 원문 (복사용)"):
        st.code(text, language="markdown")


AI_PROMPT = """당신은 팀의 주간업무 보고를 정리하는 실무 담당자입니다.
아래 원본 보고 내용을 읽고 한국어로 다음 형식에 맞춰 요약하세요.

## 이번 주 핵심
- 가장 중요한 진행사항 3~5개를 한 줄씩

## 주의가 필요한 사항
- 지연·이슈·협조 요청을 한 줄씩. 없으면 "없음"이라고만 쓰세요.

## 다음 주 초점
- 다음 주에 집중할 일 2~4개를 한 줄씩

규칙: 원본에 없는 내용을 지어내지 마세요. 담당자 이름은 필요할 때만 괄호로 덧붙이세요.
전체 400자 이내로 간결하게 쓰세요.

---- 원본 보고 ----
"""


def ai_summary_section(report_text: str, wk: str):
    """Gemini 로 임원 보고용 요약을 만듭니다."""
    st.markdown("##### AI 요약")
    c1, c2 = st.columns([1, 3])
    if c1.button("Gemini로 요약 만들기", type="primary", key=f"ai_{wk}"):
        with st.spinner("Gemini에게 요청하는 중… 10~20초 걸립니다"):
            try:
                out = api("askGemini", timeout=120, prompt=AI_PROMPT + report_text)
            except ApiError as e:
                st.session_state.pop(f"aiout_{wk}", None)
                st.error(str(e))
            else:
                st.session_state[f"aiout_{wk}"] = (out or {}).get("text", "")
    c2.caption("이 주차 보고 내용을 Gemini에 보내 핵심·이슈·다음 주 초점으로 정리합니다.")

    summary = st.session_state.get(f"aiout_{wk}")
    if summary:
        with st.container(border=True):
            st.markdown(summary)
        d1, d2 = st.columns([1, 3])
        d1.download_button("요약 내려받기", data=summary.encode("utf-8"),
                           file_name=f"주간보고_요약_{wk}.md", mime="text/markdown",
                           key=f"aidl_{wk}")
        if d2.button("요약 지우기", key=f"aiclr_{wk}"):
            st.session_state.pop(f"aiout_{wk}", None)
            st.rerun()
        st.caption("AI가 만든 초안입니다. 보고 전에 내용을 확인하고 다듬어 주세요.")


def page_adm_users():
    page_head("사용자 · 권한", "가입된 구성원의 권한을 관리합니다. 비밀번호는 해시로만 저장되어 "
               "평문 확인은 불가능하며, 필요 시 초기화할 수 있습니다.")

    wk = cur_week()["key"]
    us = sorted(users(), key=lambda u: (u["role"] != "admin", u.get("team", "")))
    st.dataframe(
        pd.DataFrame([{
            "이름": u["name"], "사번": u["empNo"], "팀명": u["team"],
            "권한": "관리자" if u["role"] == "admin" else "입력자",
            "이번 주": len([r for r in reports() if r["userId"] == u["id"] and r["week"] == wk]),
            "누적": len([r for r in reports() if r["userId"] == u["id"]]),
            "비밀번호 해시": u.get("pwPreview", "") + "…",
        } for u in us]),
        hide_index=True, width="stretch",
    )

    st.markdown("---")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("##### 권한 · 비밀번호")
        uid = st.selectbox("대상", [u["id"] for u in us],
                           format_func=lambda x: f"{user_team(x)} · {user_name(x)}",
                           key="admuser_target")
        u = user_by_id(uid)
        b1, b2 = st.columns(2)
        if b1.button("관리자로" if u["role"] != "admin" else "입력자로", width="stretch"):
            run("toggleRole", f"{u['name']} 님의 권한을 변경했습니다.", userId=uid)
        if b2.button("사용자 삭제", width="stretch"):
            st.session_state["deluser"] = uid

        with st.form("resetpw"):
            npw = st.text_input("새 비밀번호", type="password", placeholder="6자 이상")
            if st.form_submit_button("비밀번호 초기화"):
                run("resetPw", f"{u['name']} 님의 비밀번호를 초기화했습니다.",
                    userId=uid, newPw=npw)
        st.caption("설정한 비밀번호를 본인에게 전달하고, 첫 로그인 후 ‘내 정보’에서 "
                   "변경하도록 안내하세요.")

        if st.session_state.get("deluser") == uid:
            n = len([r for r in reports() if r["userId"] == uid])
            st.warning(f"{u['name']} 님을 삭제할까요?"
                       + (f" 작성한 주간업무 {n}건도 함께 삭제됩니다." if n else ""))
            d1, d2 = st.columns([1, 4])
            if d1.button("삭제 확정", type="primary"):
                st.session_state.pop("deluser", None)
                run("deleteUser", "삭제되었습니다.", userId=uid)
            if d2.button("취소", key="deluser_cancel"):
                st.session_state.pop("deluser", None)
                st.rerun()

    with c2:
        st.markdown("##### 사용자 직접 추가")
        with st.form("adduser"):
            a1, a2 = st.columns(2)
            name = a1.text_input("이름")
            emp = a2.text_input("사번")
            a3, a4 = st.columns(2)
            team = a3.text_input("팀명")
            role = a4.selectbox("권한", ["user", "admin"],
                                format_func=lambda r: "입력자" if r == "user" else "관리자")
            pw = st.text_input("초기 비밀번호", type="password", placeholder="6자 이상")
            if st.form_submit_button("추가", type="primary"):
                run("saveUser", "사용자를 추가했습니다.",
                    name=name, empNo=emp, team=team, role=role, pw=pw)


def page_adm_data():
    page_head("데이터 백업", "데이터는 구글 스프레드시트에 저장됩니다. 시트 자체가 원본이지만, "
               "주기적으로 파일로도 내려받아 보관하세요.")

    d = db()
    m = st.columns(3)
    m[0].metric("사용자", f"{len(d['users'])} 명")
    m[1].metric("프로젝트", f"{len(d['projects'])} 개")
    m[2].metric("주간업무", f"{len(d['reports'])} 건")

    st.markdown("##### 내보내기")
    c1, c2, c3 = st.columns(3)
    c1.download_button("전체 데이터 JSON",
                       data=json.dumps(d, ensure_ascii=False, indent=2).encode("utf-8"),
                       file_name=f"주간업무백업_{date.today().isoformat()}.json",
                       mime="application/json")
    with c2:
        csv_button(reports(), "전체주간업무.csv", "전체 주간업무 CSV", key="admdata")
    pbuf = io.StringIO()
    pd.DataFrame(projects()).to_csv(pbuf, index=False)
    c3.download_button("프로젝트 목록 CSV",
                       data=pbuf.getvalue().encode("utf-8-sig"),
                       file_name="프로젝트목록.csv", mime="text/csv")

    st.markdown("##### 연결 상태")
    c1, c2 = st.columns(2)
    if c1.button("Apps Script 연결 확인", width="stretch"):
        try:
            st.success(f"정상 연결됨 · {api('ping')}")
        except ApiError as e:
            st.error(str(e))
    if c2.button("Gemini 연결 확인", width="stretch"):
        with st.spinner("Gemini에 확인 요청 중…"):
            try:
                s = api("geminiStatus", timeout=120) or {}
            except ApiError as e:
                st.error(str(e))
            else:
                if s.get("ready"):
                    st.success(f"Gemini 정상 · 모델 {s.get('model')}")
                else:
                    st.error(f"Gemini 사용 불가 · {s.get('reason')}")
                    st.caption("Apps Script 프로젝트 설정 > 스크립트 속성에 "
                               "GEMINI_API_KEY 를 등록했는지 확인하세요.")
    if st.button("스프레드시트 다시 읽기"):
        refresh()
        st.rerun()

    st.markdown("##### 초기화")
    st.caption("모든 사용자·프로젝트·주간업무를 삭제합니다. "
               "삭제 후에는 관리자 계정 만들기 화면부터 다시 시작합니다.")
    confirm = st.text_input("삭제하려면 `DELETE ALL` 을 입력하세요", key="wipe_confirm")
    if st.button("전체 데이터 삭제", disabled=confirm != "DELETE ALL"):
        try:
            api("wipe")
        except ApiError as e:
            st.error(str(e))
        else:
            st.session_state.clear()
            st.rerun()


# ============================================================
# 라우팅
# ============================================================

PAGES = {
    "my-home": ("대시보드", page_my_home),
    "my-input": ("주간업무 입력", page_my_input),
    "my-works": ("내 진행사항 관리", page_my_works),
    "ref-proj": ("프로젝트 목록", page_ref_proj),
    "my-acc": ("내 정보", page_my_acc),
    "adm-week": ("금주 모니터링", page_adm_week),
    "adm-proj": ("프로젝트별 모니터링", page_adm_proj),
    "adm-person": ("사람별 모니터링", page_adm_person),
    "adm-team": ("팀별 모니터링", page_adm_team),
    "adm-report": ("보고서 취합", page_adm_report),
    "adm-users": ("사용자 · 권한", page_adm_users),
    "adm-data": ("데이터 백업", page_adm_data),
}

NAV_GROUPS_USER = [
    ("내 업무", ["my-home", "my-input", "my-works"]),
    ("기준 정보", ["ref-proj"]),
    ("계정", ["my-acc"]),
]
NAV_GROUPS_ADMIN = [
    ("모니터링", ["adm-week", "adm-proj", "adm-person", "adm-team", "adm-report"]),
    ("기준 정보", ["ref-proj", "adm-users", "adm-data"]),
    ("내 업무", ["my-input", "my-works", "my-acc"]),
]


def nav_label(key: str) -> str:
    return PAGES[key][0]


def flat_nav(groups: list) -> list:
    return [k for _, keys in groups for k in keys]


def render_nav(groups: list) -> str:
    """대분류(그룹) 아래 중분류(페이지) 버튼을 그립니다. 현재 선택된 페이지 key 를 돌려줍니다."""
    for i, (title, keys) in enumerate(groups):
        # Streamlit 이 내부 여백을 눌러버리므로 인라인 스타일로 고정합니다.
        sep = "" if i == 0 else "border-top:1px solid rgba(255,255,255,.16);margin-top:6px;"
        st.sidebar.markdown(
            f"<div class='navgroup' style='{sep}padding:22px 0 11px 3px;"
            f"line-height:15px;display:block;'>{esc(title)}</div>",
            unsafe_allow_html=True)
        for k in keys:
            active = st.session_state.get("nav_page") == k
            if st.sidebar.button(nav_label(k), key=f"navbtn_{k}",
                                 type="primary" if active else "secondary",
                                 width="stretch"):
                st.session_state["nav_page"] = k
                st.rerun()
    return st.session_state.get("nav_page")


def main():
    global ME

    if "me" not in st.session_state:
        auth_screens()
        st.stop()

    ME = st.session_state["me"]

    # 세션 중 계정이 삭제됐거나 권한이 바뀐 경우를 따라갑니다.
    try:
        fresh = user_by_id(ME["id"])
    except ApiError as e:
        st.error(str(e))
        if st.button("다시 시도"):
            refresh()
            st.rerun()
        st.stop()
        return
    if not fresh:
        st.session_state.pop("me", None)
        st.warning("계정 정보를 찾을 수 없습니다. 다시 로그인해 주세요.")
        st.stop()
    ME = st.session_state["me"] = fresh

    if msg := st.session_state.pop("_toast", None):
        st.toast(msg)

    groups = NAV_GROUPS_ADMIN if is_admin() else NAV_GROUPS_USER
    default = "adm-week" if is_admin() else "my-home"
    if st.session_state.get("nav_page") not in flat_nav(groups):
        st.session_state["nav_page"] = default

    with st.sidebar:
        st.markdown(
            "<div class='side-brand' style='padding:0 0 18px;display:flex;'>"
            "<i>주</i>주간업무 관리</div>",
            unsafe_allow_html=True)
        st.markdown(
            f"<div class='side-user' style='padding:0 0 15px;display:block;line-height:1.45;"
            f"border-bottom:1px solid rgba(255,255,255,.18);'>"
            f"<b>{esc(ME['name'])}</b>"
            f"<div class='side-meta' style='line-height:1.6;display:block;'>"
            f"{esc(ME['team'])} · {esc(ME['empNo'])} · "
            f"{'관리자' if is_admin() else '입력자'}</div></div>",
            unsafe_allow_html=True)

    page = render_nav(groups)

    with st.sidebar:
        wk = cur_week()
        mine_cnt = len([r for r in my_reports() if r["week"] == wk["key"]])
        st.markdown(
            "<div class='side-foot' style='margin-top:22px;padding:14px 0 14px;"
            "border-top:1px solid rgba(255,255,255,.18);display:block;'>"
            f"<div class='side-meta' style='line-height:1.7;display:block;'>"
            f"{esc(week_label(wk))}<br>이번 주 내 작성 <b>{mine_cnt}</b>건</div></div>",
            unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        if c1.button("새로고침", width="stretch"):
            refresh()
            st.rerun()
        if c2.button("로그아웃", width="stretch"):
            st.session_state.clear()
            st.rerun()

    PAGES[page][1]()


ME: dict = {}

if __name__ == "__main__":
    main()
