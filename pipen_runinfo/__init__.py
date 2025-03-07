from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, List
from pathlib import Path

from yunpath import CloudPath
from pipen import plugin

from .version import __version__
from .session_info import get_inject_session_code_fun

if TYPE_CHECKING:  # pragma: no cover
    from pipen import Proc, Pipen
    from pipen.job import Job


def _get_lang(langpath: str | List[str]):
    if isinstance(langpath, list):
        langpath = langpath[0]

    stem = Path(langpath).stem if langpath else "bash"
    # Might be python3, python3.7, python3.7m, etc.
    if stem.startswith("python"):
        return "python"

    if stem in ("Rscript", "R") or stem.startswith("Rscript") or stem.startswith("R-"):
        return "R"

    if stem.startswith("bash"):
        return "bash"

    if stem.startswith("fish"):
        return "fish"

    return stem


class PipenRuninfoPlugin:
    name = "runinfo"
    version = __version__
    priority = 998

    @plugin.impl
    async def on_init(pipen: Pipen):
        """Called when the pipeline is initialized."""
        # Whether to include module path in the runinfo (for python only)
        # Either pipeline-level option or process-level option
        pipen.config.plugin_opts.setdefault("runinfo_path", True)
        # Whether to include submodules in the runinfo (for python only)
        # Either pipeline-level option or process-level option
        pipen.config.plugin_opts.setdefault("runinfo_submod", False)
        # Specify the lang directly instead of inferring from the proc.lang
        # Process-level option
        pipen.config.plugin_opts.setdefault("runinfo_lang", None)

    @plugin.impl
    def on_proc_script_computed(proc: Proc):
        """Called when a process is initialized.

        Try to modify the script so that we can get the runinfo.
        """
        pipeline_plugin_opts = proc.pipeline.config.get("plugin_opts", None) or {}
        proc_plugin_opts = proc.plugin_opts or {}
        runinfo_path = proc_plugin_opts.get(
            "runinfo_path",
            pipeline_plugin_opts.get("runinfo_path", True),
        )
        runinfo_submod = proc_plugin_opts.get(
            "runinfo_submod",
            pipeline_plugin_opts.get("runinfo_submod", False),
        )
        runinfo_lang = proc_plugin_opts.get(
            "runinfo_lang",
            pipeline_plugin_opts.get("runinfo_lang", None),
        )
        if not runinfo_lang:
            langpath = proc.lang
            runinfo_lang = _get_lang(langpath)

        if proc.script is None:  # pragma: no cover
            return

        inject_session_code_fun = get_inject_session_code_fun(runinfo_lang)
        if inject_session_code_fun is None:  # pragma: no cover
            return

        proc.script = inject_session_code_fun(
            proc.script,
            show_path=runinfo_path,
            include_submodule=runinfo_submod,
        )

    @plugin.impl
    def on_jobcmd_init(job: Job) -> str:
        if isinstance(job.metadir.mounted, CloudPath):  # pragma: no cover
            return textwrap.dedent(
                f"""
                # plugin: runinfo
                runinfo_device_orig="{job.metadir.mounted}/job.runinfo.device"
                runinfo_device=$(mktemp)
                runinfo_time_orig="{job.metadir.mounted}/job.runinfo.time"
                runinfo_time=$(mktemp)
                """
            )

        else:
            return textwrap.dedent(
                f"""
                # plugin: runinfo
                runinfo_device="{job.metadir.mounted}/job.runinfo.device"
                runinfo_time="{job.metadir.mounted}/job.runinfo.time"
                """
            )

    @plugin.impl
    def on_jobcmd_prep(job: Job) -> str:
        return textwrap.dedent(
            r"""
            # plugin: runinfo
            if env time -V &>/dev/null; then
                cmd="env time \
                    -f '# Generated by pipen-runinfo v%(version)s\n\n\
Command: %%C\n\
Voluntary context switches: %%w\n\
Involuntary context switches: %%c\n\
Percentage of CPU this job got: %%P\n\
Major page faults: %%F\n\
Minor page faults: %%R\n\
Maximum resident set size (kB): %%M\n\
Elapsed real time (s): %%e\n\
System (kernel) time (s): %%S\n\
User time (s): %%U\n\
Exit status: %%x' \
                    -o $runinfo_time $cmd"
            else
                echo "GNU time is not available, job is not timed." > $runinfo_time
                echo "See: https://www.gnu.org/software/time/" >> $runinfo_time
            fi
            """ % {"version": __version__}
        )

    @plugin.impl
    def on_jobcmd_end(job: Job) -> str:
        return textwrap.dedent(
            """        # plugin: runinfo

            echo "# Generated by pipen-runinfo v%(version)s" > $runinfo_device
            # shellcheck disable=SC2129
            echo "" >> $runinfo_device
            echo "Scheduler" >> $runinfo_device
            echo "---------" >> $runinfo_device
            echo "%(scheduler)s" >> $runinfo_device
            echo "" >> $runinfo_device
            echo "Hostname" >> $runinfo_device
            echo "--------" >> $runinfo_device
            hostname >> $runinfo_device
            echo "" >> $runinfo_device
            echo "CPU" >> $runinfo_device
            echo "----" >> $runinfo_device
            lscpu >> $runinfo_device
            echo "" >> $runinfo_device
            echo "Memory" >> $runinfo_device
            echo "------" >> $runinfo_device
            free -h >> $runinfo_device
            echo "" >> $runinfo_device
            echo "Disk" >> $runinfo_device
            echo "----" >> $runinfo_device
            df -h >> $runinfo_device
            echo "" >> $runinfo_device
            echo "Network" >> $runinfo_device
            echo "-------" >> $runinfo_device
            if ifconfig --version &>/dev/null; then
                ifconfig >> $runinfo_device
            else
                if ip -V &>/dev/null; then
                    ip a >> $runinfo_device
                else
                    echo "Neither ifconfig nor ip is available." >> $runinfo_device
                fi
            fi
            # shellcheck disable=SC2129
            echo "" >> $runinfo_device
            echo "GPU" >> $runinfo_device
            echo "---" >> $runinfo_device
            if nvidia-smi --version &>/dev/null; then
                nvidia-smi >> $runinfo_device
            else
                echo "nvidia-smi is not available." >> $runinfo_device
            fi
            echo "" >> $runinfo_device

            if [[ -v runinfo_device_orig ]]; then
                cloudsh mv $runinfo_device $runinfo_device_orig
                cloudsh mv $runinfo_time $runinfo_time_orig
            fi
            """ % {"scheduler": job.proc.scheduler.name, "version": __version__}
        )
