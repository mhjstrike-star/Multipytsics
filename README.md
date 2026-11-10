# Multi-Physics Software

Main에서 설계변수와 출력변수를 확정하고, Screening에서 데이터 품질을 점검하며, AMR과 DO에서 후속 작업을 수행하는 프로젝트입니다. 현재 작업 브랜치의 개발 대상은 Screening입니다.

## 브랜치와 원복 기준

| 브랜치 | 확인한 커밋 | 역할 |
| --- | --- | --- |
| `feature/new-work` | `db8c75a` | 현재 Screening 작업 브랜치. AMR 수정 전 공통 커밋에서 시작합니다. |
| `backup/AMR_OLD`, `origin/backup/AMR_OLD` | `791ce79` | AMR 수정과 모의 실행 예제의 보관 위치입니다. |
| `main`, `origin/main` | `791ce79` | 확인 시점에 AMR 보관 브랜치와 같은 커밋을 가리킵니다. |

`feature/new-work`의 원복 기준인 `db8c75a`에는 해석 로그를 `task/amrfunction.log`로 모으는 변경까지 들어 있습니다. 이 기준점 이후의 AMR 변경은 `backup/AMR_OLD`에서 확인할 수 있습니다. 브랜치 전환 시 `page_AMR.py`, `functions/amr_functions.py`, `functions/solve.py`는 기준 커밋의 버전으로 돌아가며, AMR 모의 실행 소스와 `.gitignore`도 현재 기준 커밋에는 없습니다. 이전에 생성한 `Example_Code/runs` 및 `Example_Code/_numba_cache` 폴더는 작업 디렉터리에 남을 수 있습니다. 기준 커밋에는 Python 바이트코드가 추적되어 있으므로 Screening 변경을 커밋할 때는 변경 파일 목록을 확인합니다.

## 보관한 AMR 수정 내역

| 커밋 | 변경 내용 |
| --- | --- |
| `16d1252` | 실행 및 이어하기 중복 요청을 차단하고, 실제 작업 프로세스 종료 후 재실행을 허용합니다. |
| `177bf8d` | 작업 폴더 정리 전에 필수 입력, 고객사 `AutoCal` 연결, 이어하기 CSV의 숫자 형식과 열 개수를 검증합니다. |
| `8321c5d` | `AutoCal` 호출 실패 시 완료 파일 대기를 건너뛰고, 노드·IP·실험점 작업 번호와 오류를 로그에 남깁니다. |
| `7e58131` | `All` 해석에서 Maxwell과 Mechanical 완료가 모두 확인된 뒤 결과를 읽습니다. |
| `cfc43fc` | Python 캐시, 가상환경, AMR 작업 파일을 Git에서 제외하는 `.gitignore`를 추가했습니다. |
| `6111785` | 이어하기 번호를 저장된 카운터와 기존 작업 폴더에서 복구합니다. 화면의 개선 정체 횟수를 새 실행과 이어하기의 `no_imp_count`에 전달합니다. |
| `a553202` | `Example_Code/Run_AMR_Demo.cmd`와 모의 해석 예제를 추가했습니다. 예제는 상위 폴더를 프로젝트 경로로 사용하고, `toolbox_path.txt`에서 ToolBox 위치를 읽습니다. |

AMR 보관 브랜치에서는 설치된 AMR 엔진과 모의 해석 응답으로 실험점 18개 평가와 `Restart.csv` 생성을 확인했습니다. 고객사 `AutoCal`을 통한 실제 Ansys 해석은 별도 연동 검증이 필요합니다.

## Screening

- [page_main.py](page_main.py)의 설계변수 확정 처리에서 Screening의 `refresh_table()`을 호출합니다. [page_screening.py](page_screening.py)는 확정된 설계변수와 출력변수를 표에 표시합니다.
- Screening의 `실행` 버튼은 `PageScreening.on_execute()`에 연결되어 있습니다. 함수가 비어 있어 현재는 분석을 시작하거나 실행 로그를 생성하지 않습니다.
- [functions/screening_functions.py](functions/screening_functions.py)에는 `AIDPrep` 기반 예제 흐름이 있습니다. 1차원 이상점, 중복점, 2차원 이상점, 데이터 부족을 검사한 뒤 정제 데이터를 리포트용으로 저장합니다. 현재 함수는 `cpath`를 입력받지 않고 참조하며, `Threebar_ex.csv`, 데이터 개수, 변수명과 범위가 예제에 고정되어 있습니다.

### 다음 구현 순서

1. Screening 입력 CSV의 열 구성, 헤더, 설계변수·출력변수 순서를 정합니다. 입력과 출력 경로를 명시적으로 전달하고, 확정 변수 개수에 맞춰 파일을 검증합니다.
2. `screening_functions.main()`에서 예제 전용 값을 입력 인자로 바꾸고, 이상점·중복점·데이터 부족 판정 및 결과 파일 위치를 호출부에 전달합니다.
3. `PageScreening.on_execute()`에서 검증된 입력을 백엔드에 넘기고, 분석 진행과 완료·오류를 화면 로그에 표시합니다.
4. 정상 행, 중복 행, 이상점이 있는 작은 CSV로 입력부터 정제 결과 저장까지 확인합니다.