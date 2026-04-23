from __future__ import annotations

from html import escape

import streamlit as st

from budget_dashboard import (
    AMOUNT_UNITS,
    FUND_SOURCES,
    apply_base_filters,
    apply_query,
    build_outline_payload,
    compute_summary,
    format_amount_by_unit,
    format_budget_type_label,
    format_stat_item_label,
    get_filter_options,
    get_org_department_lines,
    get_org_name,
    parse_budget_upload,
    preview_uploaded_table,
    sort_budget_items,
    strip_basis_prefix,
)


PAGE_SIZE = 100
TAB_OPTIONS = {
    "summary": "요약",
    "funds": "재원 분석",
    "execution": "집행 현황",
}
UNIT_OPTIONS = {
    "thousand": "천원",
    "million": "백만원",
    "hundredMillion": "억원",
}


def segmented_widget(label: str, options: list[str], format_func):
    if hasattr(st, "segmented_control"):
        return st.segmented_control(
            label,
            options=options,
            format_func=format_func,
            selection_mode="single",
            default=options[0],
            label_visibility="collapsed",
        )
    return st.radio(
        label,
        options=options,
        format_func=format_func,
        horizontal=True,
        label_visibility="collapsed",
    )


def inject_global_css() -> None:
    st.markdown(
        """
        <style>
          .stApp {
            background: linear-gradient(180deg, #F6F3EE 0%, #F8FAFC 36%, #EEF2F7 100%);
          }
          [data-testid="stHeader"] {
            background: rgba(248, 250, 252, 0.84);
          }
          [data-testid="stSidebar"] {
            background: transparent;
            border-right: none;
          }
          [data-testid="stSidebar"] > div:first-child {
            background: transparent;
          }
          [data-testid="stSidebarUserContent"] {
            padding-top: 1.2rem;
          }
          .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2rem;
            max-width: 1560px;
          }
          .panel {
            background: rgba(255, 255, 255, 0.94);
            border: 1px solid #E5E7EB;
            border-radius: 24px;
            box-shadow: 0 20px 48px rgba(15, 23, 42, 0.06);
            padding: 1.15rem 1.2rem;
          }
          .hero {
            display: flex;
            gap: 14px;
            align-items: center;
            margin-bottom: 1rem;
          }
          .hero-badge {
            width: 48px;
            height: 48px;
            border-radius: 16px;
            display: grid;
            place-items: center;
            background: linear-gradient(135deg, #E6F0FF 0%, #DDF8F0 100%);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.7);
            font-size: 22px;
          }
          .hero-title {
            font-size: 1.1rem;
            font-weight: 800;
            color: #111827;
            letter-spacing: -0.02em;
          }
          .hero-subtitle {
            font-size: 0.86rem;
            color: #6B7280;
            margin-top: 2px;
          }
          .section-title {
            font-size: 1rem;
            font-weight: 800;
            color: #111827;
          }
          .section-subtitle {
            font-size: 0.86rem;
            color: #6B7280;
            margin-top: 4px;
            margin-bottom: 14px;
          }
          .chip-wrap {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
          }
          .chip {
            display: inline-flex;
            align-items: center;
            padding: 7px 12px;
            border-radius: 999px;
            background: #EEF2FF;
            color: #4338CA;
            font-size: 0.78rem;
            font-weight: 700;
          }
          .metric-value {
            font-size: 2rem;
            font-weight: 900;
            color: #111827;
            letter-spacing: -0.04em;
          }
          .metric-sub {
            margin-top: 8px;
            font-size: 0.9rem;
            color: #6B7280;
          }
          .mini-card {
            padding: 16px 18px;
            border-radius: 18px;
            background: #F8FAFC;
            border: 1px solid #E5E7EB;
            margin-bottom: 10px;
          }
          .mini-label {
            font-size: 0.8rem;
            font-weight: 800;
          }
          .mini-value {
            margin-top: 8px;
            font-size: 1rem;
            font-weight: 800;
            color: #111827;
          }
          .mini-sub {
            margin-top: 6px;
            font-size: 0.8rem;
            color: #6B7280;
          }
          .field-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            padding: 12px 14px;
            border-radius: 16px;
            background: #F8FAFC;
            border: 1px solid #E5E7EB;
            margin-bottom: 10px;
          }
          .field-name {
            font-size: 0.86rem;
            font-weight: 700;
            color: #374151;
          }
          .field-value {
            font-size: 0.82rem;
            font-weight: 800;
            color: #111827;
          }
          .empty-box {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 2.6rem 0;
            text-align: center;
          }
          .empty-box.compact {
            padding: 1.2rem 0;
          }
          .empty-emoji {
            font-size: 34px;
          }
          .empty-title {
            font-size: 1rem;
            font-weight: 800;
            color: #4B5563;
          }
          .empty-desc {
            font-size: 0.84rem;
            color: #9CA3AF;
            max-width: 420px;
          }
          .fund-row {
            position: relative;
            overflow: hidden;
            border-radius: 18px;
            border: 1px solid #E5E7EB;
            background: #FFFFFF;
            margin-bottom: 10px;
          }
          .fund-fill {
            position: absolute;
            left: 8px;
            top: 8px;
            bottom: 8px;
            border-radius: 12px;
          }
          .fund-content {
            position: relative;
            display: grid;
            grid-template-columns: minmax(120px, 1.2fr) minmax(150px, 1fr) 84px;
            gap: 12px;
            align-items: center;
            padding: 14px 16px;
          }
          .upload-note {
            padding: 16px 18px;
            border-radius: 18px;
            font-size: 0.9rem;
            line-height: 1.7;
          }
          .upload-note.ok {
            background: #ECFDF5;
            border: 1px solid #A7F3D0;
            color: #047857;
          }
          .upload-note.warn {
            background: #FFF7ED;
            border: 1px solid #FED7AA;
            color: #9A3412;
          }
          .outline-top {
            font-size: 0.95rem;
            font-weight: 800;
            color: #111827;
          }
          .outline-meta {
            margin-top: 4px;
            font-size: 0.82rem;
            color: #6B7280;
          }
          .outline-line {
            padding: 10px 12px;
            border-radius: 14px;
            background: #FFFFFF;
            border: 1px solid #DBEAFE;
            margin-top: 10px;
          }
          .outline-line.child {
            background: #F1F5F9;
            border-color: #E5E7EB;
          }
          .outline-flex {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: flex-start;
          }
          .outline-basis {
            color: #111827;
            line-height: 1.6;
            font-weight: 700;
          }
          .outline-amount {
            white-space: nowrap;
            font-size: 0.79rem;
            font-weight: 800;
            color: #0F172A;
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 999px;
            padding: 4px 10px;
          }
          .sidebar-caption {
            font-size: 0.78rem;
            font-weight: 800;
            color: #4B5563;
            letter-spacing: 0.08em;
            margin-bottom: 2px;
          }
          .sidebar-title {
            font-size: 1.05rem;
            font-weight: 800;
            color: #111827;
            margin-bottom: 8px;
          }
          .sidebar-help {
            font-size: 0.86rem;
            color: #6B7280;
          }
          div[data-testid="stSidebar"] .stButton button,
          .stButton button {
            border-radius: 999px;
            border: 1px solid #D7DEE8;
            background: #FFFFFF;
            color: #374151;
            font-weight: 700;
          }
          .stTextInput input, .stSelectbox select, .stFileUploader section {
            border-radius: 16px !important;
          }
          #MainMenu, footer {
            visibility: hidden;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_budget_data(file_name: str, file_bytes: bytes):
    return parse_budget_upload(file_name, file_bytes)


@st.cache_data(show_spinner=False)
def load_preview_data(file_name: str, file_bytes: bytes):
    return preview_uploaded_table(file_name, file_bytes)


def reset_filters(include_query: bool = True) -> None:
    keys = [
        "budget_type_filter",
        "org_name_filter",
        "department_filter",
        "account_name_filter",
        "detail_project_filter",
        "stat_item_filter",
    ]
    if include_query:
        keys.append("query_input")
    for key in keys:
        st.session_state[key] = ""
    st.session_state["display_count"] = PAGE_SIZE
    st.rerun()


def file_meta_html(file_name: str, file_size: int, rows: int) -> str:
    return f"""
    <div class="upload-note ok">
      선택된 파일: <strong>{escape(file_name)}</strong><br/>
      파일 크기: {file_size / 1024 / 1024:.2f} MB<br/>
      읽은 예산 행 수: {rows:,}건
    </div>
    """


def empty_state(title: str, description: str, compact: bool = False) -> None:
    st.markdown(
        f"""
        <div class="empty-box {'compact' if compact else ''}">
          <div class="empty-emoji">{'🗂️' if compact else '📁'}</div>
          <div class="empty-title">{escape(title)}</div>
          <div class="empty-desc">{escape(description)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_active_chips(filters: dict[str, str]) -> None:
    labels: list[str] = []
    if filters["query"]:
        labels.append(f"검색어 · {filters['query']}")
    if filters["budgetType"]:
        labels.append(f"예산구분 · {format_budget_type_label(filters['budgetType'])}")
    if filters["orgName"]:
        labels.append(f"실국명 · {filters['orgName']}")
    if filters["department"]:
        labels.append(f"부서명 · {filters['department']}")
    if filters["accountName"]:
        labels.append(f"회계명 · {filters['accountName']}")
    if filters["detailProject"]:
        labels.append(f"세부사업명 · {filters['detailProject']}")
    if filters["statItemName"]:
        labels.append(f"통계목명 · {filters['statItemName']}")
    if not labels:
        return
    html = "".join(f'<span class="chip">{escape(label)}</span>' for label in labels)
    st.markdown(f'<div class="chip-wrap">{html}</div>', unsafe_allow_html=True)


def render_summary_cards(summary: dict, amount_unit: str, filters: dict[str, str]) -> None:
    fund_entries = [entry for entry in summary["fundTotals"] if entry["amount"] > 0]
    field_highlights = summary["fieldTotals"][:8]
    col1, col2 = st.columns([1.45, 0.95], gap="large")

    with col1:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">검색된 편성액 합계</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">재원별 금액은 요청하신 순서로 표시하고, 금액이 없는 항목은 생략했습니다.</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="metric-value">{escape(format_amount_by_unit(summary['totalAmount'], amount_unit))}</div>
            <div class="metric-sub">검색 결과 {summary['totalCount']:,}건</div>
            """,
            unsafe_allow_html=True,
        )
        render_active_chips(filters)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if fund_entries:
            fund_columns = st.columns(3)
            for index, entry in enumerate(fund_entries):
                with fund_columns[index % 3]:
                    ratio = (entry["amount"] / summary["totalAmount"] * 100) if summary["totalAmount"] else 0
                    st.markdown(
                        f"""
                        <div class="mini-card" style="border-color:{entry['accent']}22">
                          <div class="mini-label" style="color:{entry['accent']}">{escape(entry['label'])}</div>
                          <div class="mini-value">{escape(format_amount_by_unit(entry['amount'], amount_unit))}</div>
                          <div class="mini-sub">전체 대비 {ratio:.1f}%</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            empty_state("표시할 재원 금액이 없습니다", "현재 조건에서는 0보다 큰 재원 항목이 없습니다.", compact=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">분야별 합계</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">상위 분야를 빠르게 훑어볼 수 있게 유지했습니다.</div>', unsafe_allow_html=True)
        if field_highlights:
            for entry in field_highlights:
                st.markdown(
                    f"""
                    <div class="field-row">
                      <span class="field-name">{escape(entry['field_name'])}</span>
                      <span class="field-value">{escape(format_amount_by_unit(entry['total_amount'], amount_unit))}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            empty_state("분야별 합계가 없습니다", "검색 조건을 조금 넓혀보세요.", compact=True)
        st.markdown("</div>", unsafe_allow_html=True)


def render_outline(entries: list[dict], amount_unit: str) -> None:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">편성내역</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">검색 결과에 해당하는 편성내역을 순서대로 확인할 수 있습니다.</div>', unsafe_allow_html=True)
    if not entries:
        empty_state("표시할 편성내역이 없습니다", "검색 조건에 맞는 항목이 없습니다.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    for entry in entries:
        primary, secondary = get_org_department_lines(entry["department"])
        title = f"{format_budget_type_label(entry['budget_type'])} | {primary} | {entry['detail_project'] or '-'} | {format_amount_by_unit(entry['budget_amount'], amount_unit)}"
        with st.expander(title, expanded=False):
            st.markdown(
                f"""
                <div class="outline-top">{escape(entry['account_name'] or '-')}</div>
                <div class="outline-meta">{escape(secondary or entry['department'] or '-')} · {escape(format_stat_item_label(entry['stat_item_code'], entry['stat_item_name']))}</div>
                """,
                unsafe_allow_html=True,
            )
            render_outline_line(entry["calc_basis"], entry["calc_formula"], entry["budget_amount"], amount_unit, "parent")
            for child in entry["children"]:
                render_outline_line(child["calc_basis"], child["calc_formula"], child["budget_amount"], amount_unit, child["level"])
    st.markdown("</div>", unsafe_allow_html=True)


def render_outline_line(basis: str, formula: str, budget_amount: float, amount_unit: str, level: str) -> None:
    marker = "○" if level == "parent" else "-" if level == "child" else "˚" if level == "grandchild" else "•"
    klass = "outline-line" if level == "parent" else "outline-line child"
    formula_html = f'<div style="margin-top:6px;padding-left:20px;font-size:0.82rem;color:#475569;line-height:1.6">{escape(formula)}</div>' if formula else ""
    st.markdown(
        f"""
        <div class="{klass}">
          <div class="outline-flex">
            <div class="outline-basis">{escape(marker)} {escape(strip_basis_prefix(basis))}</div>
            <div class="outline-amount">{escape(format_amount_by_unit(budget_amount, amount_unit))}</div>
          </div>
          {formula_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_fund_cards(summary: dict, amount_unit: str) -> None:
    entries = [entry for entry in summary["fundTotals"] if entry["amount"] > 0]
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">재원 분석</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">재원별 금액은 국고보조금부터 기타까지 요청하신 순서로 배치했습니다.</div>', unsafe_allow_html=True)
    if not entries:
        empty_state("표시할 재원 금액이 없습니다", "현재 필터 조건에 해당하는 재원 정보가 없습니다.")
    else:
        columns = st.columns(3)
        for index, entry in enumerate(entries):
            with columns[index % 3]:
                ratio = (entry["amount"] / summary["totalAmount"] * 100) if summary["totalAmount"] else 0
                st.markdown(
                    f"""
                    <div class="mini-card" style="background:#FFFFFF;border-color:{entry['accent']}33;box-shadow:0 10px 30px rgba(15,23,42,0.04);">
                      <div class="mini-label" style="color:{entry['accent']}">{escape(entry['label'])}</div>
                      <div class="mini-value">{escape(format_amount_by_unit(entry['amount'], amount_unit))}</div>
                      <div class="mini-sub">전체 대비 {ratio:.1f}%</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    st.markdown("</div>", unsafe_allow_html=True)


def render_fund_composition(summary: dict, amount_unit: str) -> None:
    entries = [entry for entry in summary["fundTotals"] if entry["amount"] > 0]
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">재원별 구성표</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">각 행 배경에 비율 막대를 넣어 수치를 더 직관적으로 볼 수 있게 했습니다.</div>', unsafe_allow_html=True)
    if not entries:
        empty_state("재원 분석 결과가 없습니다", "검색 조건을 바꾸면 재원별 구성표가 나타납니다.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    for entry in entries:
        ratio = (entry["amount"] / summary["totalAmount"] * 100) if summary["totalAmount"] else 0
        fill_width = max(ratio, 6) if ratio > 0 else 0
        st.markdown(
            f"""
            <div class="fund-row">
              <div class="fund-fill" style="width:{fill_width:.1f}%; background:linear-gradient(90deg, {entry['accent']}33 0%, {entry['accent']}12 100%);"></div>
              <div class="fund-content">
                <div style="font-size:0.86rem;font-weight:800;color:{entry['accent']}">{escape(entry['label'])}</div>
                <div style="text-align:right;font-size:0.88rem;font-weight:800;color:#111827;white-space:nowrap">{escape(format_amount_by_unit(entry['amount'], amount_unit))}</div>
                <div style="text-align:right;font-size:0.82rem;color:#475569;font-weight:700">{ratio:.1f}%</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_execution_panel(execution_file, preview_df) -> None:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">집행 현황</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">사이드바에서 올린 집행현황 파일을 여기서 바로 확인할 수 있습니다.</div>', unsafe_allow_html=True)
    if execution_file:
        st.markdown(
            f"""
            <div class="upload-note ok">
              선택된 파일: <strong>{escape(execution_file.name)}</strong><br/>
              파일 크기: {execution_file.size / 1024 / 1024:.2f} MB
            </div>
            """,
            unsafe_allow_html=True,
        )
        if preview_df is not None:
            st.dataframe(preview_df, use_container_width=True, hide_index=True)
    else:
        st.markdown(
            """
            <div class="upload-note warn">
              아직 업로드된 집행 파일이 없습니다. 사이드바의 집행현황 파일 업로드 영역에서 `.xlsx`, `.xlsm`, `.csv`
              파일을 올리면 예산 데이터와 함께 검토할 수 있습니다.
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_detail_table(items_df, amount_unit: str, total_count: int) -> None:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">상세 편성 내역</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">산출근거는 산출근거명으로 표기하고, 상세 표에서도 요청하신 필터 순서를 유지합니다.</div>', unsafe_allow_html=True)
    if items_df.empty:
        empty_state("상세 편성 내역이 없습니다", "다른 검색어나 필터를 시도해보세요.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    display_count = st.session_state.get("display_count", PAGE_SIZE)
    visible_df = items_df.head(display_count).copy()
    visible_df["예산구분"] = visible_df["budget_type"].apply(format_budget_type_label)
    visible_df["실국명"] = visible_df["department"].apply(get_org_name)
    visible_df["부서명"] = visible_df["department"].replace("", "-")
    visible_df["회계명"] = visible_df["account_name"].replace("", "-")
    visible_df["세부사업명"] = visible_df["detail_project"].replace("", "-")
    visible_df["통계목명"] = visible_df.apply(
        lambda row: format_stat_item_label(row["stat_item_code"], row["stat_item_name"]),
        axis=1,
    )
    visible_df["산출근거명"] = visible_df["calc_basis"].replace("", "-")
    visible_df["예산액"] = visible_df["budget_amount"].apply(lambda value: format_amount_by_unit(value, amount_unit))
    st.dataframe(
        visible_df[["예산구분", "실국명", "부서명", "회계명", "세부사업명", "통계목명", "산출근거명", "예산액"]],
        use_container_width=True,
        hide_index=True,
    )
    if len(items_df) > display_count:
        if st.button(f"더 보기 ({total_count:,}건 중 {display_count:,}건 표시)", key="load_more_button"):
            st.session_state["display_count"] = display_count + PAGE_SIZE
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="예산 현황 대시보드", page_icon="📊", layout="wide")
    inject_global_css()

    if "display_count" not in st.session_state:
        st.session_state["display_count"] = PAGE_SIZE

    st.sidebar.markdown('<div class="panel">', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sidebar-caption">왼쪽 필터</div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sidebar-title">조건 선택</div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sidebar-help">업로드한 예산 파일 안에서 예산구분부터 통계목명까지 기존 순서대로 탐색합니다.</div>', unsafe_allow_html=True)

    budget_file = st.sidebar.file_uploader(
        "예산 파일 업로드",
        type=["xlsx", "xlsm", "csv"],
        help="원본 예산서(.xlsx) 또는 정규화된 budgets.csv를 업로드할 수 있습니다.",
        key="budget_file_uploader",
    )
    execution_file = st.sidebar.file_uploader(
        "집행현황 파일 업로드",
        type=["xlsx", "xlsm", "csv"],
        help="집행 파일은 예산 파일과 별도로 올릴 수 있습니다.",
        key="execution_file_uploader",
    )
    preview_df = None
    if execution_file:
        try:
            preview_df = load_preview_data(execution_file.name, execution_file.getvalue())
        except Exception as error:  # noqa: BLE001
            st.sidebar.markdown(
                f'<div class="upload-note warn">집행 파일 미리보기를 만들지 못했습니다.<br/>{escape(str(error))}</div>',
                unsafe_allow_html=True,
            )

    if not budget_file:
        if execution_file:
            st.sidebar.markdown(
                f"""
                <div class="upload-note ok">
                  집행 파일 준비 완료: <strong>{escape(execution_file.name)}</strong><br/>
                  파일 크기: {execution_file.size / 1024 / 1024:.2f} MB
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.sidebar.markdown("</div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="panel">
              <div class="hero">
                <div class="hero-badge">📊</div>
                <div>
                  <div class="hero-title">예산 현황 대시보드</div>
                  <div class="hero-subtitle">기존 Project BD 화면 구조를 유지하면서 업로드형 Streamlit 버전으로 옮긴 페이지입니다.</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        empty_state("예산 파일을 업로드해 주세요", "좌측 사이드바에서 `.xlsx`, `.xlsm`, `.csv` 파일을 업로드하면 요약, 재원 분석, 집행 현황 탭이 활성화됩니다.")
        render_execution_panel(execution_file, preview_df)
        return

    budget_bytes = budget_file.getvalue()
    try:
        budget_df = load_budget_data(budget_file.name, budget_bytes)
    except Exception as error:  # noqa: BLE001
        st.sidebar.markdown(
            f'<div class="upload-note warn">예산 파일을 읽지 못했습니다.<br/>{escape(str(error))}</div>',
            unsafe_allow_html=True,
        )
        st.sidebar.markdown("</div>", unsafe_allow_html=True)
        st.error("업로드한 예산 파일 형식을 다시 확인해 주세요.")
        return

    st.sidebar.markdown(file_meta_html(budget_file.name, budget_file.size, len(budget_df)), unsafe_allow_html=True)

    query = st.session_state.get("query_input", "")
    base_filters = {
        "query": query,
        "budgetType": st.session_state.get("budget_type_filter", ""),
        "orgName": st.session_state.get("org_name_filter", ""),
        "department": st.session_state.get("department_filter", ""),
        "accountName": st.session_state.get("account_name_filter", ""),
        "detailProject": st.session_state.get("detail_project_filter", ""),
        "statItemName": st.session_state.get("stat_item_filter", ""),
    }
    options = get_filter_options(budget_df, base_filters)

    if base_filters["budgetType"] not in options["uniqueBudgetTypes"]:
        st.session_state["budget_type_filter"] = ""
        base_filters["budgetType"] = ""
    if base_filters["orgName"] not in options["uniqueOrgs"]:
        st.session_state["org_name_filter"] = ""
        base_filters["orgName"] = ""
    visible_departments = options["uniqueDepartments"] if not base_filters["orgName"] else [
        department for department in options["uniqueDepartments"] if get_org_name(department) == base_filters["orgName"]
    ]
    if base_filters["department"] not in visible_departments:
        st.session_state["department_filter"] = ""
        base_filters["department"] = ""
    if base_filters["accountName"] not in options["uniqueAccounts"]:
        st.session_state["account_name_filter"] = ""
        base_filters["accountName"] = ""
    if base_filters["detailProject"] not in options["uniqueDetailProjects"]:
        st.session_state["detail_project_filter"] = ""
        base_filters["detailProject"] = ""
    if base_filters["statItemName"] not in options["uniqueStatItems"]:
        st.session_state["stat_item_filter"] = ""
        base_filters["statItemName"] = ""

    st.sidebar.selectbox(
        "예산구분",
        options=[""] + options["uniqueBudgetTypes"],
        index=([""] + options["uniqueBudgetTypes"]).index(base_filters["budgetType"]),
        format_func=lambda value: "전체 예산구분" if value == "" else format_budget_type_label(value),
        key="budget_type_filter",
    )
    st.sidebar.selectbox(
        "실국명",
        options=[""] + options["uniqueOrgs"],
        index=([""] + options["uniqueOrgs"]).index(base_filters["orgName"]),
        format_func=lambda value: "전체 실국명" if value == "" else value,
        key="org_name_filter",
    )
    st.sidebar.selectbox(
        "부서명",
        options=[""] + visible_departments,
        index=([""] + visible_departments).index(base_filters["department"]),
        format_func=lambda value: ("해당 실국 전체 부서" if base_filters["orgName"] else "전체 부서명") if value == "" else value,
        key="department_filter",
    )
    st.sidebar.selectbox(
        "회계명",
        options=[""] + options["uniqueAccounts"],
        index=([""] + options["uniqueAccounts"]).index(base_filters["accountName"]),
        format_func=lambda value: "전체 회계명" if value == "" else value,
        key="account_name_filter",
    )
    st.sidebar.selectbox(
        "세부사업명",
        options=[""] + options["uniqueDetailProjects"],
        index=([""] + options["uniqueDetailProjects"]).index(base_filters["detailProject"]),
        format_func=lambda value: "전체 세부사업명" if value == "" else value,
        key="detail_project_filter",
    )
    st.sidebar.selectbox(
        "통계목명",
        options=[""] + options["uniqueStatItems"],
        index=([""] + options["uniqueStatItems"]).index(base_filters["statItemName"]),
        format_func=lambda value: "전체 통계목" if value == "" else value,
        key="stat_item_filter",
    )
    active_sidebar_filter_count = len([value for key, value in base_filters.items() if key != "query" and value])
    st.sidebar.caption(f"활성 필터 {active_sidebar_filter_count}개")
    st.sidebar.button("필터 초기화", on_click=reset_filters, kwargs={"include_query": False}, use_container_width=True)
    st.sidebar.markdown("</div>", unsafe_allow_html=True)

    active_filters = {
        "query": st.session_state.get("query_input", ""),
        "budgetType": st.session_state.get("budget_type_filter", ""),
        "orgName": st.session_state.get("org_name_filter", ""),
        "department": st.session_state.get("department_filter", ""),
        "accountName": st.session_state.get("account_name_filter", ""),
        "detailProject": st.session_state.get("detail_project_filter", ""),
        "statItemName": st.session_state.get("stat_item_filter", ""),
    }
    signature = tuple(active_filters.items())
    if st.session_state.get("filter_signature") != signature:
        st.session_state["filter_signature"] = signature
        st.session_state["display_count"] = PAGE_SIZE

    filtered_base_df = apply_base_filters(budget_df, active_filters)
    filtered_items_df = sort_budget_items(apply_query(filtered_base_df, active_filters["query"]))
    summary = compute_summary(filtered_base_df, active_filters["query"])
    outline_entries = build_outline_payload(filtered_base_df, active_filters["query"])

    st.markdown(
        """
        <div class="panel">
          <div class="hero">
            <div class="hero-badge">📊</div>
            <div>
              <div class="hero-title">예산 현황 대시보드</div>
              <div class="hero-subtitle">검색 결과를 요약, 재원 분석, 상세 편성 기준으로 확인합니다.</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.text_input(
        "검색",
        key="query_input",
        placeholder="세부사업명, 부서명, 산출근거명 검색... (띄어쓰기 무시)",
        label_visibility="collapsed",
    )

    top_col1, top_col2, top_col3 = st.columns([1.1, 1.1, 0.8])
    with top_col1:
        selected_tab = segmented_widget("탭", list(TAB_OPTIONS.keys()), lambda value: TAB_OPTIONS[value])
    with top_col2:
        selected_unit = segmented_widget("금액 단위", list(UNIT_OPTIONS.keys()), lambda value: UNIT_OPTIONS[value])
    with top_col3:
        active_filter_count = len([value for value in active_filters.values() if value])
        st.button(
            f"전체 초기화 ({active_filter_count})",
            disabled=active_filter_count == 0,
            on_click=reset_filters,
            use_container_width=True,
        )

    if selected_tab == "summary":
        render_summary_cards(summary, selected_unit, active_filters)
        render_outline(outline_entries, selected_unit)
        return

    if selected_tab == "funds":
        render_fund_cards(summary, selected_unit)
        render_fund_composition(summary, selected_unit)
        return

    render_execution_panel(execution_file, preview_df)
    render_detail_table(filtered_items_df, selected_unit, len(filtered_items_df))


if __name__ == "__main__":
    main()
