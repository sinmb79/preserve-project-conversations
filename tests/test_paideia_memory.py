import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from datetime import datetime as real_datetime, timezone
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "paideia_memory.py"
SPEC = importlib.util.spec_from_file_location("paideia_memory", SCRIPT)
assert SPEC and SPEC.loader
MEMORY_MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MEMORY_MODULE
SPEC.loader.exec_module(MEMORY_MODULE)


SAMPLE = """보스: LLM과 개발 계획을 세우면 요약 과정에서 작은 요구가 누락됩니다.
줄리아: 어떤 방식으로 보존하면 좋을까요?
보스: 원본, 대제목, 소제목, 요약본, 패턴 총 5가지를 저장해야 합니다.
보스: 사용자가 다른 LLM을 쓰더라도 저장된 내용으로 프로젝트를 이어갈 수 있어야 합니다.
보스: 사용자의 개성과 개발 방식을 패턴화하고, 오류는 검증해서 숨기지 않아야 합니다.
"""


class PaideiaMemoryCliTests(unittest.TestCase):
    def run_cli(
        self,
        *args: str,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command_env = os.environ.copy()
        if env:
            command_env.update(env)
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), *args],
            cwd=str(cwd or ROOT),
            env=command_env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_ingest_creates_exact_five_core_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "conversation.md"
            source.write_text(SAMPLE, encoding="utf-8")
            vault = tmp_path / "vault"

            result = self.run_cli(
                "ingest",
                "--project",
                "보스 기억 테스트",
                "--input",
                str(source),
                "--vault",
                str(vault),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            session = Path(result.stdout.strip())
            files = sorted(path.name for path in session.iterdir())
            self.assertEqual(
                files,
                [
                    "01_raw_conversation.md",
                    "02_major_outline.md",
                    "03_minor_outline.md",
                    "04_summary.md",
                    "05_patterns.md",
                ],
            )
            self.assertEqual((session / "01_raw_conversation.md").read_text(encoding="utf-8"), SAMPLE)
            self.assertIn("총 5가지를 저장", (session / "04_summary.md").read_text(encoding="utf-8"))
            self.assertIn("작은 차이", (session / "05_patterns.md").read_text(encoding="utf-8"))
            project_root = session.parent
            self.assertTrue((project_root / "_project_index.md").exists())
            self.assertTrue((project_root / "_timeline.md").exists())
            registry = (project_root / "_pattern_registry.md").read_text(encoding="utf-8")
            self.assertIn("Pattern Registry", registry)
            self.assertRegex(registry, r"\[(candidate|observed|stable)\]")

    def test_search_finds_pattern_and_summary_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "conversation.md"
            source.write_text(SAMPLE, encoding="utf-8")
            vault = tmp_path / "vault"
            ingest = self.run_cli(
                "ingest",
                "--project",
                "memory-portability",
                "--input",
                str(source),
                "--vault",
                str(vault),
            )
            self.assertEqual(ingest.returncode, 0, ingest.stderr)

            result = self.run_cli(
                "search",
                "--project",
                "memory-portability",
                "--vault",
                str(vault),
                "--query",
                "다른 LLM 프로젝트 이어갈",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("04_summary.md", result.stdout)
            self.assertIn("_pattern_registry.md", result.stdout)

    def test_fail_on_secret_blocks_ingest_without_partial_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "conversation.md"
            fake_key = "sk-" + "proj-" + ("abcdefghijklmnopqrstuvwxyz" + "123456")
            source.write_text(
                f"보스: 이 키는 저장하면 안 됩니다 {fake_key}\n",
                encoding="utf-8",
            )
            vault = tmp_path / "vault"

            result = self.run_cli(
                "ingest",
                "--project",
                "secret-test",
                "--input",
                str(source),
                "--vault",
                str(vault),
                "--fail-on-secret",
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("openai_api_key", result.stdout)
            self.assertFalse(vault.exists())

    def test_secret_is_preserved_only_in_raw_and_masked_in_derived_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            secret = "sk-" + "proj-" + ("abcdefghijklmnopqrstuvwxyz" + "123456")
            source = tmp_path / "conversation.md"
            source.write_text(
                f"보스: 원본에는 {secret} 이 있을 수 있지만 파생 파일은 숨겨야 합니다.\n",
                encoding="utf-8",
            )
            vault = tmp_path / "vault"

            result = self.run_cli(
                "ingest",
                "--project",
                "secret-mask",
                "--input",
                str(source),
                "--vault",
                str(vault),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            session = Path(result.stdout.strip())
            self.assertIn(secret, (session / "01_raw_conversation.md").read_text(encoding="utf-8"))
            for name in [
                "02_major_outline.md",
                "03_minor_outline.md",
                "04_summary.md",
                "05_patterns.md",
            ]:
                text = (session / name).read_text(encoding="utf-8")
                self.assertNotIn(secret, text, name)
            self.assertIn("sk-p...3456", (session / "04_summary.md").read_text(encoding="utf-8"))

    def test_raw_conversation_preserves_source_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "conversation.md"
            raw_bytes = b"\xef\xbb\xbf" + "보스: 원본 CRLF 보존\r\n줄리아: 확인했습니다\r\n".encode("utf-8")
            source.write_bytes(raw_bytes)
            vault = tmp_path / "vault"

            result = self.run_cli(
                "ingest",
                "--project",
                "byte-exact",
                "--input",
                str(source),
                "--vault",
                str(vault),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            session = Path(result.stdout.strip())
            self.assertEqual((session / "01_raw_conversation.md").read_bytes(), raw_bytes)

    def test_cp949_source_is_preserved_raw_and_decoded_for_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "conversation.txt"
            raw_bytes = "보스: CP949 원본도 저장해야 합니다.\r\n".encode("cp949")
            source.write_bytes(raw_bytes)
            vault = tmp_path / "vault"

            result = self.run_cli(
                "ingest",
                "--project",
                "cp949-source",
                "--input",
                str(source),
                "--vault",
                str(vault),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            session = Path(result.stdout.strip())
            self.assertEqual((session / "01_raw_conversation.md").read_bytes(), raw_bytes)
            self.assertIn("CP949 원본", (session / "04_summary.md").read_text(encoding="utf-8"))

    def test_scan_reports_secret_and_doctor_checks_encoding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "conversation.md"
            fake_token = "gh" + "p_" + ("abcdefghijklmnopqrstuvwxyz" + "ABCDE1234567890")
            source.write_text(
                f"보스: 토큰 {fake_token}\n",
                encoding="utf-8",
            )

            scan = self.run_cli("scan", "--target", str(source))
            self.assertEqual(scan.returncode, 1)
            self.assertIn("github_token", scan.stdout)
            self.assertNotIn("abcdefghijklmnopqrstuvwxyzABCDE", scan.stdout)

            doctor = self.run_cli("doctor")
            self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)
            self.assertIn("encoding=ok", doctor.stdout)

    def test_context_includes_accumulated_pattern_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            vault = tmp_path / "vault"
            for idx in range(2):
                source = tmp_path / f"conversation-{idx}.md"
                source.write_text(SAMPLE + f"보스: 반복 확인 {idx}\n", encoding="utf-8")
                result = self.run_cli(
                    "ingest",
                    "--project",
                    "context-project",
                    "--input",
                    str(source),
                    "--vault",
                    str(vault),
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            context = self.run_cli(
                "context",
                "--project",
                "context-project",
                "--vault",
                str(vault),
            )

            self.assertEqual(context.returncode, 0, context.stderr)
            self.assertIn("Accumulated Patterns", context.stdout)
            self.assertIn("_pattern_registry.md", context.stdout)
            registry = (vault / "context-project" / "_pattern_registry.md").read_text(encoding="utf-8")
            self.assertIn("[stable]", registry)
            self.assertIn("stable=2", registry)

    def test_json_import_handles_author_dict_and_rejects_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            valid = tmp_path / "conversation.json"
            valid.write_text(
                '{"messages":[{"author":{"role":"user"},"content":"보스: JSON 원본도 저장해야 합니다."}]}',
                encoding="utf-8",
            )
            vault = tmp_path / "vault"

            result = self.run_cli(
                "ingest",
                "--project",
                "json-import",
                "--input",
                str(valid),
                "--vault",
                str(vault),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            session = Path(result.stdout.strip())
            self.assertIn("JSON 원본", (session / "04_summary.md").read_text(encoding="utf-8"))

            malformed = tmp_path / "broken.json"
            malformed.write_text('{"messages": [', encoding="utf-8")
            bad = self.run_cli(
                "ingest",
                "--project",
                "json-import",
                "--input",
                str(malformed),
                "--vault",
                str(vault),
            )
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn("Invalid JSON conversation export", bad.stderr)

    def test_json_import_supports_common_llm_export_shapes(self) -> None:
        chatgpt_export = [
            {
                "mapping": {
                    "root": {"parent": None, "children": ["user"]},
                    "user": {
                        "parent": "root",
                        "children": ["assistant"],
                        "message": {
                            "create_time": 1,
                            "author": {"role": "user"},
                            "content": {"parts": ["보스: ChatGPT export 대화도 저장해야 합니다."]},
                        },
                    },
                    "assistant": {
                        "parent": "user",
                        "children": [],
                        "message": {
                            "create_time": 2,
                            "author": {"role": "assistant"},
                            "content": {"parts": ["줄리아: 저장하겠습니다."]},
                        },
                    },
                }
            }
        ]
        claude_export = {
            "chat_messages": [
                {"sender": "human", "text": "보스: Claude export 원본도 저장해야 합니다."},
                {"sender": "assistant", "text": "줄리아: 확인했습니다."},
            ]
        }
        gemini_export = {
            "turns": [
                {"role": "user", "parts": [{"text": "보스: Gemini turns 형식도 저장해야 합니다."}]},
                {"role": "model", "parts": [{"text": "줄리아: 처리하겠습니다."}]},
            ]
        }

        for obj, phrase in [
            (chatgpt_export, "ChatGPT export"),
            (claude_export, "Claude export"),
            (gemini_export, "Gemini turns"),
        ]:
            messages = MEMORY_MODULE.messages_from_json_obj(obj)
            self.assertGreaterEqual(len(messages), 2)
            self.assertEqual(messages[0].role, "user")
            self.assertIn(phrase, messages[0].content)

    def test_neutral_sessions_do_not_promote_unrelated_user_patterns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            vault = tmp_path / "vault"
            neutral = "user: Hello.\nassistant: Hello.\n"
            for idx in range(3):
                source = tmp_path / f"neutral-{idx}.md"
                source.write_text(neutral, encoding="utf-8")
                result = self.run_cli(
                    "ingest",
                    "--project",
                    "neutral-project",
                    "--input",
                    str(source),
                    "--vault",
                    str(vault),
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            registry = (vault / "neutral-project" / "_pattern_registry.md").read_text(encoding="utf-8")
            pattern_lines = [line for line in registry.splitlines() if line.startswith("- [")]
            self.assertEqual(pattern_lines, [])
            self.assertNotIn("small details", registry.lower())

    def test_repeated_same_source_gets_distinct_session_ids(self) -> None:
        class FixedDateTime:
            @staticmethod
            def now(tz=None):
                return real_datetime(2026, 1, 1, 0, 0, 0, 123456, tzinfo=tz or timezone.utc)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "conversation.md"
            source.write_text("user: preserve this project memory.\nassistant: acknowledged.\n", encoding="utf-8")
            vault = tmp_path / "vault"
            args = SimpleNamespace(
                project="collision-project",
                input=str(source),
                vault=str(vault),
                fail_on_secret=False,
            )
            original_datetime = MEMORY_MODULE.datetime
            MEMORY_MODULE.datetime = FixedDateTime
            try:
                first_out = io.StringIO()
                second_out = io.StringIO()
                with contextlib.redirect_stdout(first_out):
                    self.assertEqual(MEMORY_MODULE.ingest(args), 0)
                with contextlib.redirect_stdout(second_out):
                    self.assertEqual(MEMORY_MODULE.ingest(args), 0)
            finally:
                MEMORY_MODULE.datetime = original_datetime

            first_session = Path(first_out.getvalue().strip())
            second_session = Path(second_out.getvalue().strip())
            self.assertNotEqual(first_session, second_session)
            self.assertTrue(first_session.exists())
            self.assertTrue(second_session.exists())
            self.assertEqual(second_session.name, first_session.name + "-1")

    def test_human_pattern_review_and_promotion_override_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "conversation.md"
            source.write_text(SAMPLE, encoding="utf-8")
            vault = tmp_path / "vault"
            ingest = self.run_cli(
                "ingest",
                "--project",
                "human-review",
                "--input",
                str(source),
                "--vault",
                str(vault),
            )
            self.assertEqual(ingest.returncode, 0, ingest.stderr)

            review = self.run_cli("review-patterns", "--project", "human-review", "--vault", str(vault))
            self.assertEqual(review.returncode, 0, review.stderr)
            review_path = Path(review.stdout.strip())
            self.assertTrue(review_path.exists())
            self.assertIn("Pattern Review", review_path.read_text(encoding="utf-8"))

            pattern = "사용자는 승인된 패턴만 stable로 신뢰합니다."
            promoted = self.run_cli(
                "promote-pattern",
                "--project",
                "human-review",
                "--vault",
                str(vault),
                "--pattern",
                pattern,
                "--status",
                "stable",
                "--note",
                "manual approval",
            )
            self.assertEqual(promoted.returncode, 0, promoted.stderr)
            registry = (vault / "human-review" / "_pattern_registry.md").read_text(encoding="utf-8")
            self.assertIn("[stable] " + pattern, registry)
            self.assertIn("human=stable", registry)

    def test_semantic_search_finds_related_local_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "conversation.md"
            source.write_text(SAMPLE, encoding="utf-8")
            vault = tmp_path / "vault"
            ingest = self.run_cli(
                "ingest",
                "--project",
                "semantic-project",
                "--input",
                str(source),
                "--vault",
                str(vault),
            )
            self.assertEqual(ingest.returncode, 0, ingest.stderr)

            result = self.run_cli(
                "semantic-search",
                "--project",
                "semantic-project",
                "--vault",
                str(vault),
                "--query",
                "프로젝트를 이어가기 위한 기억",
                "--min-score",
                "0.01",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("similarity=", result.stdout)

    def test_export_share_excludes_raw_and_redacts_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            secret = "sk-" + "proj-" + ("abcdefghijklmnopqrstuvwxyz" + "123456")
            source = tmp_path / "conversation.md"
            source.write_text(f"보스: 원본에는 {secret} 이 있지만 공유본에서는 숨깁니다.\n", encoding="utf-8")
            vault = tmp_path / "vault"
            ingest = self.run_cli(
                "ingest",
                "--project",
                "share-project",
                "--input",
                str(source),
                "--vault",
                str(vault),
            )
            self.assertEqual(ingest.returncode, 0, ingest.stderr)
            output = tmp_path / "share.zip"

            exported = self.run_cli(
                "export-share",
                "--project",
                "share-project",
                "--vault",
                str(vault),
                "--output",
                str(output),
            )
            self.assertEqual(exported.returncode, 0, exported.stderr)
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                self.assertIn("SHARE_MANIFEST.md", names)
                self.assertFalse(any(name.endswith("01_raw_conversation.md") for name in names))
                for name in names:
                    data = archive.read(name).decode("utf-8")
                    self.assertNotIn(secret, data)

    @unittest.skipUnless(MEMORY_MODULE.__dict__.get("seal_payload"), "seal helpers unavailable")
    def test_seal_and_unseal_vault_roundtrip_when_crypto_is_available(self) -> None:
        try:
            import cryptography  # noqa: F401
        except ImportError:
            self.skipTest("cryptography is not installed")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "conversation.md"
            source.write_text(SAMPLE, encoding="utf-8")
            vault = tmp_path / "vault"
            ingest = self.run_cli(
                "ingest",
                "--project",
                "sealed-project",
                "--input",
                str(source),
                "--vault",
                str(vault),
            )
            self.assertEqual(ingest.returncode, 0, ingest.stderr)
            sealed = tmp_path / "memory.ppcm"
            unsealed = tmp_path / "memory.zip"
            env = {"PPCM_SEAL_PASSWORD": "correct horse battery staple"}

            seal = self.run_cli(
                "seal-vault",
                "--project",
                "sealed-project",
                "--vault",
                str(vault),
                "--output",
                str(sealed),
                env=env,
            )
            self.assertEqual(seal.returncode, 0, seal.stderr)
            self.assertTrue(sealed.read_bytes().startswith(b"PPCM-SEAL-v1\n"))

            unseal = self.run_cli(
                "unseal-vault",
                "--input",
                str(sealed),
                "--output",
                str(unsealed),
                env=env,
            )
            self.assertEqual(unseal.returncode, 0, unseal.stderr)
            with zipfile.ZipFile(unsealed) as archive:
                self.assertIn("SHARE_MANIFEST.md", archive.namelist())


if __name__ == "__main__":
    unittest.main()
