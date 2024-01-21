import os
import platform

from llvmlite import binding  # type: ignore

import errors


# * Example of what the lld command *should* look like (linux)
# * ===========================================================
# binding.lld.lld_linux(f"{loc}",
#     [
#         "/usr/lib64/crt1.o", "/usr/lib64/crti.o",
#         "/usr/lib64/gcc/x86_64-pc-linux-gnu/12.2.1/crtbegin.o", f"{loc}.o",
#         "/usr/lib64/gcc/x86_64-pc-linux-gnu/12.2.1/crtend.o",
#         "/usr/lib64/crtn.o"
#     ],
#     [
#         "-Bdynamic", "-no-pie", "--build-id", "--dynamic-linker",
#         "/lib64/ld-linux-x86-64.so.2",
#         "-L/usr/lib/gcc/x86_64-pc-linux-gnu/12.2.1/",
#         "-L/usr/lib/", "-L/usr/lib64/", "-L/lib/", "-L/lib64/", "-lc"
#     ]
# )
def link_windows(file: str, objects: list[str],
                 additional_args: list[str] = []):
    '''Linking for windows from a windows host machine'''
    binding.lld.lld_windows(file,
                            [
                                *get_linuxcrt(),
                                # *["tests/crt.o"],
                                *[object.replace("/", "\\") for object in objects],
                            ],
                            [
                                "-Bdynamic", "-no-pie", "--build-id",
                                "--dynamic-linker", "-LC:\Windows\System32"
                                # "-Iwin32u.dll"
                            ] + additional_args
                            )


def link_linux(file: str, objects: list[str],
               additional_args: list[str] = []):
    '''Linking for linux from a linux host machine'''
    gcc_dir = get_gcc_dir(["lib64", "lib", "bin"])
    binding.lld.lld_linux(file,
                          [
                              *get_linuxcrt(),
                              # *["tests/crt.o"],
                              *objects,
                          ],
                          [
                              "-Bdynamic", "-no-pie", "--build-id",
                              "--dynamic-linker",
                              "/lib64/ld-linux-x86-64.so.2",
                              f"-L{gcc_dir}/",
                              "-L/usr/lib/", "-L/usr/lib64/", "-L/lib/",
                              "-L/lib64/", "-L/usr/lib/x86_64-linux-gnu",
                              "-lc", "-lm"
                          ] + additional_args
                          )


def get_gcc_dir(lib_dir: list | str = 'lib') -> str:
    '''get the gcc directory'''

    if isinstance(lib_dir, list):
        gcc_base = ""
        for location in lib_dir:
            gcc_base = f"/usr/{location}/gcc/"
            if os.path.exists(gcc_base):
                break
    else:
        gcc_base = f"/usr/{lib_dir}/gcc/"
        if not os.path.exists(gcc_base):
            errors.error(f"Directory '{gcc_base}' does not exist." +
                         " Aborting linking process")

    gcc_targets = os.listdir(gcc_base)
    if len(gcc_targets) > 1:
        errors.inline_warning("Found more than one directory inside " +
                              f"'{gcc_base}' defaulting to the " +
                              f"first one: {gcc_targets[0]}")
    gcc_target = gcc_targets[0]
    gcc_versions = os.listdir(f"{gcc_base}/{gcc_target}")
    if len(gcc_versions) > 1:
        errors.inline_warning("Found more than one directory inside " +
                              f"'{gcc_base}/{gcc_target}'defaulting to the " +
                              f"first one: {gcc_versions[0]}")

    gcc_version = gcc_versions[0]
    return f"{gcc_base}/{gcc_target}/{gcc_version}"


def compile_runtime():
    import Ast.module
    old_mod_list = Ast.module.modules
    Ast.module.modules = {}

    libbcl_dir = os.path.dirname(__file__) + "/libbcl"

    output_dir = os.getcwd() + "/target"

    import compile

    compile.compile_runtime(f"{libbcl_dir}/runtime.bcl", "runtime")

    Ast.module.modules = old_mod_list

    return f"{output_dir}/o/.runtime.o"


def get_linuxcrt() -> list[str]:
    '''get CRT files on linux platform'''
    gcc_dir = get_gcc_dir(["lib64", "lib", "bin"])  # `lib` as fallback
    # all_files = os.listdir(gcc_dir)
    # for crt_path in ['/lib/', '/lib64/', gcc_dir, '/usr/lib/', '/usr/lib64/']:
    #     all_files += os.listdir(crt_path)
    output = []
    exclude = ("crtfastmath", "crtprec32", "crtprec64", "crtprec80",
               "crtbeginT", "crtbeginS", "crtendS", "crtendT",
               "crtoffloadtable")

    # note: this *could* be a one-liner, it would just be ugly.
    # for file in all_files:
    #     if file.count('.') != 1:
    #         continue
    #     name, ext = file.split('.')
    #     if ext != 'o':  # skip non .o files
    #         continue
    #     if name.startswith('crt') and name not in exclude:
    #         output.append(f'{gcc_dir}/{file}')
    for crt_path in ['/lib/', '/lib64/', gcc_dir, '/usr/lib/', '/usr/lib64/', '/usr/lib/x86_64-linux-gnu/']:
        all_libs = os.listdir(crt_path)
        for file in all_libs:
            if file.startswith("crt") and (".o" in file) and file[3].isdigit():
                output.append(f"{crt_path}{file}")
                break
        else:
            continue
        break
    else:  # no break
        print(output)
        errors.error("Unable to find a valid crt file in '/lib/'")

    for file in output:
        errors.developer_info(f"found crt file: {file}")

    return output + [compile_runtime()]


def link_all(file: str, objects: list[str],
             additional_args: list[str] = []) -> str:
    '''detect host machine and run the correct linking function.
    Return output file name'''
    system = platform.system()

    if system == "Linux":
        link_linux(file, objects, additional_args)
        return file

    if system == "Windows":
        link_windows(file, objects, additional_args)
        return file.replace("/", "\\")[1:]+'.exe'

    errors.error("Linking is currently unsupported on Non-Linux platforms.\n" +
                 "Even on linux platforms, linking may fail.\n" +
                 "If you encounter bugs, use --emit-object and your own " +
                 "linker.")
    return ""  # needed for the IDE to not freak out.
