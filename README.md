# pipen-runinfo

Generate running information for jobs in [pipen][1] pipelines.

## Install

```bash
pip install -U pipen-runinfo
```

## Enable/Disable the plugin

The plugin is registered via entrypoints. It's by default enabled. To disable it: plugins=[..., "no:runinfo"], or uninstall this plugin.

## Plugin options

- `runinfo_lang`: The name of the language to run the job script.
    Default is `None`, which means it will be inferred from the `proc.lang`
    This should be a process-level option, unless you only have one single
    process in your pipeline.
- `runinfo_path`: Whether to include paths for the modules in the running information.
    Default is `True`.
    This option could be either specified in the process-level or the pipeline-level.
    Only works for `python`.
- `runinfo_submod`: Whether to include submodules in the running information.
    Default is `False`.
    This option could be either specified in the process-level or the pipeline-level.
    Only works for `python`.

## Supported languages

`python`, `R`, `bash`, and `fish`.

## Usage

The plugin will generate a `job.runinfo` file in the job directory of the pipeline, which contains the running information of the job.

### Python

Generates a TSV file with the following columns:

- `Name`: The name of the module, or python itself
- `__version__`: The version fetched by `module.__version__` or `module.version`
- `importlib.metadata`: The version fetched by `importlib.metadata.version(package)`
- `Path`: The path of the module (only if `runinfo_path` is `True`)

### R

Generates a text file `sessionInfo()` output.

### Bash

Generates a TSV file with the following columns:

- `SHELL`: The value of `$SHELL`
- `BASH_VERSION`: The value of `$BASH_VERSION`
- `BASH_ARGV0`: The value of `$BASH_ARGV0`
- `BASH_SOURCE`: The value of `$BASH_SOURCE`
- `proc-exe`: The real path of the executable from `/proc/<pid>/exe`
- `proc-exe-version`: The version of the executable from `/proc/<pid>/exe --version`

### Fish

Generates a TSV file with the following columns:

- `SHELL`: The value of `$SHELL`
- `FISH_VERSION`: The value of `$FISH_VERSION`
- `proc-exe`: The real path of the executable from `/proc/<pid>/exe`
- `proc-exe-version`: The version of the executable from `/proc/<pid>/exe --version`


[1]: https://github.com/pwwang/pipen
