[![🔗 대시보드 바로가기](https://img.shields.io/badge/%F0%9F%94%97-%EB%8C%80%EC%8B%9C%EB%B3%B4%EB%93%9C%20%EB%B0%94%EB%A1%9C%EA%B0%80%EA%B8%B0-173B63?style=for-the-badge&logo=github&logoColor=white)](https://hsc-class02.github.io/juy_KEPC/)

# 한국전력공사 DART 재무분석 Agent

한국전력공사(고유번호 **00159193**)의 OpenDART 재무정보를 수집·정리하고, 주요 재무지표와 추세를 대시보드로 시각화하는 프로젝트입니다.

## 대시보드

**[🔗 한국전력공사 재무 대시보드 열기](https://hsc-class02.github.io/juy_KEPC/)**

- 상단: 핵심 KPI, 연도별 재무 추세, 수익성 및 현금흐름 차트
- 하단: Annual, Half-year, Quarterly report 데이터를 각각 별도 테이블로 제공
- 마지막 섹션: 국내 비교기업(Peer Firms) 및 비교 가능성 메모

## 수집 범위와 분석

- 대상 기업: 한국전력공사 (DART 고유번호 00159193)
- 시작 연도: 2010년부터 API에서 제공되는 가용 자료
- 보고서 유형: 사업보고서(11011), 반기보고서(11012), 1분기보고서(11013), 3분기보고서(11014)
- 연결재무제표(CFS)를 우선 사용하고, 연결 데이터가 없는 경우 별도재무제표(OFS)를 대체 자료로 사용하며 데이터 기준을 표시합니다.
- 주요 지표: 매출액, 영업이익, 당기순이익, 총자산, 총부채, 자본, 영업·투자·재무 현금흐름, CAPEX, FCF, 영업이익률, 부채비율, 유동비율, 순차입금 등
- 분기별 표는 DART의 1분기·3분기 보고서 기준입니다. 한국의 정기 공시 주기에 따라 반기·연간 자료는 각각 별도 표로 표시합니다. 보고서에 공시된 값을 확인 없이 임의로 단일 분기 값으로 환산하지 않습니다.

## 자동 업데이트

GitHub Actions가 **매월 1일(한국시간 오전 9시)** 자동 실행되며, 수동 실행도 지원합니다. 분석 결과가 변경되면 대시보드 데이터 JSON을 갱신하고 GitHub Pages에 배포합니다.

## 저장소 구조

| 경로 | 역할 |
|---|---|
| `src/dart_client.py` | OpenDART API 호출 및 응답 처리 |
| `src/parser.py` | 재무제표 계정 추출·정규화 |
| `src/analysis.py` | 재무비율 및 분석 신호 계산 |
| `scripts/update.py` | 2010년 이후 정기보고서 데이터 수집·가공, 대시보드 데이터 생성 |
| `dashboard/index.html` | 차트 및 기간별 테이블을 제공하는 정적 대시보드 |
| `dashboard/data.json` | 대시보드에서 읽는 최신 데이터 |
| `.github/workflows/update.yml` | 월간 데이터 갱신 작업 |
| `.github/workflows/pages.yml` | GitHub Pages 배포 |

## 최초 설정

1. Repository의 **Settings → Secrets and variables → Actions**에서 repository secret을 추가합니다.
2. Secret 이름은 `DART_API_KEY`, 값은 OpenDART에서 발급한 API 인증키로 설정합니다. 기존 저장소에서 `OPENDART_API_KEY` 이름을 사용한다면 workflow가 해당 이름도 대체 키로 확인합니다.
3. **Settings → Pages**에서 배포 소스를 GitHub Actions로 설정합니다.
4. Actions 탭에서 **Update KEPCO financial data** workflow를 한 번 실행해 초기 데이터를 수집합니다. 워크플로가 저장소 변경 시 자동으로 시작되면 별도 실행은 필요하지 않습니다.

API 인증키는 코드 또는 README에 입력하지 마세요.

## 국내 Peer Firms

Peer firms는 사업 구조와 규제 환경을 기준으로 선정한 참고 비교군입니다. 사업·수익 모델이 완전히 같지는 않으며, 한국전력공사 연결재무제표에는 일부 계열사 실적이 포함될 수 있으므로 그룹 계열사와 한전 연결 실적을 동시에 합산해 비교하지 않도록 유의해야 합니다.

| 기업 | 주요 사업 / 비교 관점 | 상장·관계 | 비교 가능성 |
|---|---|---|---|
| [한국가스공사](https://www.kogas.or.kr/) | 국가 가스 도입·도매 및 공공 에너지 인프라 | 상장 공기업 | 높음 — 규제형 에너지 유틸리티 |
| [한국지역난방공사](https://www.kdhc.co.kr/) | 지역난방·열병합 발전 | 상장 공기업 | 높음 — 공공 에너지 공급 |
| [한국수력원자력](https://www.khnp.co.kr/) | 원자력·수력 발전 | 비상장, 한전 계열 | 사업 참고 — 그룹 연결 범위 유의 |
| [한전KPS](https://www.kps.co.kr/) | 발전 설비 정비·유지보수 | 상장, 한전 계열 | 사업 참고 — 정비 서비스 중심 |
| [한국전력기술](https://www.kepco-enc.com/) | 발전소 설계·엔지니어링 | 상장, 한전 계열 | 사업 참고 — 엔지니어링 중심 |
| [한국남동발전](https://www.koenergy.kr/) | 발전 사업 | 비상장, 한전 계열 | 사업 참고 — 발전 믹스 및 연료비 |
| [한국중부발전](https://www.komipo.co.kr/) | 발전 사업 | 비상장, 한전 계열 | 사업 참고 — 발전 믹스 및 연료비 |
| [한국남부발전](https://www.kospo.co.kr/) | 발전 사업 | 비상장, 한전 계열 | 사업 참고 — 발전 믹스 및 연료비 |
| [한국서부발전](https://www.iwest.co.kr/) | 발전 사업 | 비상장, 한전 계열 | 사업 참고 — 발전 믹스 및 연료비 |
| [한국동서발전](https://www.ewp.co.kr/) | 발전 사업 | 비상장, 한전 계열 | 사업 참고 — 발전 믹스 및 연료비 |
| [SGC에너지](https://www.sgcenergy.co.kr/) | 민간 발전·집단에너지 | 상장 민간기업 | 중간 — 민간 발전사 보조 비교군 |

비교군은 재무 수치가 자동 수집된다는 의미가 아니라, 한국전력공사 분석을 위한 국내 peer 목록입니다. 개별 기업의 수치 직접 비교를 추가할 때는 같은 회계기간, 연결/별도 기준, 회계 정책과 전력·열 사업 비중을 함께 확인하세요.
