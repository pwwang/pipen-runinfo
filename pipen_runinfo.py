from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, List
from pathlib import Path

from pipen import plugin
from pipen.job import Job

if TYPE_CHECKING:
    from pipen import Proc, Pipen

__version__ = "0.7.0"

# Monkey-path Job.CMD_WRAPPER_TEMPLATE to time the script
Job.CMD_WRAPPER_TEMPLATE = Job.CMD_WRAPPER_TEMPLATE.replace(
    "{job.strcmd} \\",
    textwrap.dedent(
        """
        jobcmd="{job.strcmd}"
        if [ -z "$jobcmd" ]; then
            jobcmd="echo 'No command to run (probably no script specified?)' 1>&2"
        fi

        # Check if GNU time is available
        if env time -V &>/dev/null; then
            jobcmd="env time -o {job.metadir}/job.runinfo.time -v $jobcmd"
        else
            echo "GNU time is not available, job is not timed." > {job.metadir}/job.runinfo.time
        fi

        eval $jobcmd \\"""  # noqa: E501
    ),
).replace(
    "{postscript}",
    textwrap.dedent(
        """
        {postscript}

        echo "# CPU" > {job.metadir}/job.runinfo.device
        lscpu >> {job.metadir}/job.runinfo.device
        echo "" >> {job.metadir}/job.runinfo.device
        echo "# Memory" >> {job.metadir}/job.runinfo.device
        lsmem --summary=only >> {job.metadir}/job.runinfo.device
        """
    ),
)


SESSION_INFO_PYTHON = r"""
def _session_info(show_path: bool, include_submodule: bool):
    try:
        from importlib import metadata as importlib_metadata
    except ImportError:
        import importlib_metadata

    import sys
    runinfo_file = "{{job.metadir}}/job.runinfo.session"

    lines = ["# Generated by pipen_runinfo v%(version)s\n", "# Lang: python\n"]
    if show_path:
        lines.append("Name\t__version__\timportlib.metadata\tPath\n")
        lines.append(f"python\t{sys.version}\t-\t{sys.executable}\n")
    else:
        lines.append("Name\t__version__\timportlib.metadata\n")
        lines.append(f"python\t{sys.version}\t-\n")

    for name, module in sys.modules.copy().items():
        if not include_submodule and "." in name:
            continue

        ver = getattr(
            module,
            "__version__",
            getattr(module, "version", "-"),
        )
        mdfile = getattr(module, "__file__", None)
        if mdfile is None or "site-packages" not in mdfile or not module.__package__:
            # Suppose it's a built-in module
            continue

        try:
            imver = importlib_metadata.version(module.__package__)
        except importlib_metadata.PackageNotFoundError:
            imver = "-"

        if show_path:
            lines.append(f"{name}\t{ver}\t{imver}\t{mdfile}\n")
        else:
            lines.append(f"{name}\t{ver}\t{imver}\n")

    with open(runinfo_file, "w") as fout:
        fout.writelines(lines)
""" % {"version": __version__}


SESSION_INFO_R = r"""
writeLines(
    c(
        "# Generated by pipen_runinfo v%(version)s",
        "# Lang: R",
        capture.output(sessionInfo())
    ),
    "{{job.metadir}}/job.runinfo.session"
)
""" % {"version": __version__}

SESSION_INFO_FISH = r"""
set -l runinfo_file "{{job.metadir}}/job.runinfo.session"
echo "# Generated by pipen_runinfo v%(version)s" > $runinfo_file
echo "# Lang: fish" >> $runinfo_file
echo -e "SHELL\t$SHELL" >> $runinfo_file
echo -e "FISH_VERSION\t$FISH_VERSION" >> $runinfo_file
set -l exe (readlink /proc/(echo %%self)/exe)
echo -e "proc-exe\t$exe" >> $runinfo_file
echo -e "proc-exe-verion\t$($exe --version)" 2>/dev/null >> $runinfo_file
""" % {"version": __version__}

SESSION_INFO_BASH = r"""
runinfo_file="{{job.metadir}}/job.runinfo.session"
echo "# Generated by pipen_runinfo v%(version)s" > $runinfo_file
echo "# Lang: bash" >> $runinfo_file
echo -e "SHELL\t$SHELL" >> $runinfo_file
echo -e "BASH_VERSION\t$BASH_VERSION" >> $runinfo_file
echo -e "BASH_ARGV0\t$BASH_ARGV0" >> $runinfo_file
echo -e "BASH_SOURCE\t$BASH_SOURCE" >> $runinfo_file
exe=$(readlink /proc/$$/exe)
echo -e "proc-exe\t$exe" >> $runinfo_file
echo -e "proc-exe-version\t$($exe --version | head -1)" >> $runinfo_file
""" % {"version": __version__}


def _get_lang(langpath: str | List[str]):
    if isinstance(langpath, list):
        langpath = langpath[0]

    stem = Path(langpath).stem if langpath else "bash"
    # Might be python3, python3.7, python3.7m, etc.
    if stem.startswith("python"):
        return "python"

    if (
        stem in ("Rscript", "R")
        or stem.startswith("Rscript")
        or stem.startswith("R-")
    ):
        return "R"

    if stem.startswith("bash"):
        return "bash"

    if stem.startswith("fish"):
        return "fish"

    return stem


def _get_code(
    lang: str,
    show_path: bool,
    include_submodule: bool,
) -> str | None:
    if lang == "python":
        return (
            f"{SESSION_INFO_PYTHON}\n\n"
            "if __name__ == '__main__':\n"
            f"    _session_info({show_path}, {include_submodule})\n"
        )

    if lang == "R":
        return SESSION_INFO_R

    if lang == "bash":
        return SESSION_INFO_BASH

    if lang == "fish":
        return SESSION_INFO_FISH

    return None


def _append_code(script: str, code: str):
    return f"{script.rstrip()}\n\n{code.rstrip()}\n"


class PipenRuninfoPlugin:
    name = "runinfo"
    version = __version__
    priority = 998

    @plugin.impl
    async def on_init(pipen: "Pipen"):
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
    def on_proc_script_computed(proc: "Proc"):
        """Called when a process is initialized.

        Try to modify the script so that we can get the runinfo.
        """
        pipeline_plugin_opts = (
            proc.pipeline.config.get("plugin_opts", None) or {}
        )
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

        code = _get_code(
            runinfo_lang,
            show_path=runinfo_path,
            include_submodule=runinfo_submod,
        )
        if code is None:
            # If the language is not supported, just
            return

        script = proc.script
        if script is None:
            return

        script = _append_code(script, code)
        proc.script = script
