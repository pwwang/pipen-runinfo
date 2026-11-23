import os
import subprocess
from types import SimpleNamespace

import pytest  # noqa
from pipen import Proc, Pipen
from pipen_runinfo import PipenRuninfoPlugin, _get_lang


# @pytest.mark.forked
def test_pipeline(tmp_path):

    outdir = tmp_path / "outdir"
    workdir = tmp_path / "workdir"

    class Python(Proc):
        """Running info for Python."""

        input = "var"
        output = "var:var:{{in.var}}"
        # See if we can get the runinfo (version for pipen)
        script = """
            import pipen
            import pipen_runinfo

            if {{in.var}} == 0:
                print("hello")
            else:
                print("world")
                raise ValueError("Error")
        """
        lang = "python"

    pipeline = (
        Pipen(
            name="PipelinePython",
            forks=2,
            outdir=outdir,
            workdir=workdir,
        )
        .set_starts(Python)
        .set_data([0, 1])
    )
    pipeline.run()


# @pytest.mark.forked
def test_pipeline_with_no_script(tmp_path):

    outdir = tmp_path / "outdir"
    workdir = tmp_path / "workdir"

    class Python(Proc):
        """Running info for Python."""
        input = "var"
        output = "var:var:{{in.var}}"
        lang = "python"

    pipeline = (
        Pipen(
            name="PipelineNoscript",
            forks=2,
            outdir=outdir,
            workdir=workdir,
        )
        .set_starts(Python)
        .set_data([0, 1])
    )
    pipeline.run()


def test_get_lang():

    assert _get_lang("python") == "python"
    assert _get_lang("python") == "python"
    assert _get_lang("python3") == "python"
    assert _get_lang("python3.8") == "python"
    assert _get_lang("R") == "R"
    assert _get_lang("Rscript") == "R"
    assert _get_lang("Rscript-3.6") == "R"
    assert _get_lang("R-3.6") == "R"
    assert _get_lang("bash") == "bash"
    assert _get_lang(["bash", "-e"]) == "bash"
    assert _get_lang("fish") == "fish"
    assert _get_lang("sh") == "sh"
    assert _get_lang("zsh") == "zsh"
    assert _get_lang("python3.8.1") == "python"


def test_device_info_fallbacks(tmp_path):
    job = SimpleNamespace(proc=SimpleNamespace(scheduler=SimpleNamespace(name="local")))
    code = PipenRuninfoPlugin().on_jobcmd_end(job)

    # Shadow lscpu/free with failing stubs to force the /proc fallbacks
    shim = tmp_path / "bin"
    shim.mkdir()
    for name in ("lscpu", "free"):
        stub = shim / name
        stub.write_text("#!/bin/sh\nexit 1\n")
        stub.chmod(0o755)

    runinfo = tmp_path / "job.runinfo.device"
    shell = tmp_path / "device.sh"
    shell.write_text(f'runinfo_device="{runinfo}"\n{code}')

    subprocess.run(
        ["bash", str(shell)],
        check=True,
        env={**os.environ, "PATH": f"{shim}:{os.environ.get('PATH', '')}"},
    )

    content = runinfo.read_text()
    assert "processor" in content
    assert "MemTotal" in content
