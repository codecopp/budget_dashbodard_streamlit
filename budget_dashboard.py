from __future__ import annotations

from dataclasses import dataclass
from functools import cmp_to_key
from io import BytesIO
from typing import Any

import openpyxl
import pandas as pd


AmountUnit = str
FundKey = str

OUT_HEADERS = [
    "fiscal_year",
    "budget_type",
    "field_name",
    "sector_name",
    "committee_name",
    "policy_project",
    "unit_project",
    "account_code",
    "account_name",
    "detail_project",
    "subsidy_type",
    "department",
    "budget_item_code",
    "budget_item_name",
    "stat_item_code",
    "stat_item_name",
    "mandatory_type",
    "calc_basis",
    "calc_formula",
    "budget_amount",
    "original_amount",
    "comparison_change",
    "national_subsidy",
    "local_special_subsidy",
    "fund_subsidy",
    "special_grant",
    "province_subsidy",
    "special_adj_grant",
    "city_budget",
    "local_bond",
    "other",
]

TEXT_COLUMNS = [
    "fiscal_year",
    "budget_type",
    "field_name",
    "sector_name",
    "committee_name",
    "policy_project",
    "unit_project",
    "account_code",
    "account_name",
    "detail_project",
    "subsidy_type",
    "department",
    "budget_item_code",
    "budget_item_name",
    "stat_item_code",
    "stat_item_name",
    "mandatory_type",
    "calc_basis",
    "calc_formula",
]

NUMERIC_COLUMNS = [
    "budget_amount",
    "original_amount",
    "comparison_change",
    "national_subsidy",
    "local_special_subsidy",
    "fund_subsidy",
    "special_grant",
    "province_subsidy",
    "special_adj_grant",
    "city_budget",
    "local_bond",
    "other",
]

HEADER_ALIASES = {
    "fiscal_year": ("회계연도",),
    "budget_type": ("예산구분",),
    "field_name": ("분야명",),
    "sector_name": ("부문명",),
    "committee_name": ("위원회명",),
    "policy_project": ("정책사업명",),
    "unit_project": ("단위사업명",),
    "account_code": ("회계코드",),
    "account_name": ("회계구분명", "회계명"),
    "detail_project": ("세부사업명",),
    "subsidy_type": ("자체보조구분명",),
    "department": ("부서명",),
    "budget_item_code": ("편성목코드", "편성목"),
    "budget_item_name": ("편성목명",),
    "stat_item_code": ("통계목코드", "통계목"),
    "stat_item_name": ("통계목명",),
    "mandatory_type": ("조정의무재량구분", "의무/재량구분"),
    "calc_basis": ("조정산출근거", "산출근거명"),
    "calc_formula": ("조정산출근거식", "산출근거식"),
    "budget_amount": ("경정조정액", "예산액"),
    "comparison_change": ("조정액(증감)", "비교증감"),
    "national_subsidy": ("조정증감|국고보조금", "국고보조금"),
    "local_special_subsidy": ("조정증감|지특보조금", "지특보조금"),
    "fund_subsidy": ("조정증감|기금보조금", "기금보조금"),
    "special_grant": ("조정증감|특별교부세", "특별교부세"),
    "province_subsidy": ("조정증감|도비보조금", "도비보조금"),
    "special_adj_grant": ("조정증감|특별조정교부금", "특별조정교부금"),
    "city_budget": ("조정증감|시비", "시비"),
    "local_bond": ("조정증감|지방채", "지방채"),
    "other": ("조정증감|기타", "기타"),
}

OPTIONAL_HEADER_ALIASES = {
    "unknown_fund": ("조정증감|.", "."),
}

ORG_ORDER_SOURCE = [
    "정책기획관",
    "대변인",
    "감사담당관",
    "자치행정국",
    "일자리경제국",
    "복지국",
    "환경국",
    "도시안전주택국",
    "해양수산국",
    "관광컨벤션도시추진본부",
    "의회사무국",
    "남구보건소",
    "북구보건소",
    "농업기술센터",
    "건설교통사업본부",
    "맑은물사업본부",
    "푸른도시사업단",
    "평생학습원",
    "서울사무소",
    "수산물품질관리센터",
    "남구",
    "북구",
]

DEPT_ORDER_SOURCE = {
    "정책기획관": ["정책기획관"],
    "대변인": ["대변인"],
    "감사담당관": ["감사담당관"],
    "자치행정국": ["총무새마을과", "예산법무과", "재정관리과", "체육산업과", "문화예술과", "정보통신과"],
    "일자리경제국": ["투자기업지원과", "바이오미래산업과", "배터리첨단산업과", "디지털융합산업과", "수소에너지산업과", "경제노동정책과", "일자리청년과"],
    "복지국": ["복지정책과", "노인장애인복지과", "여성가족과", "교육청소년과"],
    "환경국": ["환경정책과", "기후대기과", "자원순환과", "식품산업과"],
    "도시안전주택국": ["도시계획과", "도시재생과", "안전총괄과", "지진방재사업과", "건축디자인과", "공동주택과"],
    "해양수산국": ["수산정책과", "어촌활력과", "해양산업과", "항만과"],
    "관광컨벤션도시추진본부": ["관광산업과", "마이스산업과", "컨벤션건립과"],
    "의회사무국": ["의회사무국"],
    "남구보건소": ["남구보건소 보건정책과", "남구보건소 건강관리과"],
    "북구보건소": ["북구보건소 보건정책과", "북구보건소 건강관리과"],
    "농업기술센터": ["농업정책과", "농촌활력과", "축산과", "기술보급과", "농식품유통과"],
    "건설교통사업본부": ["건설과", "도로시설과", "교통지원과", "대중교통과", "차량등록과"],
    "맑은물사업본부": ["상하수도행정과", "상수도과", "정수과", "하수도과", "하수재생과"],
    "푸른도시사업단": ["그린웨이추진과", "녹지과", "공원과", "생태하천과"],
    "평생학습원": ["평생교육과", "시립도서관", "시립미술관"],
    "서울사무소": ["서울사무소"],
    "수산물품질관리센터": ["수산물품질관리센터"],
    "남구": ["남구자치행정과", "남구민원토지정보과", "남구복지환경위생과", "남구세무과", "남구산업과", "남구건설교통과", "남구건축허가과", "구룡포읍", "연일읍", "오천읍", "대송면", "동해면", "장기면", "호미곶면", "상대동", "해도동", "송도동", "청림동", "제철동", "효곡동", "대이동"],
    "북구": ["북구자치행정과", "북구민원토지정보과", "북구복지환경위생과", "북구세무과", "북구산업과", "북구건설교통과", "북구건축허가과", "흥해읍", "신광면", "청하면", "송라면", "기계면", "죽장면", "기북면", "중앙동", "양학동", "죽도동", "용흥동", "우창동", "두호동", "장량동", "환여동"],
}

FUND_SOURCES = [
    {"key": "national_subsidy", "label": "국고보조금", "accent": "#24926A"},
    {"key": "local_special_subsidy", "label": "지특보조금", "accent": "#0F766E"},
    {"key": "fund_subsidy", "label": "기금보조금", "accent": "#0B8A83"},
    {"key": "special_grant", "label": "특별교부세", "accent": "#2563EB"},
    {"key": "province_subsidy", "label": "도비보조금", "accent": "#7C3AED"},
    {"key": "special_adj_grant", "label": "특별조정교부금", "accent": "#C2410C"},
    {"key": "city_budget", "label": "시비", "accent": "#D97706"},
    {"key": "local_bond", "label": "지방채", "accent": "#6D28D9"},
    {"key": "other", "label": "기타", "accent": "#475569"},
]

AMOUNT_UNITS = {
    "thousand": {"label": "천원", "divisor": 1},
    "million": {"label": "백만원", "divisor": 1000},
    "hundredMillion": {"label": "억원", "divisor": 100000},
}

SEARCH_COLUMNS = [
    "field_name",
    "budget_type",
    "department",
    "account_name",
    "detail_project",
    "policy_project",
    "unit_project",
    "budget_item_name",
    "stat_item_code",
    "stat_item_name",
    "calc_basis",
    "calc_formula",
]

ORG_INDEX_MAP = {name: index for index, name in enumerate(ORG_ORDER_SOURCE)}
DEPARTMENT_TO_ORG_MAP = {
    department: org_name
    for org_name, departments in DEPT_ORDER_SOURCE.items()
    for department in departments
}
DEPARTMENT_INDEX_MAP: dict[str, int] = {}
for departments in DEPT_ORDER_SOURCE.values():
    for index, department in enumerate(departments):
        DEPARTMENT_INDEX_MAP.setdefault(department, index)


@dataclass(frozen=True)
class SearchMatcher:
    compact_query: str
    tokens: list[str]


def safe_num(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def build_column_map(header_row_1: tuple[Any, ...], header_row_2: tuple[Any, ...]) -> dict[str, int]:
    column_map: dict[str, int] = {}
    for index, (first, second) in enumerate(zip(header_row_1, header_row_2)):
        left = normalize_text(first)
        right = normalize_text(second)
        combined = f"{left}|{right}" if left and right else left or right
        if combined:
            column_map[combined] = index
        if left:
            column_map.setdefault(left, index)
        if right:
            column_map.setdefault(right, index)
    return column_map


def get_col(column_map: dict[str, int], field_name: str) -> int:
    for alias in HEADER_ALIASES[field_name]:
        if alias in column_map:
            return column_map[alias]
    raise ValueError(f"{field_name} 컬럼을 찾지 못했습니다: {HEADER_ALIASES[field_name]}")


def get_optional_col(column_map: dict[str, int], aliases: tuple[str, ...]) -> int | None:
    for alias in aliases:
        if alias in column_map:
            return column_map[alias]
    return None


def get_text(row: tuple[Any, ...], index: int | None) -> str:
    if index is None or index >= len(row):
        return ""
    return normalize_text(row[index])


def get_numeric(row: tuple[Any, ...], index: int | None) -> float:
    if index is None or index >= len(row):
        return 0.0
    return safe_num(row[index])


def build_record(row: tuple[Any, ...], columns: dict[str, int], optional_columns: dict[str, int | None]) -> list[Any]:
    budget_amount = get_numeric(row, columns["budget_amount"])
    comparison_change = get_numeric(row, columns["comparison_change"])
    budget_type = get_text(row, columns["budget_type"])
    other_amount = get_numeric(row, columns["other"]) + get_numeric(row, optional_columns["unknown_fund"])

    if budget_type == "본예산":
        original_amount = 0.0
        if comparison_change == 0:
            comparison_change = budget_amount
    else:
        original_amount = max(budget_amount - comparison_change, 0.0)

    return [
        get_text(row, columns["fiscal_year"]),
        budget_type,
        get_text(row, columns["field_name"]),
        get_text(row, columns["sector_name"]),
        get_text(row, columns["committee_name"]),
        get_text(row, columns["policy_project"]),
        get_text(row, columns["unit_project"]),
        get_text(row, columns["account_code"]),
        get_text(row, columns["account_name"]),
        get_text(row, columns["detail_project"]),
        get_text(row, columns["subsidy_type"]),
        get_text(row, columns["department"]),
        get_text(row, columns["budget_item_code"]),
        get_text(row, columns["budget_item_name"]),
        get_text(row, columns["stat_item_code"]),
        get_text(row, columns["stat_item_name"]),
        get_text(row, columns["mandatory_type"]),
        get_text(row, columns["calc_basis"]),
        get_text(row, columns["calc_formula"]),
        budget_amount,
        original_amount,
        comparison_change,
        get_numeric(row, columns["national_subsidy"]),
        get_numeric(row, columns["local_special_subsidy"]),
        get_numeric(row, columns["fund_subsidy"]),
        get_numeric(row, columns["special_grant"]),
        get_numeric(row, columns["province_subsidy"]),
        get_numeric(row, columns["special_adj_grant"]),
        get_numeric(row, columns["city_budget"]),
        get_numeric(row, columns["local_bond"]),
        other_amount,
    ]


def normalize_budget_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    if not set(OUT_HEADERS).issubset(normalized.columns):
        missing = [column for column in OUT_HEADERS if column not in normalized.columns]
        raise ValueError("정규화된 예산 데이터 컬럼이 부족합니다: " + ", ".join(missing))

    normalized = normalized[OUT_HEADERS].copy()
    for column in TEXT_COLUMNS:
        normalized[column] = normalized[column].fillna("").astype(str).str.strip()
    for column in NUMERIC_COLUMNS:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce").fillna(0.0)
    normalized.insert(0, "id", range(1, len(normalized) + 1))
    normalized["org_name"] = normalized["department"].map(get_org_name)
    normalized["stat_item_display"] = normalized.apply(
        lambda row: format_stat_item_label(row.get("stat_item_code"), row.get("stat_item_name")),
        axis=1,
    )
    normalized["search_text"] = normalized.apply(build_search_text, axis=1)
    normalized["calc_basis_level"] = normalized["calc_basis"].apply(get_calc_basis_level)
    return normalized


def parse_excel_budget_bytes(file_bytes: bytes) -> pd.DataFrame:
    workbook = openpyxl.load_workbook(BytesIO(file_bytes), data_only=True, read_only=True)
    worksheet = workbook.active
    row_iterator = worksheet.iter_rows(values_only=True)

    try:
        first_row = next(row_iterator)
    except StopIteration as exc:
        raise ValueError("업로드된 엑셀 파일이 비어 있습니다.") from exc

    if set(OUT_HEADERS).issubset({normalize_text(value) for value in first_row}):
        df = pd.read_excel(BytesIO(file_bytes))
        return normalize_budget_dataframe(df)

    try:
        second_row = next(row_iterator)
    except StopIteration as exc:
        raise ValueError("예산 원본 엑셀의 헤더가 올바르지 않습니다.") from exc

    column_map = build_column_map(first_row, second_row)
    columns = {field: get_col(column_map, field) for field in HEADER_ALIASES}
    optional_columns = {
        field: get_optional_col(column_map, aliases)
        for field, aliases in OPTIONAL_HEADER_ALIASES.items()
    }

    records: list[list[Any]] = []
    for row in row_iterator:
        if not any(row):
            continue
        records.append(build_record(row, columns, optional_columns))

    if not records:
        raise ValueError("엑셀에서 읽은 예산 행이 없습니다.")

    return normalize_budget_dataframe(pd.DataFrame(records, columns=OUT_HEADERS))


def parse_budget_upload(file_name: str, file_bytes: bytes) -> pd.DataFrame:
    lower_name = file_name.lower()
    if lower_name.endswith(".csv"):
        df = pd.read_csv(BytesIO(file_bytes))
        return normalize_budget_dataframe(df)
    if lower_name.endswith(".xlsx") or lower_name.endswith(".xlsm"):
        return parse_excel_budget_bytes(file_bytes)
    if lower_name.endswith(".xls"):
        raise ValueError("`.xls` 형식은 현재 지원하지 않습니다. 가능하면 `.xlsx` 또는 정규화된 `.csv`로 저장해 업로드해 주세요.")
    raise ValueError("지원하지 않는 파일 형식입니다. `.xlsx`, `.xlsm`, `.csv` 파일을 업로드해 주세요.")


def preview_uploaded_table(file_name: str, file_bytes: bytes, rows: int = 10) -> pd.DataFrame:
    lower_name = file_name.lower()
    if lower_name.endswith(".csv"):
        return pd.read_csv(BytesIO(file_bytes), nrows=rows)
    if lower_name.endswith(".xlsx") or lower_name.endswith(".xlsm"):
        return pd.read_excel(BytesIO(file_bytes), nrows=rows)
    raise ValueError("미리보기는 `.xlsx`, `.xlsm`, `.csv`만 지원합니다.")


def format_budget_type_label(value: str | None) -> str:
    raw = normalize_text(value)
    if not raw:
        return "-"
    if raw.startswith("추경"):
        digits = "".join(char for char in raw if char.isdigit())
        return f"추경 {digits}차" if digits else raw
    if raw.startswith("기금계획변경"):
        digits = "".join(char for char in raw if char.isdigit())
        return f"기금계획변경 {digits}차" if digits else raw
    return raw


def get_budget_type_order(value: str | None) -> tuple[int, int, str]:
    raw = normalize_text(value)
    if raw == "본예산":
        return (0, 0, raw)
    if raw.startswith("추경"):
        digits = "".join(char for char in raw if char.isdigit())
        return (1, int(digits or 0), raw)
    if raw.startswith("기금계획변경"):
        digits = "".join(char for char in raw if char.isdigit())
        return (2, int(digits or 0), raw)
    return (3, 10**9, raw)


def compare_budget_types(left: str | None, right: str | None) -> int:
    left_key = get_budget_type_order(left)
    right_key = get_budget_type_order(right)
    return (left_key > right_key) - (left_key < right_key)


def get_org_name(department: str | None) -> str:
    raw = normalize_text(department)
    if not raw:
        return ""
    return DEPARTMENT_TO_ORG_MAP.get(raw, raw)


def compare_org_names(left: str | None, right: str | None) -> int:
    left_raw = normalize_text(left)
    right_raw = normalize_text(right)
    left_index = ORG_INDEX_MAP.get(left_raw, 10**9)
    right_index = ORG_INDEX_MAP.get(right_raw, 10**9)
    left_key = (left_index, left_raw)
    right_key = (right_index, right_raw)
    return (left_key > right_key) - (left_key < right_key)


def compare_departments(left: str | None, right: str | None) -> int:
    left_raw = normalize_text(left)
    right_raw = normalize_text(right)
    org_comparison = compare_org_names(get_org_name(left_raw), get_org_name(right_raw))
    if org_comparison != 0:
        return org_comparison
    left_key = (DEPARTMENT_INDEX_MAP.get(left_raw, 10**9), left_raw)
    right_key = (DEPARTMENT_INDEX_MAP.get(right_raw, 10**9), right_raw)
    return (left_key > right_key) - (left_key < right_key)


def format_stat_item_label(code: str | None, name: str | None) -> str:
    code_value = normalize_text(code)
    name_value = normalize_text(name)
    if code_value and name_value:
        return f"{code_value} {name_value}"
    return code_value or name_value or "-"


def sort_unique(values: list[str], comparator) -> list[str]:
    cleaned = [value for value in values if normalize_text(value)]
    unique_values = list(dict.fromkeys(cleaned))
    return sorted(unique_values, key=cmp_to_key(comparator))


def sort_budget_types(values: list[str]) -> list[str]:
    return sort_unique(values, compare_budget_types)


def sort_org_names(values: list[str]) -> list[str]:
    return sort_unique(values, compare_org_names)


def sort_departments(values: list[str]) -> list[str]:
    return sort_unique(values, compare_departments)


def sort_text_values(values: list[str]) -> list[str]:
    cleaned = [value for value in values if normalize_text(value)]
    return sorted(dict.fromkeys(cleaned), key=lambda value: value)


def get_departments_for_org(org_name: str | None) -> list[str]:
    raw = normalize_text(org_name)
    if not raw:
        return []
    if raw in DEPT_ORDER_SOURCE:
        return list(DEPT_ORDER_SOURCE[raw])
    return []


def format_amount_by_unit(amount: float | int | None, unit: AmountUnit, with_unit: bool = True, zero_label: str | None = None) -> str:
    numeric_amount = float(amount or 0)
    config = AMOUNT_UNITS[unit]
    if numeric_amount == 0:
        return zero_label or ("0" if not with_unit else f"0 {config['label']}")

    scaled_value = numeric_amount / config["divisor"]
    if unit == "thousand":
        decimals = 0
    elif unit == "million":
        decimals = 0 if abs(scaled_value) >= 100 else 1
    else:
        if abs(scaled_value) >= 100:
            decimals = 0
        elif abs(scaled_value) >= 10:
            decimals = 1
        else:
            decimals = 2
    formatted = f"{scaled_value:,.{decimals}f}"
    return formatted if not with_unit else f"{formatted} {config['label']}"


def normalize_search_value(value: str | None) -> str:
    raw = normalize_text(value).lower()
    return "".join(char for char in raw if char.isalnum() or ("\u3131" <= char <= "\u318E") or ("\uAC00" <= char <= "\uD7A3"))


def build_search_matcher(query: str) -> SearchMatcher:
    sanitized = query.replace("%", " ").replace(",", " ").replace("(", " ").replace(")", " ").strip()
    compact_query = normalize_search_value(sanitized)
    tokens = [token for token in {normalize_search_value(part) for part in sanitized.split()} if token]
    return SearchMatcher(compact_query=compact_query, tokens=tokens)


def has_search_query(matcher: SearchMatcher) -> bool:
    return bool(matcher.compact_query or matcher.tokens)


def build_search_text(row: pd.Series) -> str:
    parts = [normalize_text(row.get(column)) for column in SEARCH_COLUMNS]
    return normalize_search_value(" ".join(part for part in parts if part))


def matches_search_text(search_text: str, matcher: SearchMatcher) -> bool:
    if not has_search_query(matcher):
        return True
    if not search_text:
        return False
    if matcher.compact_query and matcher.compact_query in search_text:
        return True
    return all(token in search_text for token in matcher.tokens)


def apply_query(df: pd.DataFrame, query: str) -> pd.DataFrame:
    matcher = build_search_matcher(query)
    if not has_search_query(matcher):
        return df.copy()
    return df[df["search_text"].apply(lambda value: matches_search_text(value, matcher))].copy()


def apply_base_filters(df: pd.DataFrame, filters: dict[str, str]) -> pd.DataFrame:
    filtered = df.copy()
    if filters.get("budgetType"):
        filtered = filtered[filtered["budget_type"] == filters["budgetType"]]
    if filters.get("orgName"):
        departments = get_departments_for_org(filters["orgName"])
        if departments:
            filtered = filtered[filtered["department"].isin(departments)]
        else:
            filtered = filtered[filtered["org_name"] == filters["orgName"]]
    if filters.get("department"):
        filtered = filtered[filtered["department"] == filters["department"]]
    if filters.get("accountName"):
        filtered = filtered[filtered["account_name"] == filters["accountName"]]
    if filters.get("detailProject"):
        filtered = filtered[filtered["detail_project"] == filters["detailProject"]]
    if filters.get("statItemName"):
        value = filters["statItemName"]
        if " " in value:
            code, name = value.split(" ", 1)
            filtered = filtered[(filtered["stat_item_code"] == code) & (filtered["stat_item_name"] == name)]
        else:
            filtered = filtered[filtered["stat_item_name"] == value]
    return filtered.copy()


def get_filter_options(df: pd.DataFrame, filters: dict[str, str]) -> dict[str, list[str]]:
    keys = ["budgetType", "orgName", "department", "accountName", "detailProject", "statItemName"]
    rows_by_key: dict[str, pd.DataFrame] = {}
    for key in keys:
        next_filters = dict(filters)
        next_filters[key] = ""
        subset = apply_query(apply_base_filters(df, next_filters), filters.get("query", ""))
        rows_by_key[key] = subset

    return {
        "uniqueBudgetTypes": sort_budget_types(rows_by_key["budgetType"]["budget_type"].dropna().astype(str).tolist()),
        "uniqueOrgs": sort_org_names(rows_by_key["orgName"]["org_name"].dropna().astype(str).tolist()),
        "uniqueDepartments": sort_departments(rows_by_key["department"]["department"].dropna().astype(str).tolist()),
        "uniqueAccounts": sort_text_values(rows_by_key["accountName"]["account_name"].dropna().astype(str).tolist()),
        "uniqueDetailProjects": sort_text_values(rows_by_key["detailProject"]["detail_project"].dropna().astype(str).tolist()),
        "uniqueStatItems": sort_text_values(rows_by_key["statItemName"]["stat_item_display"].dropna().astype(str).tolist()),
    }


def get_calc_basis_level(value: str | None) -> str:
    raw = normalize_text(value)
    if not raw:
        return ""
    first_char = raw[0]
    if first_char == "○":
        return "parent"
    if first_char == "-":
        return "child"
    if first_char == "˚":
        return "grandchild"
    return "item"


def get_fund_amount(row: pd.Series | dict[str, Any]) -> float:
    return sum(float(row.get(source["key"], 0) or 0) for source in FUND_SOURCES)


def get_rows_for_summary_aggregation(rows: pd.DataFrame, query: str) -> list[dict[str, Any]]:
    records = rows.to_dict("records")
    matcher = build_search_matcher(query)
    use_matcher = has_search_query(matcher)
    aggregated_rows: list[dict[str, Any]] = []
    pending_parent: dict[str, Any] | None = None
    pending_children: list[dict[str, Any]] = []

    def row_matches(row: dict[str, Any]) -> bool:
        return matches_search_text(row.get("search_text", ""), matcher)

    def flush_pending() -> None:
        nonlocal pending_parent, pending_children
        if pending_parent:
            matched_parent = (not use_matcher) or row_matches(pending_parent)
            matched_children = [row for row in pending_children if row_matches(row)] if use_matcher else pending_children
            if matched_children:
                aggregated_rows.extend(matched_children)
            elif matched_parent:
                aggregated_rows.append(pending_parent)
        elif pending_children:
            matched_children = [row for row in pending_children if row_matches(row)] if use_matcher else pending_children
            aggregated_rows.extend(matched_children)
        pending_parent = None
        pending_children = []

    for row in records:
        level = row.get("calc_basis_level") or get_calc_basis_level(row.get("calc_basis"))
        if level == "parent":
            flush_pending()
            pending_parent = row
            continue
        if pending_parent:
            pending_children.append(row)
            continue
        pending_children.append(row)

    flush_pending()
    return aggregated_rows


def compute_summary(rows: pd.DataFrame, query: str) -> dict[str, Any]:
    matched_rows = apply_query(rows, query)
    summary_rows = get_rows_for_summary_aggregation(rows, query)
    field_totals: dict[str, float] = {}
    fund_totals = {source["key"]: 0.0 for source in FUND_SOURCES}
    total_amount = 0.0

    for row in summary_rows:
        fund_amount = get_fund_amount(row)
        total_amount += fund_amount
        field_name = normalize_text(row.get("field_name"))
        if field_name:
            field_totals[field_name] = field_totals.get(field_name, 0.0) + fund_amount
        for source in FUND_SOURCES:
            fund_totals[source["key"]] += float(row.get(source["key"], 0) or 0)

    return {
        "totalAmount": total_amount,
        "totalCount": len(matched_rows),
        "fieldTotals": [
            {"field_name": field_name, "total_amount": amount}
            for field_name, amount in sorted(field_totals.items(), key=lambda item: (-item[1], item[0]))
        ],
        "fundTotals": [
            {"key": source["key"], "label": source["label"], "amount": fund_totals[source["key"]], "accent": source["accent"]}
            for source in FUND_SOURCES
        ],
    }


def build_outline_payload(rows: pd.DataFrame, query: str) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    current_parent: dict[str, Any] | None = None

    for row in rows.to_dict("records"):
        basis = normalize_text(row.get("calc_basis"))
        if not basis:
            continue
        level = row.get("calc_basis_level") or get_calc_basis_level(basis)
        if level == "parent" or current_parent is None:
            current_parent = {
                "id": row["id"],
                "budget_type": normalize_text(row.get("budget_type")),
                "department": normalize_text(row.get("department")),
                "account_name": normalize_text(row.get("account_name")),
                "detail_project": normalize_text(row.get("detail_project")),
                "stat_item_code": normalize_text(row.get("stat_item_code")),
                "stat_item_name": normalize_text(row.get("stat_item_name")),
                "calc_basis": basis,
                "calc_formula": normalize_text(row.get("calc_formula")),
                "budget_amount": float(row.get("budget_amount", 0) or 0),
                "search_text": row.get("search_text", ""),
                "children": [],
            }
            payload.append(current_parent)
            continue

        child_level = level if level in {"child", "grandchild"} else "item"
        current_parent["children"].append(
            {
                "id": row["id"],
                "calc_basis": basis,
                "calc_formula": normalize_text(row.get("calc_formula")),
                "budget_amount": float(row.get("budget_amount", 0) or 0),
                "level": child_level,
                "search_text": row.get("search_text", ""),
            }
        )

    matcher = build_search_matcher(query)
    if not has_search_query(matcher):
        return payload

    filtered_payload: list[dict[str, Any]] = []
    for entry in payload:
        parent_matches = matches_search_text(entry.get("search_text", ""), matcher)
        if parent_matches:
            filtered_payload.append(entry)
            continue
        matched_children = [
            child
            for child in entry["children"]
            if matches_search_text(
                normalize_search_value(
                    " ".join(
                        [
                            entry.get("department", ""),
                            entry.get("account_name", ""),
                            entry.get("detail_project", ""),
                            entry.get("stat_item_code", ""),
                            entry.get("stat_item_name", ""),
                            child.get("calc_basis", ""),
                            child.get("calc_formula", ""),
                        ]
                    )
                ),
                matcher,
            )
        ]
        if matched_children:
            next_entry = dict(entry)
            next_entry["children"] = matched_children
            filtered_payload.append(next_entry)
    return filtered_payload


def compare_budget_rows(left: dict[str, Any], right: dict[str, Any]) -> int:
    comparisons = [
        compare_budget_types(left.get("budget_type"), right.get("budget_type")),
        compare_departments(left.get("department"), right.get("department")),
        (normalize_text(left.get("account_name")) > normalize_text(right.get("account_name")))
        - (normalize_text(left.get("account_name")) < normalize_text(right.get("account_name"))),
        (normalize_text(left.get("detail_project")) > normalize_text(right.get("detail_project")))
        - (normalize_text(left.get("detail_project")) < normalize_text(right.get("detail_project"))),
        (normalize_text(left.get("stat_item_name")) > normalize_text(right.get("stat_item_name")))
        - (normalize_text(left.get("stat_item_name")) < normalize_text(right.get("stat_item_name"))),
        (normalize_text(left.get("stat_item_code")) > normalize_text(right.get("stat_item_code")))
        - (normalize_text(left.get("stat_item_code")) < normalize_text(right.get("stat_item_code"))),
    ]
    for comparison in comparisons:
        if comparison != 0:
            return comparison
    left_amount = float(left.get("budget_amount", 0) or 0)
    right_amount = float(right.get("budget_amount", 0) or 0)
    return (right_amount > left_amount) - (right_amount < left_amount)


def sort_budget_items(rows: pd.DataFrame) -> pd.DataFrame:
    records = sorted(rows.to_dict("records"), key=cmp_to_key(compare_budget_rows))
    return pd.DataFrame(records)


def strip_basis_prefix(value: str | None) -> str:
    raw = normalize_text(value)
    if not raw:
        return "-"
    stripped = raw.lstrip("○-˚ ").strip()
    return stripped or raw


def get_org_department_lines(department: str | None) -> tuple[str, str]:
    raw = normalize_text(department)
    if not raw:
        return ("-", "")
    org_name = get_org_name(raw)
    if org_name and org_name != raw:
        return (org_name, raw)
    return (raw, "")
