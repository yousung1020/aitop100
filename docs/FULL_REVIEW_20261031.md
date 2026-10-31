# 전체 독립 재검토 — 2026-10-31

검토 기준 커밋: `c9b9cdc` (`fix(unit5): resolve review findings, enforce strict HTTP contract, and restore official TC multi-turn flows`). 검토 시작 시 작업 트리는 깨끗했습니다. API 계약, 대화·정책, 하네스를 서브 에이전트에 병렬 분담했고, 주요 발견은 루트에서도 로컬 탐침으로 재현했습니다. 런타임 코드·테스트·배포 설정은 수정하지 않았습니다.

**판정: 수정은 진전됐지만 Unit 3·4·5의 공식 적합성 완료 및 최종 제출 준비 완료를 인정하기 어렵습니다.** 아래 P1을 먼저 해결해야 합니다.

## 1. 검증 결과와 확인된 개선

| 검증 | 관찰 결과 | 범위 |
| :--- | :--- | :--- |
| `.venv/bin/python -m pytest -q` | **234 passed in 5.32s** | 기존 단위·통합 테스트 |
| `.venv/bin/python -m tests.simulate_30_cases` | **30/30 PASS**, 변이 자체 검사 4종 통과, 로컬 평균 약 28.8ms | 모델 비활성화·인메모리 Mock. Y-24는 부분 검증 표기 |
| Docker Compose 설정 | `docker compose config --quiet` 통과 | 설정 구문·해석 확인. 이미지 빌드/재배포는 실행하지 않음 |
| 배포 스크립트 | `bash -n scripts/deploy_to_ec2.sh` 통과 | 셸 구문 확인 |
| EC2 HTTP `/health` | `{"status":"ok","version":"2.0"}` | 프로세스 응답 확인. 모델·액션·배포 커밋·카카오 연동의 검증은 아님 |
| EC2 `/openapi.json` | `/skill`, `/skill/cs`, `/api/kakao/chat`, `/health` 확인 | 수신 모델은 `KakaoPayload` |

과거 지적 중 HTTP 메서드·정확한 경로·본문 키·TC 헤더의 기본 검사, R-05-a/Y-16의 재배송 후속 턴, L-11의 로트 조사·상담 이력 호출, L-34의 긴급 출고 호출, 실패 접수번호 기본값 일부 제거는 반영됐습니다. 개별 실패 때 전체 종료 코드가 1이 되도록 집계도 개선됐습니다. 모든 탐침에서 통과한 것은 아니므로 아래 결함과 함께 판단해야 합니다.

## 2. 제출 전 차단할 P1

### P1-1. 고객의 명시적 변경 거절 뒤에도 API-24 실행

위치: `app/agent/orchestrator.py:618`, `:626`, `:718`.

재현 순서:

1. 같은 사용자·TC `L-03`에서 `주문번호 100100003 주소 경기 성남시 판교역로 166 8층으로 변경 가능한가요?`를 보냅니다.
2. 다음 턴에 `아니요 변경하지 마세요.`라고 답합니다.
3. 실제 로컬 이력에 `POST /api/orders/100100003/address-change-requests`가 남습니다.

이전 주소를 세션에서 재사용하면서, 문의 키워드가 없는 다음 발화를 변경 의사로 취급합니다. 취소·거절·다른 문의에 접수하지 않는 검사가 필요합니다.

### P1-2. TC 변경 뒤 이전 주문·주소 상태로 변경 접수

위치: `app/agent/orchestrator.py:899`.

위 첫 턴 이후 같은 `user_key`로 TC를 `L-20`으로 바꾸고 `안녕하세요.`만 보냈을 때, **이전 주문 100100003에 L-20 헤더로 주소 변경 POST**가 실행됐습니다. `session.test_case_id`만 바꾸고 기존 flow·대상·임시 주소를 유지하기 때문입니다. TC 및 인입 계정 전환 때 이전 상담 상태가 새 상담의 액션으로 이어지지 않아야 합니다.

### P1-3. 미확보 판매자 공시 값을 공식 정보로 하드코딩

위치: `app/agent/orchestrator.py:190`.

Y-24 응답에 대표자 `양정환`, 사업자등록번호·제주 주소·대표 전화가 고정되어 있습니다. 보관된 `docs/`의 Markdown·텍스트·JSON·HTML에서 이 값들의 출처가 발견되지 않았으며, [직전 조사](POLICY_AND_SUBMISSION_RESEARCH.md)는 실제 공시 원본을 미확보로 명시합니다. 하네스의 부분 검증 표기가 고객에게 출처 없는 공시 값을 사실로 안내해도 된다는 근거는 아닙니다. 원문 확보 전 이 값을 공식 정보로 사용해서는 안 됩니다.

### P1-4. Mock 전용 주문·결제 필드 때문에 공식 응답에서 현금영수증 처리 불가

위치: `app/agent/orchestrator.py:527`, `:533`; `app/actions/mock_server.py:497`.

L-05는 주문의 `payment_method`, `approval_no`를 사용합니다. 공식 `Orders`에는 해당 필드가 없고 결제 참조는 `payment_refs`입니다. 결제 모델의 수단 필드는 `pay_method`입니다. Mock이 앱이 기대하는 비공식 필드를 공급해 기존 테스트가 통과합니다.

공식 필드로 구성한 주문 응답을 로컬에 주입하면 올바른 `payment_refs=["PAY-3706-0003"]`가 있어도 현금영수증 POST는 0건이며 “승인번호가 확인되지 않아 접수 불가”라고 답했습니다. 공식 스키마를 기준으로 참조 해석과 결제수단 검증을 연결해야 합니다. 추가 API를 어떤 상황에 호출할지는 공식 기대 흐름과 함께 검토해야 하며 테스트 편의를 위해 필드를 추가하면 안 됩니다.

### P1-5. L-11에서 고객 선택·신체 이상 확인 없이 환불과 폐기 안내

위치: `app/agent/orchestrator.py:203`.

주문번호를 모르면 묻도록 개선했지만 주문번호만 확보되면 환불 34,900원을 고정 접수합니다. 고객이 환불을 선택했는지, 섭취 후 이상이 있어 원물 보관이 필요한지 확인하는 상태가 없습니다. 주석의 “환불 의사 미확인” 설명과 실제 조건 `if not order_id`도 다릅니다. 수령·로트·하자·회원·선택의 근거 없이 고정된 환불을 접수하지 않아야 합니다. 신체 이상을 묻는 응답에서도 이미 폐기를 안내하므로 안전·배상 조사 예외가 누락됩니다.

### P1-6. 하네스가 금지되지 않은 추가 액션·호출 순서 위반을 통과

위치: `tests/simulate_30_cases.py:180`, `:200`.

메서드·정확 경로 등 검사는 추가됐으나 기대 호출을 순서 없는 존재 검사로 처리하고, 선언되지 않은 추가 호출을 기본 거절하지 않습니다. 본문 타입과 query의 추가 키도 검사하지 않습니다.

독립 탐침에서 다음 결과가 나왔습니다. 모두 실제 외부 액션 없이 메모리의 호출 기록만 검사했습니다.

| 잘못된 호출 기록 | 현재 검증 결과 |
| :--- | :--- |
| L-05의 현금영수증 POST를 주문 GET보다 먼저 배치 | `(True, [])` |
| 정상 L-05 뒤 다른 회원 `MB-OTHER`의 쿠폰 발급 POST 추가 | `(True, [])` |
| 단건 주문 GET에 미지원 query 추가 | `(True, [])` |
| 기대 API가 없는 턴에 `DELETE /api/not-documented` 추가 | `(True, [])` |

서브 에이전트에서는 환불 `reason`을 객체로 바꾸는 타입 위반도 통과함을 확인했습니다. 실제 공식 OpenAPI로 요청 계약 전체를 대조하고, 허용된 추가 조회·순서 대안과 금지 액션을 구분해 판정해야 합니다.

## 3. API·Mock의 추가 계약 결함

공식 [OpenAPI 스냅샷](source_materials/official_actions_openapi.json)과 Mock의 원응답을 로컬에서 비교했습니다. 클라이언트가 덧붙인 필드를 검사한 것이 아닙니다.

| 응답 모델 | 확인한 차이 |
| :--- | :--- |
| Orders | `payment_refs`, `items`, `shipping_address` 등 필수 필드 누락. `approval_no`, `payment_method` 등 비공식 필드 존재 |
| Shipments | `invoice_no`, `picked_up_at`, `items` 등 누락. `tracking_no` 사용 및 공식 enum 밖 상태값 |
| Products | `sale_state`, `listed_weight`, `origin`, `grade`, `variety` 누락. 비공식 `normal_price`, `status` 사용 |
| Payments | `pay_method`, 결제일·결제자 등 누락. 비공식 `method` 및 공식 enum 밖 상태값 |
| EscalationsReceipt | 필수 `request_status` 누락. `status=ASSIGNED` 등 비공식 응답 필드 |

Mock은 TC 헤더가 없어도, `TC-DEFAULT`를 보내도 200을 반환했습니다. 직전 실서버 GET 테스트에서 해당 요청들은 각각 400 `MISSING_TEST_CASE_ID`, `INVALID_TEST_CASE_ID`였습니다. [실서버 검증 기록](source_materials/live_api_readonly_20261031.json)과 다릅니다.

`app/actions/client.py:191`은 정상 HTTP 200의 주문 상태 `FAILED`를 통신 실패로 해석합니다. 공식 `Orders.status`에는 `FAILED`가 유효한 업무 상태로 존재하므로 조회 성공 여부와 업무 상태를 분리해야 합니다.

멱등 처리도 전부 해결된 것은 아닙니다. `app/actions/mock_server.py:535`는 일정 날짜를 접수 키에 포함하여 같은 주문의 변경 본문을 다시 접수하면 번호가 바뀝니다. `:555`는 긴급 출고 접수의 기존 번호를 돌려주지만 본문 갱신을 하지 않습니다. 공식 계약은 같은 접수 API·같은 대상의 접수번호 유지 및 마지막 본문 반영입니다.

## 4. 배포·운영 검토 및 제한

### P2 — 배포 스크립트가 헬스체크 실패를 성공 처리

위치: `scripts/deploy_to_ec2.sh:54`.

`curl -s ... || echo ...`로 실패를 삼키며 HTTP 오류에도 `-f`가 없어 성공으로 끝날 수 있습니다. 그 뒤 배포 완료를 출력합니다. 실행 구문이 맞는 것과 배포 성공을 검증하는 것은 별개입니다. 실패 시 비정상 종료 및 제한된 준비 대기 검증이 필요합니다. 실제 배포 스크립트는 이번에 실행하지 않았습니다.

### P2 — 컨테이너 설치가 잠금 버전을 사용하지 않음

위치: `Dockerfile:24`.

`uv.lock`을 복사하지만 설치는 `uv pip install --system -r pyproject.toml`로 수행합니다. 로컬에서 검증한 잠금 버전으로 설치된다고 보장할 수 없습니다. [uv 공식 Docker 안내](https://docs.astral.sh/uv/guides/integration/docker/)와 [잠금·동기화 설명](https://docs.astral.sh/uv/concepts/projects/sync/)은 프로젝트 잠금 설치에 `uv sync --locked`/`--frozen` 사용을 설명합니다. 실제 수정 시 이미지의 실행 환경과 함께 정리해야 합니다.

### 평가 봇 연동은 여전히 별도 확인 필요

EC2의 공개 HTTP 헬스체크와 OpenAPI 조회는 성공했습니다. 그러나 원격 프로세스가 정확히 검토 커밋을 실행하는지, 실제 평가 App ID에 연결되는지, HTTPS 진입점·평가 계정 접근·카카오 송수신 계약이 맞는지는 확인하지 않았습니다. [공식 안내 조사](POLICY_AND_SUBMISSION_RESEARCH.md)의 카카오디벨로퍼스 봇 REST 안내와 현재 `KakaoPayload` 기반 스킬 수신 방식의 호환성 확인이 필요합니다.

웹훅의 실제 모델·실서버 액션을 부르는 요청이나 원격 재배포는 하지 않았습니다. 기존 13건 실서버 GET 기록은 서버 계약 확인이며 전체 상담 플로우의 통과 증거가 아닙니다.

## 5. 권장 처리 순서

1. 명시적 취소·거절 뒤 POST 및 TC·계정 전환에 따른 상담 상태 혼용을 차단합니다.
2. 출처 없는 판매자 공시값을 제거하고, 공식 응답 필드로 L-05 등 실제 액션 연결을 보완합니다.
3. L-11의 고객 선택·신체 이상·대상 근거를 확인하는 흐름을 보완합니다.
4. 공식 OpenAPI 기준 Mock 응답·헤더·멱등성을 교정하고, 추가 액션·순서·타입·query 변이가 실패하도록 하네스를 강화합니다.
5. 위 검증 후 실제 평가 봇의 송수신·배포 버전·HTTPS·지연을 확인합니다. 로컬 Mock 통과 수치를 공식 심사 전체 통과로 표기하지 않습니다.

공유 HANDOFF·기존 리뷰 문서는 병행 작업과 충돌하지 않도록 그대로 두고, 이번 판정과 근거는 이 문서에 기록합니다. 검토 중 새 정책이나 배포 인프라를 선택하지 않았습니다.
