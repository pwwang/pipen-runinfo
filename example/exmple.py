from pipen import Proc, Pipen


class R(Proc):
    """Running info for R."""

    input = "var"
    output = "var:var:{{in.var}}"
    script = """print("hello")"""
    lang = "Rscript"


class Python(Proc):
    """Running info for Python."""

    input = "var"
    output = "var:var:{{in.var}}"
    # See if we can get the runinfo (version for pipen)
    script = """import pipen; import pipen_runinfo; print("hello")"""
    lang = "python"


class PythonNoPathWithSubmods(Proc):
    """Running info for Python but with submodules included."""

    input = "var"
    output = "var:var:{{in.var}}"
    # See if we can get the runinfo (version for pipen)
    script = """import pipen; import pipen_runinfo; print("hello")"""
    lang = "python"
    plugin_opts = {"runinfo_path": False, "runinfo_submod": True}


class Fish(Proc):
    """Running info for fish."""

    input = "var"
    output = "var:var:{{in.var}}"
    script = """echo "hello" """
    lang = "fish"


class Bash(Proc):
    """Running info for Bash."""

    input = "var"
    output = "var:var:{{in.var}}"
    script = """echo "hello" """
    lang = "bash"


class BashRuninfoLang(Proc):
    """Running info for bash with runinfo_lang specified."""

    input = "var"
    output = "var:var:{{in.var}}"
    script = """echo "hello" """
    lang = "bash"
    plugin_opts = {"runinfo_lang": "bash"}



class Pipeline(Pipen):
    starts = [R, Python, PythonNoPathWithSubmods, Fish, Bash, BashRuninfoLang]
    data = [[1], [2], [3], [4], [5], [6]]


if __name__ == "__main__":
    Pipeline().run()
