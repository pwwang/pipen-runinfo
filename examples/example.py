import os
import sys
from shutil import which
from panpath import PanPath
from pipen import Proc, Pipen
from dotenv import load_dotenv

load_dotenv()
BUCKET = os.getenv("BUCKET")
is_cloud = len(sys.argv) > 1 and sys.argv[1] == "--cloud"
r_installed = which("Rscript") is not None
workdir = PanPath(f"gs://{BUCKET}/pipen_runinfo_example") if is_cloud else ".pipen"


pipelines = []

if r_installed:

    class R(Proc):
        """Running info for R."""

        input = "var"
        output = "var:var:{{in.var}}"
        script = """
            if ({{in.var}} == 0) {
                print("hello")
            } else {
                library(dplyr)
                main3 <- function() {
                    print("world")
                    data.frame(a = 1) %>%
                        dplyr::mutate(b = !!rlang::parse_expr("b + 1"))
                }
                main2 <- function() { main3() }
                main1 <- function() { main2() }
                main1()
            }
        """
        lang = "Rscript"

    pipelines.append(
        Pipen(name="PipelineR", forks=2, cache=False, workdir=workdir)
        .set_starts(R)
        .set_data([0, 1])
    )


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


pipelines.append(
    Pipen(name="PipelinePython", forks=2, cache=False, workdir=workdir)
    .set_starts(Python)
    .set_data([0, 1])
)


class PythonNoPathWithSubmods(Proc):
    """Running info for Python but with submodules included."""

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
    plugin_opts = {"runinfo_path": False, "runinfo_submod": True}


pipelines.append(
    Pipen(name="PipelinePythonNoPathWithSubmods", forks=2, cache=False, workdir=workdir)
    .set_starts(PythonNoPathWithSubmods)
    .set_data([0, 1])
)


class Fish(Proc):
    """Running info for fish."""

    input = "var"
    output = "var:var:{{in.var}}"
    script = """
        if test {{in.var}} -eq 0
            echo "hello"
        else
            echo "world"
            exit 1
        end
    """
    lang = "fish"


pipelines.append(
    Pipen(name="PipelineFish", forks=2, cache=False, workdir=workdir)
    .set_starts(Fish)
    .set_data([0, 1])
)


class Bash(Proc):
    """Running info for Bash."""

    input = "var"
    output = "var:var:{{in.var}}"
    script = """
        if [ "{{in.var}}" -eq 0 ]; then
            echo "hello"
        else
            echo "world"
            exit 1
        fi
    """
    lang = "bash"


pipelines.append(
    Pipen(name="PipelineBash", forks=2, cache=False, workdir=workdir)
    .set_starts(Bash)
    .set_data([0, 1])
)


class BashRuninfoLang(Proc):
    """Running info for bash with runinfo_lang specified."""

    input = "var"
    output = "var:var:{{in.var}}"
    script = """
        if [ "{{in.var}}" -eq 0 ]; then
            echo "hello"
        else
            echo "world"
            exit 1
        fi
    """
    lang = "bash"
    plugin_opts = {"runinfo_lang": "bash"}


pipelines.append(
    Pipen(name="PipelineBashRuninfoLang", forks=2, cache=False, workdir=workdir)
    .set_starts(BashRuninfoLang)
    .set_data([0, 1])
)


if __name__ == "__main__":
    for pipeline in pipelines:
        pipeline.run()
