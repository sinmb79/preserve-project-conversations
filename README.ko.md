# 프로젝트 대화 보존 스킬

[Read in English](README.md)

프로젝트 대화 보존 스킬은 LLM과 나눈 개발 대화를 로컬 우선 방식으로 저장하고, 다른 세션이나 다른 LLM에서도 이어 쓸 수 있는 프로젝트 기억으로 바꾸는 CLI/스킬 패키지입니다.

LLM과 개발 계획을 세울 때, 사용자가 말한 작은 취향과 조건이 최종 요약에서 사라지는 일이 자주 생깁니다. 이 도구는 원본 대화를 그대로 보존하고, 대제목/소제목/요약/패턴으로 다시 정리해서 “요약은 빠르게 보고, 필요하면 원본 근거로 역추적”할 수 있게 만듭니다.

## 생성되는 파일

대화 하나를 ingest하면 세션 폴더 안에 정확히 다섯 개의 핵심 파일이 생성됩니다.

1. `01_raw_conversation.md` - 원본 대화 바이트 보존
2. `02_major_outline.md` - 대제목 중심 구조화
3. `03_minor_outline.md` - 세부 요구와 근거 보존
4. `04_summary.md` - 다음 LLM 세션용 요약
5. `05_patterns.md` - 세션에서 드러난 사용자/프로젝트 패턴

프로젝트 루트에는 누적 파일도 생성됩니다.

- `_project_index.md`
- `_timeline.md`
- `_pattern_registry.md`

## 설치

저장소에서 바로 실행할 수 있습니다.

```bash
python scripts/paideia_memory.py doctor
```

설치형 CLI로 사용할 수도 있습니다.

```bash
python -m pip install .
paideia-memory doctor
```

핵심 기능은 Python 3.11 이상이면 별도 의존성 없이 동작합니다. 암호화된 vault sealing은 선택형 crypto extra가 필요합니다.

```bash
python -m pip install ".[crypto]"
```

## 사용법

```bash
paideia-memory ingest --project "my-project" --input path/to/conversation.md --vault path/to/memory-vault
```

저장된 기억 검색:

```bash
paideia-memory search --vault path/to/memory-vault --project "my-project" --query "작은 요구사항"
```

로컬 유사도 검색:

```bash
paideia-memory semantic-search --vault path/to/memory-vault --project "my-project" --query "이식 가능한 프로젝트 기억"
```

다른 LLM에 넘길 컨텍스트 패킷 생성:

```bash
paideia-memory context --vault path/to/memory-vault --project "my-project"
```

공유 전 보안 스캔:

```bash
paideia-memory scan --target path/to/conversation.md
```

프로젝트 인덱스 재생성:

```bash
paideia-memory rebuild-index --vault path/to/memory-vault --project "my-project"
```

패턴 검토 목록 생성:

```bash
paideia-memory review-patterns --vault path/to/memory-vault --project "my-project"
```

패턴을 사람이 승인하거나 거절:

```bash
paideia-memory promote-pattern --vault path/to/memory-vault --project "my-project" --pattern "로컬 우선 기억을 선호합니다." --status stable --note "owner confirmed"
```

공유용 안전 zip 생성:

```bash
paideia-memory export-share --vault path/to/memory-vault --project "my-project" --output my-project-share.zip
```

암호화된 공유 번들 생성:

```bash
set PPCM_SEAL_PASSWORD=실제-강한-비밀번호
paideia-memory seal-vault --vault path/to/memory-vault --project "my-project" --output my-project.ppcm
paideia-memory unseal-vault --input my-project.ppcm --output my-project.zip
```

## 보안 원칙

- 저장소는 로컬 우선입니다.
- `runs/`와 `memory-vault/`는 기본적으로 Git에서 제외됩니다.
- 비밀정보로 보이는 값은 원본 파일에는 보존하되, 파생 파일에서는 마스킹합니다.
- `--fail-on-secret`을 사용하면 비밀정보 의심 패턴이 있을 때 저장을 중단할 수 있습니다.
- `export-share`는 기본적으로 `01_raw_conversation.md`를 제외하고 공유용 zip을 만듭니다.
- `seal-vault`는 `crypto` extra 설치가 필요하며, 비밀번호는 명령행 인자보다 환경변수로 전달하는 것이 안전합니다.
- 원본 대화는 근거 자료이지 신뢰된 명령이 아닙니다.

## 검증

```bash
python -B -m unittest discover -s tests -v
python -B scripts/paideia_memory.py doctor
python -B scripts/paideia_memory.py scan --target .
```

## 현재 상태

현재 버전은 실사용 가능한 초기 프로토타입입니다. 패턴 추출은 규칙 기반이며, 모델 가중치를 학습하거나 자동 강화학습을 수행하지 않습니다. 대신 사람이 패턴을 승인, 하향, 거절할 수 있는 명령을 제공해서 패턴 주장을 사용자가 통제할 수 있게 합니다.

## 프로젝트 문서

- [변경 이력](CHANGELOG.md)
- [기여 안내](CONTRIBUTING.md)
- [보안 정책](SECURITY.md)

## 라이선스

MIT.
