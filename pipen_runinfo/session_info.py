from __future__ import annotations

import re
from .version import __version__ as version

# Session info code for python
# ------------------------------------------------------------
SESSION_INFO_PYTHON = r"""
# Inserted by pipen_runinfo, please do not modify
import atexit


def _session_info(show_path: bool, include_submodule: bool):
    try:
        from importlib import metadata as importlib_metadata
    except ImportError:
        import importlib_metadata

    import sys
    {%% if "://" in str(job.metadir) %%}
    from yunpath import AnyPath as _AnyPath
    {%% else %%}
    from pathlib import Path as _AnyPath
    {%% endif %%}

    runinfo_file = _AnyPath("{{job.metadir}}/job.runinfo.session")

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

    with runinfo_file.open("w") as fout:
        fout.writelines(lines)


@atexit.register
def _run_session_info():
    _session_info(%(show_path)s, %(include_submodule)s)


# End of injected by pipen_runinfo
# ------------------------------------------------------------
# Regular script starts
# ------------------------------------------------------------
"""

future_import_statement = re.compile(
    r"^from\s+__future__\s+import\s+annotations\s*$",
    re.MULTILINE,
)


def inject_session_code_python(
    script: str,
    show_path: bool,
    include_submodule: bool,
) -> str:
    """Inject the session info code into a python script.

    Args:
        script: The script to inject the session info code into.
        show_path: Whether to include the path of the modules in the session info.
        include_submodule: Whether to include submodules in the session info.

    Returns:
        The injected script.
    """
    code = SESSION_INFO_PYTHON % {
        "version": version,
        "show_path": show_path,
        "include_submodule": include_submodule,
    }
    parts = future_import_statement.split(script, 1)
    if len(parts) == 1:
        return f"{code}\n\n{script}"

    # Matched!
    # Check if the future import is at the top
    # The first parts must be empty or comments
    if not parts[0].strip() or all(
        line.lstrip().startswith("#") or not line.strip()
        for line in parts[0].splitlines()
    ):
        return f"from __future__ import annotations\n{code}\n{''.join(parts)}"

    # The future import is not at the top, it is probably in a string
    return f"{code}\n\n{script}"


# Session info code for R
# ------------------------------------------------------------
SESSION_INFO_R = r"""
.save_session_info <- function() {
    .runinfo.session.file <- "{{job.metadir}}/job.runinfo.session"
    if (grepl("://", .runinfo.session.file)) {
        .runinfo.session.file.orig <- .runinfo.session.file
        .runinfo.session.file <- tempfile()
    }

    writeLines(
        c(
            "# Generated by pipen_runinfo v%(version)s",
            "# Lang: R",
            capture.output(sessionInfo())
        ),
        .runinfo.session.file
    )

    if (exists(".runinfo.session.file.orig")) {
        system2("cloudsh", c("mv", .runinfo.session.file, .runinfo.session.file.orig))
    }
}
""" % {"version": version}


def inject_session_code_r(
    script: str,
    show_path: bool,
    include_submodule: bool,
) -> str:
    # indent = " " * 4
    injected = [f"# Injected by pipen_runinfo v{version}, please do not modify"]
    injected.extend(SESSION_INFO_R.splitlines())
    injected.append("tryCatch({")
    injected.append("# End of injected by pipen_runinfo, please do not modify")
    injected.append("# ------------------------------------------------------")
    injected.append("# Regular script starts")
    injected.append("# ------------------------------------------------------")
    injected.append("")
    # injected.extend((f"{indent}{line}" for line in script.splitlines()))
    injected.append(script)
    injected.append("")
    injected.append("# ------------------------------------------------------")
    injected.append("# Regular script ends")
    injected.append("# ------------------------------------------------------")
    injected.append("# Injected by pipen_runinfo, please do not modify")
    injected.append("}, finally = .save_session_info())")
    injected.append("# End of injected by pipen_runinfo, please do not modify")
    injected.append("")
    return "\n".join(injected)


# Session info code for bash
# ------------------------------------------------------------
SESSION_INFO_BASH = r"""
# Injected by pipen_runinfo v%(version)s, please do not modify
_session_info() {
    runinfo_file="{{job.metadir}}/job.runinfo.session"
    if [[ "$runinfo_file" == *"://"* ]]; then
        runinfo_file_orig="$runinfo_file"
        runinfo_file=$(mktemp)
    fi

    echo "# Generated by pipen_runinfo v%(version)s" > $runinfo_file
    # shellcheck disable=SC2129
    echo "# Lang: bash" >> $runinfo_file
    echo -e "SHELL\t$SHELL" >> $runinfo_file
    echo -e "BASH_VERSION\t$BASH_VERSION" >> $runinfo_file
    echo -e "BASH_ARGV0\t$BASH_ARGV0" >> $runinfo_file
    echo -e "BASH_SOURCE\t$BASH_SOURCE" >> $runinfo_file
    exe=$(readlink /proc/$$/exe)
    # shellcheck disable=SC2129
    echo -e "proc-exe\t$exe" >> $runinfo_file
    echo -e "proc-exe-version\t$($exe --version | head -1)" >> $runinfo_file

    if [[ -v runinfo_file_orig ]]; then
        cloudsh mv "$runinfo_file" "$runinfo_file_orig"
    fi
}

trap _session_info EXIT
# End of injected by pipen_runinfo
# ------------------------------------------------------------
# Regular script starts
# ------------------------------------------------------------
""" % {"version": version}


def inject_session_code_bash(
    script: str,
    show_path: bool,
    include_submodule: bool,
) -> str:
    return f"{SESSION_INFO_BASH}\n\n{script}"


# Session info code for fish
# ------------------------------------------------------------
SESSION_INFO_FISH = r"""
# Injected by pipen_runinfo v%(version)s, please do not modify
function _session_info
    set -l runinfo_file "{{job.metadir}}/job.runinfo.session"
    if string match -q "*://*" $runinfo_file
        set runinfo_file_orig $runinfo_file
        set runinfo_file (mktemp)
    end

    echo "# Generated by pipen_runinfo v%(version)s" > $runinfo_file
    echo "# Lang: fish" >> $runinfo_file
    echo -e "SHELL\t$SHELL" >> $runinfo_file
    echo -e "FISH_VERSION\t$FISH_VERSION" >> $runinfo_file
    set -l exe (readlink /proc/(echo %%self)/exe)
    echo -e "proc-exe\t$exe" >> $runinfo_file
    echo -e "proc-exe-verion\t$($exe --version)" 2>/dev/null >> $runinfo_file

    if set -q runinfo_file_orig
        cloudsh mv $runinfo_file $runinfo_file_orig
    end
end

trap _session_info EXIT
# End of injected by pipen_runinfo, please do not modify
# ------------------------------------------------------------
# Regular script starts
# ------------------------------------------------------------
""" % {"version": version}


def inject_session_code_fish(
    script: str,
    show_path: bool,
    include_submodule: bool,
) -> str:
    return f"{SESSION_INFO_FISH}\n\n{script}"


def get_inject_session_code_fun(lang: str) -> str | None:
    """Get the language support class."""
    if lang == "python":
        return inject_session_code_python
    if lang == "R":
        return inject_session_code_r
    if lang == "bash":
        return inject_session_code_bash
    if lang == "fish":
        return inject_session_code_fish

    return None
