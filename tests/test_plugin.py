import gc
import io
import shutil
import tempfile
import zipfile
from os import getcwd, path
from pathlib import Path
from sys import path as syspath
from types import SimpleNamespace

import pytest
from hatchling.builders.wheel import WheelBuilder, WheelBuilderConfig
from toml import load

from hatch_cython.plugin import CythonBuildHook
from hatch_cython.utils import plat

from .utils import arch_platform, override_dir


def join(*rel):
    return path.join(getcwd(), *rel)


def read(rel: str):
    return open(join(*rel.split("/"))).read()


@pytest.fixture
def new_src_proj(tmp_path):
    project_dir = tmp_path / "app"
    project_dir.mkdir()
    (project_dir / "bootstrap.py").write_text(read("test_libraries/bootstrap.py"))
    (project_dir / "pyproject.toml").write_text(read("test_libraries/src_structure/pyproject.toml"))
    (project_dir / "hatch.toml").write_text(read("test_libraries/src_structure/hatch.toml"))
    (project_dir / "LICENSE.txt").write_text(read("test_libraries/src_structure/LICENSE.txt"))
    shutil.copytree(join("test_libraries/src_structure", "src"), (project_dir / "src"))
    shutil.copytree(join("test_libraries/src_structure", "tests"), (project_dir / "tests"))
    shutil.copytree(join("test_libraries/src_structure", "include"), (project_dir / "include"))
    shutil.copytree(join("test_libraries/src_structure", "scripts"), (project_dir / "scripts"))
    return project_dir


@pytest.fixture
def new_namespace_proj(tmp_path):
    project_dir = tmp_path / "app"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text(read("test_libraries/namespace_structure/pyproject.toml"))
    (project_dir / "hatch.toml").write_text(read("test_libraries/namespace_structure/hatch.toml"))
    (project_dir / "LICENSE.txt").write_text("")
    shutil.copytree(join("test_libraries/namespace_structure", "src"), (project_dir / "src"))
    return project_dir


def test_namespace_build_hook(new_namespace_proj):
    with override_dir(new_namespace_proj):
        syspath.insert(0, str(new_namespace_proj))
        build_config = load(new_namespace_proj / "hatch.toml")["build"]
        cython_config = build_config["hooks"]["custom"]
        builder = WheelBuilder(root=str(new_namespace_proj))
        hook = CythonBuildHook(
            new_namespace_proj,
            cython_config,
            WheelBuilderConfig(
                builder=builder,
                root=str(new_namespace_proj),
                plugin_name="cython",
                build_config=build_config,
                target_config=build_config["targets"]["wheel"],
            ),
            SimpleNamespace(name="org-myproject"),
            directory=new_namespace_proj,
            target_name="wheel",
        )

        assert hook.is_src
        assert hook.dir_name == "org/myproject"
        assert hook.project_dir == "src/org/myproject"

        assert sorted(hook.precompiled_globs) == sorted(
            [
                "src/org/myproject/*.py",
                "src/org/myproject/**/*.py",
                "src/org/myproject/*.pyx",
                "src/org/myproject/**/*.pyx",
                "src/org/myproject/*.pxd",
                "src/org/myproject/**/*.pxd",
            ]
        )

        assert sorted(hook.normalized_included_files) == sorted(
            [
                "src/org/myproject/__about__.py",
                "src/org/myproject/__init__.py",
                "src/org/myproject/core.pyx",
            ]
        )

        assert sorted(
            [{**ls, "files": sorted(ls.get("files"))} for ls in hook.grouped_included_files],
            key=lambda x: x.get("name"),
        ) == [
            {"name": "org.myproject.__about__", "files": ["src/org/myproject/__about__.py"]},
            {"name": "org.myproject.__init__", "files": ["src/org/myproject/__init__.py"]},
            {"name": "org.myproject.core", "files": ["src/org/myproject/core.pyx"]},
        ]

    syspath.remove(str(new_namespace_proj))


@pytest.mark.parametrize("include_all_compiled_src", [None, True, False])
def test_wheel_build_hook(new_src_proj, include_all_compiled_src: bool | None):
    with override_dir(new_src_proj):
        syspath.insert(0, str(new_src_proj))
        build_config = load(new_src_proj / "hatch.toml")["build"]
        cython_config = build_config["hooks"]["custom"]
        if include_all_compiled_src is None:
            pass
        else:
            cython_config["options"]["include_all_compiled_src"] = include_all_compiled_src
        builder = WheelBuilder(root=str(new_src_proj))
        hook = CythonBuildHook(
            new_src_proj,
            cython_config,
            WheelBuilderConfig(
                builder=builder,
                root=str(new_src_proj),
                plugin_name="cython",
                build_config=build_config,
                target_config=build_config["targets"]["wheel"],
            ),
            SimpleNamespace(name="example_lib"),
            directory=new_src_proj,
            target_name="wheel",
        )

        assert hook.is_src

        if include_all_compiled_src is None:
            assert hook.options.include_all_compiled_src
        else:
            assert hook.options.include_all_compiled_src == include_all_compiled_src

        assert not hook.options.files.explicit_targets

        with arch_platform("", "windows"):
            assert hook.is_windows

        with arch_platform("", "darwin"):
            assert not hook.is_windows

        with arch_platform("", "linux"):
            assert not hook.is_windows

        assert hook.dir_name == "example_lib"

        proj = "src/example_lib"
        assert hook.project_dir == proj

        assert sorted(hook.precompiled_globs) == sorted(
            [
                "src/example_lib/*.py",
                "src/example_lib/**/*.py",
                "src/example_lib/*.pyx",
                "src/example_lib/**/*.pyx",
                "src/example_lib/*.pxd",
                "src/example_lib/**/*.pxd",
            ]
        )

        hook.clean([])
        build_data = {
            "artifacts": [],
            "force_include": {},
        }
        hook.initialize("0.1.0", build_data)

        assert sorted(hook.normalized_included_files) == sorted(
            [
                "src/example_lib/__about__.py",
                "src/example_lib/__init__.py",
                "src/example_lib/_alias.pyx",
                "src/example_lib/custom_includes.pyx",
                "src/example_lib/mod_a/__init__.py",
                "src/example_lib/mod_a/adds.pyx",
                f"src/example_lib/platform/{plat()}.pyx",
                "src/example_lib/mod_a/deep_nest/creates.pyx",
                "src/example_lib/mod_a/some_defn.pxd",
                "src/example_lib/mod_a/some_defn.py",
                "src/example_lib/normal.py",
                "src/example_lib/normal_exclude_compiled_src.py",
                "src/example_lib/normal_include_compiled_src.py",
                "src/example_lib/templated.pyx",
                "src/example_lib/test.pyx",
            ]
        )

        assert sorted(
            [{**ls, "files": sorted(ls.get("files"))} for ls in hook.grouped_included_files],
            key=lambda x: x.get("name"),
        ) == [
            {"name": "example_lib.__about__", "files": ["src/example_lib/__about__.py"]},
            {"name": "example_lib.__init__", "files": ["src/example_lib/__init__.py"]},
            {"name": "example_lib.aliased", "files": ["src/example_lib/_alias.pyx"]},
            {"name": "example_lib.custom_includes", "files": ["src/example_lib/custom_includes.pyx"]},
            {"name": "example_lib.mod_a.__init__", "files": ["src/example_lib/mod_a/__init__.py"]},
            {"name": "example_lib.mod_a.adds", "files": ["src/example_lib/mod_a/adds.pyx"]},
            {"name": "example_lib.mod_a.deep_nest.creates", "files": ["src/example_lib/mod_a/deep_nest/creates.pyx"]},
            {"name": "example_lib.mod_a.some_defn", "files": ["src/example_lib/mod_a/some_defn.py"]},
            {"name": "example_lib.normal", "files": ["src/example_lib/normal.py"]},
            {
                "name": "example_lib.normal_exclude_compiled_src",
                "files": ["src/example_lib/normal_exclude_compiled_src.py"],
            },
            {
                "name": "example_lib.normal_include_compiled_src",
                "files": ["src/example_lib/normal_include_compiled_src.py"],
            },
            {"name": f"example_lib.platform.{plat()}", "files": [f"src/example_lib/platform/{plat()}.pyx"]},
            {"name": "example_lib.templated", "files": ["src/example_lib/templated.pyx"]},
            {"name": "example_lib.test", "files": ["src/example_lib/test.pyx"]},
        ]

        assert build_data.get("infer_tag")
        assert not build_data.get("pure_python")
        assert sorted(hook.artifacts) == sorted(build_data.get("artifacts"))
        assert len(build_data.get("force_include")) == 14
        if include_all_compiled_src is None or include_all_compiled_src is True:
            expected_exclude = ["src/example_lib/normal_exclude_compiled_src.py"]
        else:
            expected_exclude = [
                "src/example_lib/__about__.py",
                "src/example_lib/__init__.py",
                "src/example_lib/_alias.pyx",
                "src/example_lib/custom_includes.pyx",
                "src/example_lib/mod_a/__init__.py",
                "src/example_lib/mod_a/adds.pyx",
                f"src/example_lib/platform/{plat()}.pyx",
                "src/example_lib/mod_a/deep_nest/creates.pyx",
                "src/example_lib/mod_a/some_defn.pxd",
                "src/example_lib/mod_a/some_defn.py",
                "src/example_lib/normal.py",
                "src/example_lib/normal_exclude_compiled_src.py",
                "src/example_lib/templated.pyx",
                "src/example_lib/test.pyx",
            ]
        assert sorted(hook.build_config.target_config["exclude"]) == sorted(expected_exclude)

    syspath.remove(str(new_src_proj))


def test_clean_removes_generated_files(new_src_proj):
    """Test that clean() removes .c and compiled extension files after a build.

    This test deliberately triggers the memo ID-reuse bug: after the build hook is
    garbage-collected, a fresh hook may receive the same memory address, causing
    @memo to return stale cached data (skipping the compile_py side effect).
    """
    with override_dir(new_src_proj):
        syspath.insert(0, str(new_src_proj))
        build_config = load(new_src_proj / "hatch.toml")["build"]
        cython_config = build_config["hooks"]["custom"]

        def make_hook():
            builder = WheelBuilder(root=str(new_src_proj))
            return CythonBuildHook(
                new_src_proj,
                cython_config,
                WheelBuilderConfig(
                    builder=builder,
                    root=str(new_src_proj),
                    plugin_name="cython",
                    build_config=build_config,
                    target_config=build_config["targets"]["wheel"],
                ),
                SimpleNamespace(name="example_lib"),
                directory=new_src_proj,
                target_name="wheel",
            )

        # Step 1: Build to generate .c and compiled extension files
        build_hook = make_hook()
        build_data = {"artifacts": [], "force_include": {}}
        build_hook.initialize("0.1.0", build_data)

        # Step 2: Verify generated files exist
        src_dir = Path(new_src_proj) / "src"
        c_files = list(src_dir.rglob("*.c"))
        assert len(c_files) > 0, f"Expected .c files after build, found none under {src_dir}"

        # Step 3: Destroy build hook and force GC so CPython may reuse the memory address.
        # This triggers the memo ID-reuse bug: the next hook created at the same address
        # would receive stale @memo cache entries (including stale included_files that
        # skip .py sources when compile_py side-effect was not re-applied).
        del build_hook
        gc.collect()

        # Step 4: Create a fresh hook (simulating `hatch clean` — a brand-new instance)
        clean_hook = make_hook()
        clean_hook.clean([])
        del clean_hook
        gc.collect()

        # Step 5: Assert all generated files are gone
        c_files_after = list(src_dir.rglob("*.c"))
        so_files_after = list(src_dir.rglob("*.so")) + list(src_dir.rglob("*.pyd"))
        assert len(c_files_after) == 0, f".c files not removed by clean(): {c_files_after}"
        assert len(so_files_after) == 0, f"compiled extension files not removed by clean(): {so_files_after}"

    syspath.remove(str(new_src_proj))


def test_finalize_drops_compiled_src_when_include_all_false(new_src_proj):
    """finalize() must remove compiled .py files from the wheel when include_all_compiled_src=False.

    Files listed in include_compiled_src should survive; everything else that was
    compiled should be dropped.
    """
    with override_dir(new_src_proj):
        syspath.insert(0, str(new_src_proj))
        build_config = load(new_src_proj / "hatch.toml")["build"]
        cython_config = build_config["hooks"]["custom"]
        cython_config["options"]["include_all_compiled_src"] = False

        builder = WheelBuilder(root=str(new_src_proj))
        hook = CythonBuildHook(
            new_src_proj,
            cython_config,
            WheelBuilderConfig(
                builder=builder,
                root=str(new_src_proj),
                plugin_name="cython",
                build_config=build_config,
                target_config=build_config["targets"]["wheel"],
            ),
            SimpleNamespace(name="example_lib"),
            directory=new_src_proj,
            target_name="wheel",
        )

        # Wheel paths use no "src/" prefix (hatchling strips it for src-layout).
        # These are all compiled files; normal_include_compiled_src.py is the only
        # one listed in include_compiled_src and should survive.
        wheel_py_files = [
            "example_lib/__about__.py",
            "example_lib/__init__.py",
            "example_lib/normal.py",
            "example_lib/normal_exclude_compiled_src.py",
            "example_lib/normal_include_compiled_src.py",
        ]
        record_name = "example_lib-0.1.0.dist-info/RECORD"

        # Build a minimal fake wheel zip
        with tempfile.NamedTemporaryFile(suffix=".whl", delete=False) as tmp:
            whl_path = tmp.name
        with zipfile.ZipFile(whl_path, "w") as zf:
            for f in wheel_py_files:
                zf.writestr(f, b"# placeholder")
            zf.writestr(record_name, "")

        build_data: dict = {"artifacts": [], "force_include": {}}
        hook.finalize("0.1.0", build_data, whl_path)

        with zipfile.ZipFile(whl_path) as zf:
            names = set(zf.namelist())

        # normal_include_compiled_src.py is in include_compiled_src → must stay
        assert "example_lib/normal_include_compiled_src.py" in names
        # all other compiled .py files must be dropped
        for dropped in [
            "example_lib/__about__.py",
            "example_lib/__init__.py",
            "example_lib/normal.py",
            "example_lib/normal_exclude_compiled_src.py",
        ]:
            assert dropped not in names, f"{dropped!r} should have been dropped from wheel"

    syspath.remove(str(new_src_proj))
