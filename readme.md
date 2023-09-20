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
## 2. Install PyDeploy into project venv

Right now PyDeploy is not on PyPI, so you'll need to install directly from Github.

## 3. Run pydeploy on your project

While in the project's root, type:

`pydeploy .`

This will analyze the `pyproject.toml` file and create a subdirectory named `deploy_<version>`, where `<version>` is the Python version for the currently active venv.

After the analysis and build process finishes you should have a `dist` subdirectory that contains your deployed project, along with a `.zip` archive of the project.

The resulting archive may be fairly large even for a simple "hello world" app, but I will introduce mechanisms in the future to make the deployed app less bulky by removing unused libraries.

Pydeploy has a few command line switches, supplied after the directory name for the project to build (typically `.`):

* `-x`: Does not build zip archives of the application files. Normally all Python files are packed into a zip file, but the original layout of Python files can be preserved with this option. Note that if PyDeploy detects a mix of Python and other files in an app directory, it will fall back to this behavior for that app directory.
* `-s`: Omit some of the larger and less commonly used standard library modules, which reduces the footprint of the redistributable. The variables `remove_stdlib_for_smallify` and `remove_for_smallify` list the libraries and modules in question. (This will eventually be replaced with a more fine-grained mechanism.)

# Tips

[TODO] The `examples` directory will contain scaffolding examples for many common project types -- a simple CLI, a windowed app using TKinter or Pygame, etc.

# Todo

* Support for including TKinter (not included with embedded redistributable)
* Support for excluding specific modules or submodules from apps or stdlib
* Quick-and-dirty "minimal" mode (no SQLite, no libcrypto or other network modules, which reduces footprint by 7MB or so)

# License

MIT