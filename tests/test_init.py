import pytest  # noqa
from pipen import Proc, Pipen
from pipen_runinfo import _get_lang


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
        Pipen(name="PipelinePython", forks=2, outdir=outdir, workdir=workdir)
        .set_starts(Python)
        .set_data([0, 1])
    )
    pipeline.run()


# @pytest.mark.forked
def test_pipeline_with_no_script(tmp_path):

    outdir = tmp_path / "outdir"
    workdir = tmp_path / "workdir"
    print(workdir)

    class Python(Proc):
        """Running info for Python."""
        input = "var"
        output = "var:var:{{in.var}}"
        lang = "python"

    pipeline = (
        Pipen(name="PipelineNoscript", forks=2, outdir=outdir, workdir=workdir)
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