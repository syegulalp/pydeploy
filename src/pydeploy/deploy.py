import glob
import logging
import os
import py_compile
import shutil
import sys
import tomllib
import zipfile
from pathlib import Path
from urllib.request import urlopen

import pip
from pip._vendor.distlib.scripts import ScriptMaker

logging.basicConfig(level=logging.INFO)

VERSION_ID = ".".join(str(_) for _ in sys.version_info[0:3])
SHORT_VERSION_ID = "".join(str(_) for _ in sys.version_info[0:2])
EMBEDDABLE_ARCHIVE_NAME = f"python-{VERSION_ID}-embed-amd64.zip"
EMBEDDABLE_DOWNLOAD_LOCATION = (
    f"https://www.python.org/ftp/python/{VERSION_ID}/{EMBEDDABLE_ARCHIVE_NAME}"
)
DISTRIBUTION_PATH = Path(f"./deploy_{VERSION_ID}")
RUNTIME_SRC_PATH = Path(DISTRIBUTION_PATH, f"./build")
RUNTIME_UNPACK_PATH = RUNTIME_SRC_PATH / "runtime"
RUNTIME_DIST_PATH = Path(DISTRIBUTION_PATH, "./dist")

VENV_PATH = Path(sys.prefix)
SYSTEM_INTERPRETER_PATH = Path(sys.base_prefix)

PYLIBS_TARGET_DIR = "pylibs"
APP_LIBS_TARGET_DIR = "app"


def fetch_runtime(source: str, target: Path):
    with urlopen(source) as u:
        redistributable_file = u.read()
    logging.info(f"Obtained runtime from {source}")
    redistributable_zip = target / EMBEDDABLE_ARCHIVE_NAME
    with open(redistributable_zip, "wb") as f:
        f.write(redistributable_file)
    z = zipfile.ZipFile(redistributable_zip)
    z.extractall(RUNTIME_UNPACK_PATH)
    logging.info(f"Runtime unpacked into {RUNTIME_UNPACK_PATH}")


def setup_directories():
    if not DISTRIBUTION_PATH.exists():
        logging.info(f"Deployment path {DISTRIBUTION_PATH} doesn't exist, creating")
        DISTRIBUTION_PATH.mkdir()
    else:
        logging.info(f"Deployment path {DISTRIBUTION_PATH} exists")

    if not RUNTIME_SRC_PATH.exists():
        logging.info(
            f"Runtime source path {RUNTIME_SRC_PATH} doesn't exist, fetching from:"
        )
        logging.info(f"{EMBEDDABLE_DOWNLOAD_LOCATION}")
        RUNTIME_SRC_PATH.mkdir()
        fetch_runtime(EMBEDDABLE_DOWNLOAD_LOCATION, RUNTIME_SRC_PATH)
    else:
        logging.info(f"Runtime source path {RUNTIME_SRC_PATH} exists")

    # Remove existing distribution path
    shutil.rmtree(RUNTIME_DIST_PATH, ignore_errors=True)
    RUNTIME_DIST_PATH.mkdir(parents=True)
    logging.info(f"Destination build path {RUNTIME_DIST_PATH}; creating")


def main():
    app_toml = tomllib.load(open("pyproject.toml", "rb"))
    app_name = app_toml["project"]["name"]

    cli_scripts = app_toml["project"].get("scripts", {})
    gui_scripts = app_toml["project"].get("gui-scripts", {})

    logging.info("Pypacker running")
    setup_directories()

    logging.info("Copying base files from redistributable")

    PACKAGE_NAME = sys.argv[1] if len(sys.argv) > 1 else "."

    for dist_dir in ("python*.exe", "python*.dll"):
        files = glob.glob(str(RUNTIME_UNPACK_PATH / dist_dir))
        for ff in files:
            file = Path(ff)
            shutil.copyfile(file, RUNTIME_DIST_PATH / file.name)

    with open(RUNTIME_DIST_PATH / f"python{SHORT_VERSION_ID}._pth", "w") as dist_dir:
        dist_dir.write(
            f"{PYLIBS_TARGET_DIR}\\python{SHORT_VERSION_ID}.zip\n"
            "{PYLIBS_TARGET_DIR}\n"
            f"{APP_LIBS_TARGET_DIR}\\{app_name}_lib.zip"
            f"{APP_LIBS_TARGET_DIR}\n"
            "."
        )

    PY_LIBS_PATH = RUNTIME_DIST_PATH / PYLIBS_TARGET_DIR
    PY_LIBS_PATH.mkdir()

    APP_LIBS_PATH = RUNTIME_DIST_PATH / APP_LIBS_TARGET_DIR

    for dist_dir in ("python*.zip", "*.pyd", "*.dll"):
        files = glob.glob(str(RUNTIME_UNPACK_PATH / dist_dir))
        for ff in files:
            file = Path(ff)
            shutil.copyfile(file, PY_LIBS_PATH / file.name)

    pip.main(["install", PACKAGE_NAME, "-t", str(APP_LIBS_PATH)])

    logging.info("Creating entry point .exes")

    gui = False

    for script in (cli_scripts, gui_scripts):
        for script_name, script_path in script.items():
            sm = ScriptMaker(
                None,
                target_dir=str(RUNTIME_DIST_PATH),
                add_launchers=True,
            )
            sm.variants = [""]
            sm.make(f"{script_name} = {script_path}", {"gui": gui})
        gui = True

    logging.info("Removing legacy bin directory from distribution")

    shutil.rmtree(APP_LIBS_PATH / "bin")

    logging.info("Removing dist-info directories")

    for dist_dir in glob.glob(str(APP_LIBS_PATH / "*.dist-info")):
        shutil.rmtree(dist_dir, ignore_errors=True)

    logging.info("Compiling .py to .pyc archives")

    app_libs_archive = zipfile.ZipFile(
        str(APP_LIBS_PATH / f"{app_name}_lib.zip"),
        "w",
        compression=zipfile.ZIP_BZIP2,
        # compresslevel=9,
    )

    for path, dirs, files in os.walk(str(APP_LIBS_PATH)):
        for dir in dirs:
            if dir.endswith("__pycache__"):
                shutil.rmtree(Path(path, dir), ignore_errors=True)
        for file in files:
            if not file.endswith(".py"):
                continue
            f_path = Path(path, file)
            compiled_f_path = f_path.with_suffix(".pyc")
            py_compile.compile(f_path, f_path.with_suffix(".pyc"))
            app_libs_archive.write(
                str(compiled_f_path),
                str(compiled_f_path).replace(str(APP_LIBS_PATH), ""),
            )
            f_path.unlink(missing_ok=True)
            compiled_f_path.unlink(missing_ok=True)

    for path, dirs, files in os.walk(str(APP_LIBS_PATH), topdown=False):
        if not files:
            Path(path).rmdir()

    logging.info("Creating .zip archive")

    zip_archive_filename = Path(DISTRIBUTION_PATH / f"{app_name}.zip")
    zip_archive_filename.unlink(missing_ok=True)

    app_archive = zipfile.ZipFile(
        str(zip_archive_filename),
        "w",
        compression=zipfile.ZIP_BZIP2,
        # compresslevel=9,
    )
    for path, dirs, files in os.walk(str(RUNTIME_DIST_PATH)):
        target_path = path.replace(str(RUNTIME_DIST_PATH), ".")
        for file in files:
            app_archive.write(str(Path(path, file)), str(Path(target_path, file)))

    app_archive.close()

    logging.info(f"Finished creating distribution for {app_name}")

    # options to include sqlite or tkinter


if __name__ == "__main__":
    main()
