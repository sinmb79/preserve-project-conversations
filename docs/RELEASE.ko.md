# 릴리스와 게시 가이드

이 프로젝트는 GitHub Release 산출물을 먼저 공개합니다. PyPI 게시는 GitHub Actions 수동 실행과 PyPI Trusted Publisher 설정이 모두 갖춰졌을 때만 진행됩니다.

## 로컬 준비

```bash
python -m pip install --upgrade build twine
```

Windows PowerShell에서 한국어 출력이 깨져 보이면 릴리스 검증 전에 UTF-8 출력을 설정합니다.

```powershell
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
```

## 로컬 릴리스 검증

저장소 루트에서 아래 명령을 실행합니다.

```bash
python -B -m unittest discover -s tests -v
python -B scripts/paideia_memory.py doctor
python -B scripts/paideia_memory.py scan --target .
python -m build
python -m twine check dist/*
```

기대 결과:

- 전체 테스트 통과
- `doctor`가 `status=ok` 출력
- `scan`이 `status: ok` 출력
- wheel과 source distribution 모두 `twine check` 통과

## GitHub Release

1. `main`에 커밋하고 푸시합니다.
2. annotated tag를 만들고 푸시합니다.

```bash
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin main vX.Y.Z
```

3. 태그에 대해 `Release` workflow가 성공했는지 확인합니다.
4. GitHub Release를 만들고 `dist/`의 wheel과 source distribution을 업로드합니다.

## PyPI Trusted Publisher

PyPI 게시 workflow는 PyPI 프로젝트에 trusted publisher가 설정된 뒤에만 동작합니다.

- PyPI project: `preserve-project-conversations`
- Owner: `sinmb79`
- Repository: `preserve-project-conversations`
- Workflow file: `.github/workflows/release.yml`
- Environment: `pypi`

PyPI에서 위 설정을 완료한 뒤 GitHub Actions의 `Release` workflow를 수동 실행하고 `publish_pypi`를 `true`로 설정하면 PyPI 게시가 진행됩니다.

태그 푸시는 산출물 빌드와 검증만 수행합니다. PyPI에는 자동 게시하지 않습니다. 패키지 공개를 사람이 명시적으로 승인하도록 두기 위한 설계입니다.
