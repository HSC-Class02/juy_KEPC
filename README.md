# 한국전력공사 DART 재무분석 Agent

한국전력공사(고유번호 `00159193`)의 DART 사업보고서를 OpenDART API로 수집하고,
사용자가 지정한 DART 기업 RSS(`companyRSS.xml`)도 원본 그대로 보관하며,
재무제표 핵심 수치와 재무비율을 계산한 뒤 GitHub Pages 대시보드에 반영하는 자동화 프로젝트입니다.

## 구조
- `src/dart_client.py`: OpenDART API 호출
- `src/parser.py`: 재무제표 계정 추출/정규화
- `src/analysis.py`: 재무비율 계산 및 실무 가이드 기반 신호 생성
- `scripts/update.py`: 신규 사업보고서 탐지 → 원문 ZIP/JSON 저장 → 분석 JSON 생성
- `dashboard/`: GitHub Pages용 정적 대시보드
- `.github/workflows/update.yml`: 자동 업데이트
- `data/raw/`: DART 원문 및 API 응답
- `data/processed/`: 대시보드 입력 데이터

## 자동 업데이트
GitHub Actions가 매일 실행됩니다. 신규 사업보고서가 있으면 원문을 저장하고 분석 결과를 갱신합니다.
수동 실행도 가능합니다.

## API Key
API Key는 코드나 Git에 넣지 않습니다.
GitHub Repository → Settings → Secrets and variables → Actions → New repository secret에서
`DART_API_KEY` 이름으로 저장합니다.

## 로컬 실행
```bash
python -m pip install -r requirements.txt
set DART_API_KEY=발급키
python scripts/update.py
```

Linux/macOS:
```bash
export DART_API_KEY=발급키
python scripts/update.py
```

## GitHub Pages
Settings → Pages → Build and deployment → Source를 `GitHub Actions`로 설정합니다.
`pages.yml` workflow가 `dashboard/`를 Pages에 배포합니다.

## 분석 기준
첨부된 「재무제표 및 재무비율 실무 가이드」의 핵심 수치/비율 정의를 기준으로 구현했습니다.
연결(CFS) 기준을 우선 사용하며, 가능한 경우 3~5개 사업연도 추세를 보여줍니다.
