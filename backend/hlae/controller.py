"""HLAE and CS2 Process Supervisor and Lifecycle Manager.

Manages safe execution, timeout enforcement, output streaming, and cleanup
for Counter-Strike 2 launched under AfxHookSource2.
"""

from __future__ import annotations

import logging
import os
import pathlib
import subprocess
import time
from typing import Callable, Optional

from backend.hlae.version import HLAEVersionDetector

logger = logging.getLogger("demtoshka.hlae.controller")


class HLAEController:
    """Supervises HLAE execution and CS2 child process lifecycle."""

    def __init__(
        self,
        hlae_exe: pathlib.Path | str,
        hook_dll: pathlib.Path | str,
        cs2_exe: pathlib.Path | str,
    ) -> None:
        self.hlae_exe = pathlib.Path(hlae_exe)
        self.hook_dll = pathlib.Path(hook_dll)
        self.cs2_exe = pathlib.Path(cs2_exe)

    def check_prerequisites(self) -> tuple[bool, str]:
        """Validate that required binaries exist and meet compatibility criteria."""
        if not self.hlae_exe.exists():
            return False, f"HLAE executable not found at: {self.hlae_exe}"
        if not self.hook_dll.exists():
            return False, f"AfxHookSource2.dll not found at: {self.hook_dll}"
        if not self.cs2_exe.exists():
            return False, f"CS2 executable not found at: {self.cs2_exe}"

        caps = HLAEVersionDetector.detect(self.hlae_exe, self.hook_dll)
        if not caps.supports_source2:
            return False, f"Detected HLAE ({caps.hlae_version}) does not support Counter-Strike 2"

        return True, f"Prerequisites OK. HLAE {caps.hlae_version}, AfxHookSource2 {caps.hook_version}"

    def build_launch_args(self, cs2_cmdline: str) -> list[str]:
        """Build argument vector for launching HLAE in unattended automation mode."""
        return [
            str(self.hlae_exe.resolve()),
            "-customLoader",
            "-noGui",
            "-autoStart",
            "-hookDllPath",
            str(self.hook_dll.resolve()),
            "-programPath",
            str(self.cs2_exe.resolve()),
            "-cmdLine",
            cs2_cmdline.strip(),
        ]

    def is_cs2_running(self) -> bool:
        """Check if cs2.exe is actively executing in the current operating system."""
        try:
            res = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq cs2.exe", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=5.0,
                check=False,
            )
            return "cs2.exe" in res.stdout
        except Exception as exc:
            logger.warning("Failed to query tasklist for cs2.exe: %s", exc)
            return False

    def terminate_cs2(self) -> None:
        """Forcefully terminate orphaned CS2 processes."""
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "cs2.exe", "/T"],
                capture_output=True,
                timeout=10.0,
                check=False,
            )
            logger.info("Terminated existing cs2.exe processes")
        except Exception as exc:
            logger.warning("Error during taskkill of cs2.exe: %s", exc)

    def execute_recording_pass(
        self,
        cs2_cmdline: str,
        timeout_seconds: float = 300.0,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> tuple[bool, str]:
        """Launch and monitor an automated recording session until CS2 quits or times out.
        
        Returns:
            (success: bool, message: str)
        """
        ok, msg = self.check_prerequisites()
        if not ok:
            return False, msg

        cmd = self.build_launch_args(cs2_cmdline)
        logger.info("Launching HLAE command: %s", " ".join(cmd))

        hlae_proc = None
        try:
            hlae_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            start_time = time.time()
            cs2_seen = False
            last_ping = start_time

            while time.time() - start_time < timeout_seconds:
                cs2_active = self.is_cs2_running()

                if cs2_active:
                    cs2_seen = True

                # Progress heartbeats
                now = time.time()
                if now - last_ping >= 5.0:
                    last_ping = now
                    elapsed = int(now - start_time)
                    if progress_callback:
                        progress_callback(f"Recording active: {elapsed}s elapsed, cs2_active={cs2_active}")

                # If CS2 started and then exited cleanly, recording completed
                if cs2_seen and not cs2_active:
                    # Give short grace period for file handles to close
                    time.sleep(2.0)
                    logger.info("CS2 process completed recording pass successfully in %.1fs", now - start_time)
                    return True, "Recording pass finished cleanly"

                # Check if HLAE loader crashed prematurely before CS2 spawned
                if hlae_proc.poll() is not None and not cs2_seen and (time.time() - start_time > 15.0):
                    _, stderr = hlae_proc.communicate()
                    return False, f"HLAE process exited prematurely without launching CS2: {stderr.strip()}"

                time.sleep(1.0)

            # Timeout reached
            logger.error("Recording pass timed out after %s seconds", timeout_seconds)
            self.terminate_cs2()
            return False, f"Recording pass timed out after {timeout_seconds}s"

        except Exception as exc:
            logger.exception("Unexpected error executing HLAE pass")
            self.terminate_cs2()
            return False, f"Execution exception: {str(exc)}"
        finally:
            if hlae_proc and hlae_proc.poll() is None:
                try:
                    hlae_proc.terminate()
                except Exception:
                    pass
