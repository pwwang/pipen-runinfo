from shutil import which
from pipen import Proc, Pipen

r_installed = which("Rscript") is not None


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
                print("world")
                stop("Error")
            }
        """
        lang = "Rscript"

    pipelines.append(Pipen(name="PipelineR", forks=2).set_starts(R).set_data([0, 1]))


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
    Pipen(name="PipelinePython", forks=2)
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
    Pipen(name="PipelinePythonNoPathWithSubmods", forks=2)
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


pipelines.append(Pipen(name="PipelineFish", forks=2).set_starts(Fish).set_data([0, 1]))


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


pipelines.append(Pipen(name="PipelineBash", forks=2).set_starts(Bash).set_data([0, 1]))


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
    Pipen(name="PipelineBashRuninfoLang", forks=2)
    .set_starts(BashRuninfoLang)
    .set_data([0, 1])
)


if __name__ == "__main__":
    for pipeline in pipelines:
        pipeline.run()
