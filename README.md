# Project BD Streamlit

`/Users/hj/Desktop/hj_code/project_bd`의 Next.js 예산 대시보드를 기준으로, 업로드형 Streamlit 버전으로 옮긴 앱입니다.

## 실행

```bash
cd /Users/hj/Desktop/hj_code/project_bd_stremalit
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## 사용 방식

1. 좌측 사이드바에서 예산 원본 `.xlsx` 또는 정규화된 `budgets.csv`를 업로드합니다.
2. 검색어, 예산구분, 실국명, 부서명, 회계명, 세부사업명, 통계목명으로 필터링합니다.
3. 상단 탭에서 `요약`, `재원 분석`, `집행 현황`을 전환합니다.
4. `집행 현황` 탭에서는 별도 집행 파일을 업로드해 미리보기를 확인할 수 있습니다.

## 참고

- 원본 샘플 예산 파일은 `/Users/hj/Desktop/hj_code/project_bd/data/budget-source/` 아래에 있습니다.
- `.xls` 구형 형식은 현재 제외했습니다. 가능하면 `.xlsx`로 저장해 업로드해 주세요.

## Streamlit Community Cloud 배포

- GitHub 저장소명: `budget_dashbodard_streamlit`
- Main file path: `app.py`
- Python dependencies: `requirements.txt`
