"""Release migration guards and recovery; no GitHub requests are made."""
import copy
import unittest
from unittest.mock import patch

from scripts import release_packages as release


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(release, "RELEASE_ID", "123")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_build_token_cannot_own_the_publication(self):
        with patch.object(release, "api", return_value={"author": {"login": "github-actions[bot]"}, "draft": True}):
            with self.assertRaises(RuntimeError):
                release.draft()

    def test_existing_published_release_is_not_used_as_a_draft(self):
        with patch.object(release, "api", return_value={"author": {"login": "Chimpi-hackintosh"}, "draft": False}):
            with self.assertRaises(RuntimeError):
                release.draft()

    def test_missing_packages_prevent_any_retirement_of_the_current_release(self):
        with patch.object(release, "api", return_value={"author": {"login": "Chimpi-hackintosh"},
                         "draft": True, "assets": []}) as api:
            with self.assertRaises(RuntimeError):
                release.finalize()
            self.assertEqual(api.call_count, 1)

    def test_failed_swap_restores_the_previous_publication_and_tag(self):
        names = [f"ChimpiBridge-0.1.1-{n}" for n in (
            "windows-x64-portable.zip", "windows-x64.exe", "macos-arm64.zip", "macos-x64.zip")]
        names += [n + ".sha256" for n in names.copy()]
        current = {"id": 123, "author": {"login": "Chimpi-hackintosh"}, "draft": True,
                   "tag_name": "temporary", "target_commitish": "build",
                   "assets": [{"name": n, "state": "uploaded", "size": 1} for n in names]}
        old = {"id": 456, "author": {"login": "github-actions[bot]"}, "draft": False,
               "tag_name": "v0.1.1", "target_commitish": "old", "name": "Previous release"}
        ref = {"sha": "old"}
        failed = False

        def fake(path, method="GET", payload=None):
            nonlocal failed
            if method == "GET":
                if path.endswith("/git/ref/tags/v0.1.1"):
                    return {"object": dict(ref)}
                return copy.deepcopy(current if path.endswith("/releases/123") else old)
            if method == "POST":
                return {}
            if path.endswith("/releases/456"):
                old.update(payload)
            elif path.endswith("/releases/123"):
                if payload.get("tag_name") == "v0.1.1" and not failed:
                    failed = True
                    raise RuntimeError("Simulated final update failure")
                current.update(payload)
            elif path.endswith("/git/refs/tags/v0.1.1"):
                ref.update(sha=payload["sha"])
            return {}

        with patch.object(release, "api", side_effect=fake), patch.dict("os.environ", {"GITHUB_SHA": "new"}):
            with self.assertRaises(RuntimeError):
                release.finalize()
        self.assertFalse(old["draft"])
        self.assertEqual(old["tag_name"], "v0.1.1")
        self.assertEqual(ref["sha"], "old")
        self.assertTrue(current["draft"])


if __name__ == "__main__":
    unittest.main()
