> This project is still in its very early stages. This documentation is correspondingly rough and incomplete.

PyDeploy is an *experimental* project to allow Python programs to be deployed as standalone applications (currently only on Microsoft Windows), provided they are written to be `pip install`-able by way of a `pyproject.toml` file.

Instead of using the PyInstaller approach, which is highly customized, PyDeploy uses Python-native tooling and procedures. It uses the Python redistributable package to create a self-contained Python instance, and `pip install`s the needed files into it.

The end result should not cause antivirus systems to complain as it only uses the binaries already signed and redistributed with Python.

PyDeploy has no dependencies other than the standard library.

# Usage

## 1. Create a `pip install`-able project using `pyproject.toml` and the proper project layout

Basically, make your app into a pip-installable package using `pyproject.toml`. If you haven't learned how to do this yet, I highly recommend it. The `examples` directory will furnish some examples for how to do this for various kinds of programs. [TODO]

Make a virtual environment for your project, and ideally use a `src` directory for your application code. You should also have a `pyproject.toml` file along these lines:

```toml
[project]
name = "myapp"
version = "0.1"

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project.scripts]
myproject = "myproject:main"
```

Note that the `project.scripts` section will be used by PyDeploy to determine what `.exe` entry points to make. In this case, we will have a CLI entry point named `myproject.exe` in our deployable app directory.

*Make sure your application works as a `pip install`-able project **before** you use PyDeploy!* Install your app into its own venv using the `-e` ("editable") flag, and test it that way.

If you want to copy *data directories or other artifacts* over to the target, see the section "Using the `tool.pydeploy` section of `pyproject.toml` to configure build behavior" below.


## 2. Install PyDeploy into project venv

Right now PyDeploy is not on PyPI, so you'll need to install directly from Github:

`pip install git+https://github.com/syegulalp/pydeploy`

## 3. Run pydeploy on your project

While in the project's root, type:

`pydeploy .`

This will analyze the `pyproject.toml` file and create a subdirectory named `deploy_<version>`, where `<version>` is the Python version for the currently active venv.

After the analysis and build process finishes you should have a `dist` subdirectory that contains your deployed project, along with a `.zip` archive of the project.

The resulting archive may be fairly large even for a simple "hello world" app, but I will introduce mechanisms in the future to make the deployed app less bulky by removing unused libraries.

# Command line options

Pydeploy has a few command line switches, supplied after the directory name for the project to build (typically `.`):

* `-x`: Does not build zip archives of the application files. Normally all Python files are packed into a zip file, but the original layout of Python files can be preserved with this option. Note that if PyDeploy detects a mix of Python and other files in an app directory, it will fall back to this behavior for that app directory.
* `-s`: Omit some of the larger and less commonly used standard library modules, which reduces the footprint of the redistributable. The variables `remove_stdlib_for_smallify` and `remove_for_smallify` list the libraries and modules in question. (This will eventually be replaced with a more fine-grained mechanism.)

# Using the `tool.pydeploy` section of `pyproject.toml` to configure build behavior

You can configure some of Pydeploy's behaviors by adding a `tool.pydeploy` section to your `pyproject.toml` file.

```toml
[tool.pydeploy]
data_dirs = [["source_dir", "target_dir"]]
omit_files = ["libs/app/module/*.c", "libs/app/module/*.pyc"]
```

## `data_dirs`

`data_dirs` is used to copy files from your source project tree, such as data files, into your distribution.

To use `data_dirs`, provide a list of two-item lists. The first item is the source directory in your project tree (with `pyproject.toml` as the root); the second item is the target directory with the executable directory as the root. (This is the directory that will by default be the current working directory when your app is launched.)

## `omit_files`

`omit_files` is a list of `glob` patterns, starting from the root of the distribution directory. Files that match these patters are removed from the distribution right before the .zip-archiving process. You can use this to remove things like build artfacts or other unwanted files from your shipped package.

# Tips

The `examples` directory contains scaffolding examples for a few common project types -- a simple CLI, a windowed app using TKinter or Pygame, etc. This gallery will be expanded with time.

# Todo

* Support for including TKinter (not included with embedded redistributable)
* Support for excluding specific modules or submodules from apps or stdlib, as opposed to just files

# License

MIT