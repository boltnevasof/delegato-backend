import asyncio
import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path

from loguru import logger

from app.core.config import settings
from app.core.constants import (
    ProvisioningTaskStatus,
    ProvisioningTaskType,
    ServerLogLevel,
    ServerStatus,
)
from app.repositories.agent import AgentRepository
from app.repositories.agent_channel import AgentChannelRepository
from app.repositories.agent_skill import AgentSkillRepository
from app.repositories.agent_tool import AgentToolRepository
from app.repositories.provisioning import ProvisioningTaskRepository
from app.repositories.server import ServerRepository
from app.repositories.server_log import ServerLogRepository


class ProvisioningService:
    def __init__(
        self,
        server_repository: ServerRepository,
        server_log_repository: ServerLogRepository,
        provisioning_repository: ProvisioningTaskRepository,
        agent_repository: AgentRepository,
        agent_skill_repository: AgentSkillRepository,
        agent_tool_repository: AgentToolRepository,
        agent_channel_repository: AgentChannelRepository,
    ) -> None:
        self._server_repo = server_repository
        self._log_repo = server_log_repository
        self._provisioning_repo = provisioning_repository
        self._agent_repo = agent_repository
        self._agent_skill_repo = agent_skill_repository
        self._agent_tool_repo = agent_tool_repository
        self._agent_channel_repo = agent_channel_repository

    async def start_provisioning(self, server_id: uuid.UUID) -> str:
        task = await self._provisioning_repo.create(
            server_id=server_id,
            task_type=ProvisioningTaskType.PROVISION,
        )
        await self._log_step(
            server_id, ServerLogLevel.INFO, "provisioning",
            "Provisioning task created",
        )
        return str(task.id)

    # ------------------------------------------------------------------
    # Terraform
    # ------------------------------------------------------------------

    async def run_terraform(self, server_id: uuid.UUID) -> str | None:
        """Create VPS via Terraform. Returns IP address or None on failure.

        Each run copies terraform files into an isolated tmpdir to allow
        parallel provisioning of multiple servers.
        Secrets are passed via TF_VAR_* environment variables, never CLI flags.
        """
        await self._log_step(
            server_id, ServerLogLevel.INFO, "terraform",
            "Starting Terraform VPS creation",
        )

        tf_source = Path(settings.INFRASTRUCTURE_DIR) / "terraform"
        tmpdir = tempfile.mkdtemp(prefix=f"tf-server-{server_id}-")

        try:
            # Copy terraform config files into isolated tmpdir
            for item in tf_source.iterdir():
                if item.name == "states" or item.name.startswith("."):
                    continue
                dest = Path(tmpdir) / item.name
                if item.is_file():
                    shutil.copy2(item, dest)

            tf_env = self._terraform_env()

            # terraform init with per-server state key
            init_cmd = [
                "terraform", "init", "-reconfigure", "-input=false",
                f"-backend-config=bucket={settings.TERRAFORM_STATE_BUCKET}",
                f"-backend-config=key=states/server-{server_id}.tfstate",
                f"-backend-config=endpoint={settings.TERRAFORM_STATE_ENDPOINT}",
                f"-backend-config=access_key={settings.TERRAFORM_STATE_ACCESS_KEY}",
                f"-backend-config=secret_key={settings.TERRAFORM_STATE_SECRET_KEY}",
                "-backend-config=region=ru-1",
            ]
            rc, stdout, stderr = await self._run_subprocess(
                init_cmd, cwd=tmpdir, env=tf_env,
            )
            await self._log_step(
                server_id, ServerLogLevel.INFO, "terraform",
                "terraform init completed", {"stdout": stdout, "stderr": stderr},
            )
            if rc != 0:
                await self._log_step(
                    server_id, ServerLogLevel.ERROR, "terraform",
                    f"terraform init failed (exit {rc})", {"stderr": stderr},
                )
                return None

            # terraform apply
            apply_env = {
                **tf_env,
                "TF_VAR_server_name": f"delegato-server-{server_id}",
                "TF_VAR_ssh_private_key_path": settings.SSH_PRIVATE_KEY_PATH,
            }
            apply_cmd = ["terraform", "apply", "-auto-approve", "-input=false"]
            rc, stdout, stderr = await self._run_subprocess(
                apply_cmd, cwd=tmpdir, env=apply_env,
            )
            await self._log_step(
                server_id, ServerLogLevel.INFO, "terraform",
                "terraform apply completed", {"stdout": stdout, "stderr": stderr},
            )
            if rc != 0:
                await self._log_step(
                    server_id, ServerLogLevel.ERROR, "terraform",
                    f"terraform apply failed (exit {rc})", {"stderr": stderr},
                )
                return None

            # terraform output
            rc, stdout, stderr = await self._run_subprocess(
                ["terraform", "output", "-json"], cwd=tmpdir, env=tf_env,
            )
            if rc != 0:
                await self._log_step(
                    server_id, ServerLogLevel.ERROR, "terraform",
                    "terraform output failed", {"stderr": stderr},
                )
                return None

            outputs = json.loads(stdout)
            ip_address = outputs.get("server_ip", {}).get("value")
            provider_id = outputs.get("server_id", {}).get("value")

            if not ip_address:
                await self._log_step(
                    server_id, ServerLogLevel.ERROR, "terraform",
                    "No server_ip in terraform output", {"raw_output": stdout},
                )
                return None

            # Persist results
            await self._server_repo.update(
                server_id,
                status=ServerStatus.CONFIGURING,
                ip_address=ip_address,
                provider_id=provider_id,
                tfstate_path=f"states/server-{server_id}.tfstate",
            )
            await self._log_step(
                server_id, ServerLogLevel.INFO, "terraform",
                f"VPS created, IP: {ip_address}, provider_id: {provider_id}",
            )

            # Cleanup tmpdir on success
            shutil.rmtree(tmpdir, ignore_errors=True)
            return ip_address

        except Exception as e:
            await self._log_step(
                server_id, ServerLogLevel.ERROR, "terraform",
                f"Terraform exception: {e}",
                {"tmpdir": tmpdir, "hint": "tmpdir preserved for debugging"},
            )
            return None

    # ------------------------------------------------------------------
    # Ansible
    # ------------------------------------------------------------------

    async def run_ansible(self, server_id: uuid.UUID) -> bool:
        """Configure server with Docker + OpenClaw via Ansible."""
        await self._log_step(
            server_id, ServerLogLevel.INFO, "ansible",
            "Starting Ansible configuration",
        )

        server = await self._server_repo.get_by_id(server_id)
        if not server or not server.ip_address:
            await self._log_step(
                server_id, ServerLogLevel.ERROR, "ansible",
                "Server not found or missing IP address",
            )
            return False

        extra_vars = await self._build_extra_vars(server.agent_id)
        ansible_dir = str(Path(settings.INFRASTRUCTURE_DIR) / "ansible")

        inventory_path = None
        extravars_path = None
        try:
            # Write temporary inventory file
            inventory_fd = tempfile.NamedTemporaryFile(
                mode="w", suffix=".ini", prefix="ansible-inv-", delete=False,
            )
            inventory_fd.write(
                f"[openclaw_servers]\n"
                f"{server.ip_address} ansible_user=root "
                f"ansible_ssh_private_key_file={settings.SSH_PRIVATE_KEY_PATH}\n"
            )
            inventory_fd.close()
            inventory_path = inventory_fd.name

            # Write temporary extra-vars JSON file
            extravars_fd = tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", prefix="ansible-vars-", delete=False,
            )
            json.dump(extra_vars, extravars_fd, ensure_ascii=False)
            extravars_fd.close()
            extravars_path = extravars_fd.name

            cmd = [
                "ansible-playbook",
                "-i", inventory_path,
                f"--extra-vars=@{extravars_path}",
                "site.yml",
            ]
            ansible_env = self._ssh_agent_env()
            rc, stdout, stderr = await self._run_subprocess(
                cmd, cwd=ansible_dir, env=ansible_env,
            )
            await self._log_step(
                server_id, ServerLogLevel.INFO, "ansible",
                "ansible-playbook site.yml completed",
                {"stdout": stdout, "stderr": stderr},
            )

            if rc != 0:
                await self._log_step(
                    server_id, ServerLogLevel.ERROR, "ansible",
                    f"ansible-playbook failed (exit {rc})",
                    {"stderr": stderr, "hint": "temp files preserved for debugging"},
                )
                return False

            await self._server_repo.update_status(server_id, ServerStatus.ACTIVE)
            await self._log_step(
                server_id, ServerLogLevel.INFO, "ansible",
                "Server configured and active",
            )

            # Cleanup temp files on success
            self._safe_unlink(inventory_path)
            self._safe_unlink(extravars_path)
            return True

        except Exception as e:
            await self._log_step(
                server_id, ServerLogLevel.ERROR, "ansible",
                f"Ansible exception: {e}",
                {"hint": "temp files preserved for debugging"},
            )
            return False

    async def run_config_update(self, server_id: uuid.UUID) -> bool:
        """Update agent config on running server via Ansible."""
        await self._log_step(
            server_id, ServerLogLevel.INFO, "ansible",
            "Starting agent config update",
        )

        server = await self._server_repo.get_by_id(server_id)
        if not server or not server.ip_address:
            await self._log_step(
                server_id, ServerLogLevel.ERROR, "ansible",
                "Server not found or missing IP address",
            )
            return False

        extra_vars = await self._build_extra_vars(server.agent_id)
        ansible_dir = str(Path(settings.INFRASTRUCTURE_DIR) / "ansible")

        inventory_path = None
        extravars_path = None
        try:
            inventory_fd = tempfile.NamedTemporaryFile(
                mode="w", suffix=".ini", prefix="ansible-inv-", delete=False,
            )
            inventory_fd.write(
                f"[openclaw_servers]\n"
                f"{server.ip_address} ansible_user=root "
                f"ansible_ssh_private_key_file={settings.SSH_PRIVATE_KEY_PATH}\n"
            )
            inventory_fd.close()
            inventory_path = inventory_fd.name

            extravars_fd = tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", prefix="ansible-vars-", delete=False,
            )
            json.dump(extra_vars, extravars_fd, ensure_ascii=False)
            extravars_fd.close()
            extravars_path = extravars_fd.name

            cmd = [
                "ansible-playbook",
                "-i", inventory_path,
                f"--extra-vars=@{extravars_path}",
                "update_agent_config.yml",
            ]
            ansible_env = self._ssh_agent_env()
            rc, stdout, stderr = await self._run_subprocess(
                cmd, cwd=ansible_dir, env=ansible_env,
            )
            await self._log_step(
                server_id, ServerLogLevel.INFO, "ansible",
                "ansible-playbook update_agent_config.yml completed",
                {"stdout": stdout, "stderr": stderr},
            )

            if rc != 0:
                await self._log_step(
                    server_id, ServerLogLevel.ERROR, "ansible",
                    f"Config update failed (exit {rc})", {"stderr": stderr},
                )
                return False

            await self._log_step(
                server_id, ServerLogLevel.INFO, "ansible",
                "Agent config updated",
            )

            self._safe_unlink(inventory_path)
            self._safe_unlink(extravars_path)
            return True

        except Exception as e:
            await self._log_step(
                server_id, ServerLogLevel.ERROR, "ansible",
                f"Config update exception: {e}",
            )
            return False

    # ------------------------------------------------------------------
    # Destroy / Rollback
    # ------------------------------------------------------------------

    async def destroy_server(self, server_id: uuid.UUID) -> bool:
        """Destroy VPS via terraform destroy. Called when Ansible fails after max retries."""
        await self._log_step(
            server_id, ServerLogLevel.WARNING, "terraform",
            "Starting terraform destroy (rollback after provisioning failure)",
        )

        tf_source = Path(settings.INFRASTRUCTURE_DIR) / "terraform"
        tmpdir = tempfile.mkdtemp(prefix=f"tf-destroy-{server_id}-")

        try:
            for item in tf_source.iterdir():
                if item.name == "states" or item.name.startswith("."):
                    continue
                dest = Path(tmpdir) / item.name
                if item.is_file():
                    shutil.copy2(item, dest)

            tf_env = self._terraform_env()

            # Init with same state key
            init_cmd = [
                "terraform", "init", "-reconfigure", "-input=false",
                f"-backend-config=bucket={settings.TERRAFORM_STATE_BUCKET}",
                f"-backend-config=key=states/server-{server_id}.tfstate",
                f"-backend-config=endpoint={settings.TERRAFORM_STATE_ENDPOINT}",
                f"-backend-config=access_key={settings.TERRAFORM_STATE_ACCESS_KEY}",
                f"-backend-config=secret_key={settings.TERRAFORM_STATE_SECRET_KEY}",
                "-backend-config=region=ru-1",
            ]
            rc, stdout, stderr = await self._run_subprocess(
                init_cmd, cwd=tmpdir, env=tf_env,
            )
            if rc != 0:
                await self._log_step(
                    server_id, ServerLogLevel.ERROR, "terraform",
                    f"terraform init for destroy failed (exit {rc})",
                    {"stderr": stderr},
                )
                return False

            # Destroy
            destroy_env = {
                **tf_env,
                "TF_VAR_server_name": f"delegato-server-{server_id}",
                "TF_VAR_ssh_private_key_path": settings.SSH_PRIVATE_KEY_PATH,
            }
            rc, stdout, stderr = await self._run_subprocess(
                ["terraform", "destroy", "-auto-approve", "-input=false"],
                cwd=tmpdir, env=destroy_env,
            )
            await self._log_step(
                server_id, ServerLogLevel.INFO, "terraform",
                "terraform destroy completed",
                {"stdout": stdout, "stderr": stderr},
            )

            if rc != 0:
                await self._log_step(
                    server_id, ServerLogLevel.ERROR, "terraform",
                    f"terraform destroy failed (exit {rc})", {"stderr": stderr},
                )
                return False

            await self._server_repo.update_status(server_id, ServerStatus.DESTROYED)
            await self._log_step(
                server_id, ServerLogLevel.WARNING, "terraform",
                "Server destroyed after provisioning failure",
            )

            shutil.rmtree(tmpdir, ignore_errors=True)
            return True

        except Exception as e:
            await self._log_step(
                server_id, ServerLogLevel.ERROR, "terraform",
                f"Destroy exception: {e}",
                {"tmpdir": tmpdir, "hint": "tmpdir preserved for debugging"},
            )
            return False

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    async def mark_error(self, server_id: uuid.UUID, error: str) -> None:
        await self._server_repo.update_status(server_id, ServerStatus.ERROR)
        await self._log_step(
            server_id, ServerLogLevel.ERROR, "provisioning",
            f"Provisioning failed: {error}",
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _terraform_env(self) -> dict[str, str]:
        """Build environment dict with TF_VAR_* secrets."""
        return {
            "TF_VAR_twc_token": settings.TIMEWEB_API_TOKEN,
            "TF_VAR_availability_zone": settings.TIMEWEB_AVAILABILITY_ZONE,
            "TF_VAR_twc_ssh_key_id": settings.TIMEWEB_SSH_KEY_ID,
            "TF_VAR_preset_cpu": str(settings.TIMEWEB_PRESET_CPU),
            "TF_VAR_preset_ram": str(settings.TIMEWEB_PRESET_RAM),
        }

    async def _build_extra_vars(self, agent_id: uuid.UUID) -> dict:
        """Build Ansible extra-vars from agent data."""
        agent = await self._agent_repo.get_by_id(agent_id)
        skills = await self._agent_skill_repo.get_by_agent_id(agent_id)
        tools = await self._agent_tool_repo.get_by_agent_id(agent_id)
        channels = await self._agent_channel_repo.get_by_agent_id(agent_id)

        return {
            "agent_soul_md": agent.soul_md or "" if agent else "",
            "agent_agent_md": agent.agent_md or "" if agent else "",
            "agent_skills": [
                {
                    "id": str(s.skill_id),
                    "is_enabled": s.is_enabled,
                }
                for s in skills
            ],
            "agent_tools": [
                {
                    "id": str(t.tool_id),
                    "is_enabled": t.is_enabled,
                    "config": t.config,
                }
                for t in tools
            ],
            "agent_channels": [
                {
                    "id": str(c.id),
                    "channel_type": c.channel_type.value,
                    "channel_config": c.channel_config,
                    "status": c.status.value,
                }
                for c in channels
            ],
            "claude_api_key": settings.CLAUDE_API_KEY,
            "openai_api_key": settings.OPENAI_API_KEY,
            "openclaw_image": settings.OPENCLAW_DOCKER_IMAGE,
        }

    @staticmethod
    def _ssh_agent_env() -> dict[str, str]:
        """Build env vars for SSH key passphrase support via SSH_ASKPASS."""
        env: dict[str, str] = {}
        if settings.SSH_PASSPHRASE:
            askpass_script = tempfile.NamedTemporaryFile(
                mode="w", suffix=".sh", prefix="ssh-askpass-",
                delete=False,
            )
            askpass_script.write(f"#!/bin/sh\necho '{settings.SSH_PASSPHRASE}'\n")
            askpass_script.close()
            os.chmod(askpass_script.name, 0o700)
            env["SSH_ASKPASS"] = askpass_script.name
            env["SSH_ASKPASS_REQUIRE"] = "force"
            env["DISPLAY"] = ""
        return env

    async def _run_subprocess(
        self,
        cmd: list[str],
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> tuple[int, str, str]:
        """Run an async subprocess, return (returncode, stdout, stderr)."""
        full_env = {**os.environ, **(env or {})}
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=full_env,
        )
        stdout_bytes, stderr_bytes = await proc.communicate()
        return (
            proc.returncode or 0,
            stdout_bytes.decode(errors="replace"),
            stderr_bytes.decode(errors="replace"),
        )

    @staticmethod
    def _safe_unlink(path: str | None) -> None:
        """Remove a file silently, ignoring errors."""
        if path:
            try:
                os.unlink(path)
            except OSError:
                pass

    async def _log_step(
        self,
        server_id: uuid.UUID,
        level: ServerLogLevel,
        stage: str,
        message: str,
        details: dict | None = None,
    ) -> None:
        await self._log_repo.create(
            server_id=server_id, level=level, stage=stage,
            message=message, details=details,
        )
        logger.info(
            "Server {server_id} [{stage}]: {message}",
            server_id=server_id, stage=stage, message=message,
        )
