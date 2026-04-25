import tempfile
import time
import unittest
from pathlib import Path
import os

from fastapi.testclient import TestClient

from apps.api.config import AppConfig
from apps.api.main import build_service, create_app


class RelayApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        database_path = Path(self.tempdir.name) / "relay-test.db"
        config = AppConfig(
            database_path=database_path,
            default_rtmp_base_url="rtmp://localhost:1935/live",
            ffmpeg_bin="ffmpeg",
            ffmpeg_loglevel="info",
            ffmpeg_extra_args="",
            runtime_log_dir=Path(self.tempdir.name) / "logs",
            relay_command_template="/bin/sh -c 'sleep 30'",
            max_retry_count=3,
            retry_delay_seconds=0.05,
        )
        self.app = create_app(service=build_service(config))
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.client.close()
        self.tempdir.cleanup()

    def test_source_crud_and_masked_url(self) -> None:
        create_payload = {
            "name": "Camera 01",
            "source_url": "rtsp://admin:secret@10.0.0.8:554/stream",
            "stream_key": "cam-01",
            "enabled": True,
            "transcode_mode": "copy",
        }

        create_response = self.client.post("/api/v1/sources", json=create_payload)
        self.assertEqual(create_response.status_code, 201)
        created = create_response.json()
        self.assertEqual(created["name"], "Camera 01")
        self.assertEqual(created["source_url_masked"], "rtsp://admin:***@10.0.0.8:554/stream")
        self.assertEqual(created["target_id"], "default")

        list_response = self.client.get("/api/v1/sources")
        self.assertEqual(list_response.status_code, 200)
        listed = list_response.json()
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["id"], created["id"])

        update_payload = {
            "name": "Camera 01 Updated",
            "source_url": "rtsp://viewer:new-pass@10.0.0.8:554/stream",
            "stream_key": "cam-01-updated",
            "enabled": False,
            "transcode_mode": "transcode",
        }
        update_response = self.client.put(
            f"/api/v1/sources/{created['id']}",
            json=update_payload,
        )
        self.assertEqual(update_response.status_code, 200)
        updated = update_response.json()
        self.assertEqual(updated["name"], "Camera 01 Updated")
        self.assertEqual(updated["transcode_mode"], "transcode")
        self.assertEqual(updated["source_url_masked"], "rtsp://viewer:***@10.0.0.8:554/stream")

        delete_response = self.client.delete(f"/api/v1/sources/{created['id']}")
        self.assertEqual(delete_response.status_code, 204)

        missing_response = self.client.get(f"/api/v1/jobs/{created['id']}/status")
        self.assertEqual(missing_response.status_code, 404)

    def test_job_start_stop_status(self) -> None:
        create_response = self.client.post(
            "/api/v1/sources",
            json={
                "name": "Camera 02",
                "source_url": "rtsp://10.0.0.9/live",
                "stream_key": "cam-02",
                "enabled": True,
                "transcode_mode": "copy",
            },
        )
        source_id = create_response.json()["id"]

        initial_status = self.client.get(f"/api/v1/jobs/{source_id}/status")
        self.assertEqual(initial_status.status_code, 200)
        self.assertEqual(initial_status.json()["status"], "stopped")

        start_response = self.client.post(f"/api/v1/jobs/{source_id}/start")
        self.assertEqual(start_response.status_code, 200)
        started = start_response.json()
        self.assertEqual(started["status"], "running")
        self.assertIsNotNone(started["started_at"])

        running_status = self.client.get(f"/api/v1/jobs/{source_id}/status")
        self.assertEqual(running_status.status_code, 200)
        self.assertEqual(running_status.json()["status"], "running")

        stop_response = self.client.post(f"/api/v1/jobs/{source_id}/stop")
        self.assertEqual(stop_response.status_code, 200)
        self.assertEqual(stop_response.json()["status"], "stopped")

        restart_response = self.client.post(f"/api/v1/jobs/{source_id}/restart")
        self.assertEqual(restart_response.status_code, 200)
        self.assertEqual(restart_response.json()["status"], "running")
        self.assertIsNotNone(restart_response.json()["pid"])

        final_stop_response = self.client.post(f"/api/v1/jobs/{source_id}/stop")
        self.assertEqual(final_stop_response.status_code, 200)

    def test_target_crud_and_job_uses_custom_target(self) -> None:
        list_response = self.client.get("/api/v1/targets")
        self.assertEqual(list_response.status_code, 200)
        default_target = list_response.json()[0]
        self.assertEqual(default_target["id"], "default")
        self.assertTrue(default_target["is_default"])

        create_target = self.client.post(
            "/api/v1/targets",
            json={
                "name": "Edge SRS",
                "rtmp_base_url": "rtmp://10.0.0.20:1935/live",
                "is_default": True,
            },
        )
        self.assertEqual(create_target.status_code, 201)
        created_target = create_target.json()
        self.assertTrue(created_target["is_default"])

        refreshed_targets = self.client.get("/api/v1/targets").json()
        refreshed_default = [item for item in refreshed_targets if item["is_default"]]
        self.assertEqual(len(refreshed_default), 1)
        self.assertEqual(refreshed_default[0]["id"], created_target["id"])

        source_response = self.client.post(
            "/api/v1/sources",
            json={
                "name": "Camera 03",
                "source_url": "rtsp://10.0.0.7/live",
                "stream_key": "cam-03",
                "enabled": True,
                "transcode_mode": "copy",
            },
        )
        self.assertEqual(source_response.status_code, 201)
        source_id = source_response.json()["id"]
        self.assertEqual(source_response.json()["target_id"], created_target["id"])

        start_response = self.client.post(f"/api/v1/jobs/{source_id}/start")
        self.assertEqual(start_response.status_code, 200)
        self.assertEqual(start_response.json()["status"], "running")
        self.assertIsNotNone(start_response.json()["pid"])

        delete_default = self.client.delete(f"/api/v1/targets/{created_target['id']}")
        self.assertEqual(delete_default.status_code, 404)

        restore_default = self.client.put(
            "/api/v1/targets/default",
            json={
                "name": "Default SRS",
                "rtmp_base_url": "rtmp://localhost:1935/live",
                "is_default": True,
            },
        )
        self.assertEqual(restore_default.status_code, 200)

        delete_custom = self.client.delete(f"/api/v1/targets/{created_target['id']}")
        self.assertEqual(delete_custom.status_code, 204)

    def test_enabled_sources_recover_on_service_restart(self) -> None:
        create_response = self.client.post(
            "/api/v1/sources",
            json={
                "name": "Camera 04",
                "source_url": "rtsp://10.0.0.12/live",
                "stream_key": "cam-04",
                "enabled": True,
                "transcode_mode": "copy",
            },
        )
        self.assertEqual(create_response.status_code, 201)
        source_id = create_response.json()["id"]

        restarted_app = create_app(
            service=build_service(
                AppConfig(
                    database_path=Path(self.tempdir.name) / "relay-test.db",
                    default_rtmp_base_url="rtmp://localhost:1935/live",
                    ffmpeg_bin="ffmpeg",
                    ffmpeg_loglevel="info",
                    ffmpeg_extra_args="",
                    runtime_log_dir=Path(self.tempdir.name) / "logs",
                    relay_command_template="/bin/sh -c 'sleep 30'",
                    max_retry_count=3,
                    retry_delay_seconds=0.05,
                )
            )
        )
        restarted_client = TestClient(restarted_app)

        status_response = restarted_client.get(f"/api/v1/jobs/{source_id}/status")
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()["status"], "running")
        self.assertIsNotNone(status_response.json()["pid"])

        stop_response = restarted_client.post(f"/api/v1/jobs/{source_id}/stop")
        self.assertEqual(stop_response.status_code, 200)
        restarted_client.close()

    def test_job_logs_are_available_and_sanitized(self) -> None:
        create_response = self.client.post(
            "/api/v1/sources",
            json={
                "name": "Camera 05",
                "source_url": "rtsp://operator:secret-pass@10.0.0.15/live",
                "stream_key": "cam-05",
                "enabled": False,
                "transcode_mode": "copy",
            },
        )
        self.assertEqual(create_response.status_code, 201)
        source_id = create_response.json()["id"]

        log_path = Path(self.tempdir.name) / "logs" / f"{source_id}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(
            "\n".join(
                [
                    "opening input rtsp://operator:secret-pass@10.0.0.15/live",
                    "stream failed",
                ]
            ),
            encoding="utf-8",
        )

        logs_response = self.client.get(f"/api/v1/jobs/{source_id}/logs")
        self.assertEqual(logs_response.status_code, 200)
        body = logs_response.json()
        self.assertEqual(body["source_id"], source_id)
        self.assertIn("rtsp://operator:***@10.0.0.15/live", body["logs"])
        self.assertNotIn("secret-pass", body["logs"])

    def test_source_detail_aggregates_target_job_and_logs(self) -> None:
        target_response = self.client.post(
            "/api/v1/targets",
            json={
                "name": "Detail SRS",
                "rtmp_base_url": "rtmp://10.0.0.21:1935/live",
                "is_default": True,
            },
        )
        self.assertEqual(target_response.status_code, 201)
        target_id = target_response.json()["id"]

        source_response = self.client.post(
            "/api/v1/sources",
            json={
                "name": "Camera Detail",
                "source_url": "rtsp://viewer:secret@10.0.0.22/live",
                "stream_key": "cam-detail",
                "enabled": False,
                "transcode_mode": "copy",
            },
        )
        self.assertEqual(source_response.status_code, 201)
        source_id = source_response.json()["id"]

        self.client.post(f"/api/v1/jobs/{source_id}/start")
        log_path = Path(self.tempdir.name) / "logs" / f"{source_id}.log"
        log_path.write_text(
            "input rtsp://viewer:secret@10.0.0.22/live\nrelay running\n",
            encoding="utf-8",
        )

        detail_response = self.client.get(f"/api/v1/sources/{source_id}")
        self.assertEqual(detail_response.status_code, 200)
        body = detail_response.json()
        self.assertEqual(body["source"]["id"], source_id)
        self.assertEqual(body["target"]["id"], target_id)
        self.assertEqual(body["job"]["status"], "running")
        self.assertIn("rtsp://viewer:***@10.0.0.22/live", body["recent_logs"])
        self.assertNotIn("secret", body["recent_logs"])

        stop_response = self.client.post(f"/api/v1/jobs/{source_id}/stop")
        self.assertEqual(stop_response.status_code, 200)

    def test_job_auto_retries_after_failure(self) -> None:
        retry_script = Path(self.tempdir.name) / "retry-once.sh"
        retry_script.write_text(
            "\n".join(
                [
                    "#!/bin/sh",
                    "FLAG=\"$1\"",
                    "if [ ! -f \"$FLAG\" ]; then",
                    "  touch \"$FLAG\"",
                    "  exit 2",
                    "fi",
                    "sleep 30",
                ]
            ),
            encoding="utf-8",
        )
        os.chmod(retry_script, 0o755)

        retry_app = create_app(
            service=build_service(
                AppConfig(
                    database_path=Path(self.tempdir.name) / "relay-retry.db",
                    default_rtmp_base_url="rtmp://localhost:1935/live",
                    ffmpeg_bin="ffmpeg",
                    ffmpeg_loglevel="info",
                    ffmpeg_extra_args="",
                    runtime_log_dir=Path(self.tempdir.name) / "retry-logs",
                    relay_command_template=f"{retry_script} {self.tempdir.name}/{{source_id}}.flag",
                    max_retry_count=1,
                    retry_delay_seconds=0.05,
                )
            )
        )
        retry_client = TestClient(retry_app)

        create_response = retry_client.post(
            "/api/v1/sources",
            json={
                "name": "Camera Retry",
                "source_url": "10.0.0.18/live",
                "stream_key": "cam-retry",
                "enabled": False,
                "transcode_mode": "copy",
            },
        )
        self.assertEqual(create_response.status_code, 201)
        source_id = create_response.json()["id"]

        start_response = retry_client.post(f"/api/v1/jobs/{source_id}/start")
        self.assertEqual(start_response.status_code, 200)
        running_status = None
        try:
            for _ in range(20):
                status_response = retry_client.get(f"/api/v1/jobs/{source_id}/status")
                self.assertEqual(status_response.status_code, 200)
                body = status_response.json()
                if body["status"] == "running" and body["retry_count"] == 1:
                    running_status = body
                    break
                time.sleep(0.05)

            self.assertIsNotNone(running_status)
        finally:
            stop_response = retry_client.post(f"/api/v1/jobs/{source_id}/stop")
            self.assertEqual(stop_response.status_code, 200)
            retry_client.close()


if __name__ == "__main__":
    unittest.main()
