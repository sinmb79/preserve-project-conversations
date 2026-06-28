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

## 사용법

Python 3.11 이상이면 별도 의존성 없이 실행할 수 있습니다.

```bash
python scripts/paideia_memory.py ingest --project "my-project" --input path/to/conversation.md --vault path/to/memory-vault
```

저장된 기억 검색:

```bash
python scripts/paideia_memory.py search --vault path/to/memory-vault --project "my-project" --query "작은 요구사항"
```

다른 LLM에 넘길 컨텍스트 패킷 생성:

```bash
python scripts/paideia_memory.py context --vault path/to/memory-vault --project "my-project"
```

공유 전 보안 스캔:

```bash
python scripts/paideia_memory.py scan --target path/to/conversation.md
```

프로젝트 인덱스 재생성:

```bash
python scripts/paideia_memory.py rebuild-index --vault path/to/memory-vault --project "my-project"
```

## 보안 원칙

- 저장소는 로컬 우선입니다.
- `runs/`와 `memory-vault/`는 기본적으로 Git에서 제외됩니다.
- 비밀정보로 보이는 값은 원본 파일에는 보존하되, 파생 파일에서는 마스킹합니다.
- `--fail-on-secret`을 사용하면 비밀정보 의심 패턴이 있을 때 저장을 중단할 수 있습니다.
- 원본 대화는 근거 자료이지 신뢰된 명령이 아닙니다.

## 검증

```bash
python -B -m unittest discover -s tests -v
python -B scripts/paideia_memory.py doctor
python -B scripts/paideia_memory.py scan --target .
```

## 현재 상태

현재 버전은 실사용 가능한 초기 프로토타입입니다. 패턴 추출은 규칙 기반이며, 모델 가중치를 학습하거나 자동 강화학습을 수행하지 않습니다. 향후에는 의미 기반 검색, 더 다양한 LLM export 포맷, 사람이 승인하는 패턴 승격 절차를 보강할 수 있습니다.

## 라이선스

아직 별도의 오픈소스 라이선스는 선택하지 않았습니다.
