import os
import platform

from llvmlite import binding

import errors

#* Example of what the lld command *should* look like (linux)
#* ===========================================================
# binding.lld.lld_linux(f"{loc}",
#     [
#         "/usr/lib64/crt1.o", "/usr/lib64/crti.o",
#         "/usr/lib64/gcc/x86_64-pc-linux-gnu/12.2.1/crtbegin.o", f"{loc}.o",
#         "/usr/lib64/gcc/x86_64-pc-linux-gnu/12.2.1/crtend.o",
#         "/usr/lib64/crtn.o"
#     ], 
#     [
#         "-Bdynamic", "-no-pie", "--build-id", "--dynamic-linker",
#         "/lib64/ld-linux-x86-64.so.2", "-L/usr/lib/gcc/x86_64-pc-linux-gnu/12.2.1/",
#         "-L/usr/lib/", "-L/usr/lib64/", "-L/lib/", "-L/lib64/", "-lc"
#     ]
# )


def link_linux(file: str, objects: list[str], additional_args: list[str] = []):
    '''Linking for linux from a linux host machine'''
    binding.lld.lld_linux(file,
            [
                *get_linuxcrt(), *objects,
            ], 
            [
                "-Bdynamic", "-no-pie", "--build-id", "--dynamic-linker",
                "/lib64/ld-linux-x86-64.so.2", f"-L{get_gcc_dir()}/",
                "-L/usr/lib/", "-L/usr/lib64/", "-L/lib/", "-L/lib64/", "-lc" #? what happens on 32 bit
            ] + additional_args
        )

def get_gcc_dir(lib_dir = 'lib') -> str:
    '''get the gcc directory'''
    if not os.path.exists(f"/usr/{lib_dir}/gcc/"):
        errors.error(f"Directory '/usr/{lib_dir}/gcc/' does not exist. Aborting linking process")
    
    gcc_targets = os.listdir(f"/usr/{lib_dir}/gcc/")
    if len(gcc_targets) > 1:
        errors.inline_warning(f"Found more than one directory inside '/usr/{lib_dir}/gcc' \
                              defaulting to the first one: {gcc_targets[0]}")
    gcc_target = gcc_targets[0]
    gcc_versions = os.listdir(f"/usr/{lib_dir}/gcc/{gcc_target}")
    if len(gcc_versions) > 1:
        errors.inline_warning(f"Found more than one directory inside '/usr/{lib_dir}/gcc/{gcc_target}' \
                              defaulting to the first one: {gcc_versions[0]}")
    
    gcc_version = gcc_versions[0]
    return f"/usr/lib/gcc/{gcc_target}/{gcc_version}"

def get_linuxcrt() -> list[str]:
    '''get CRT files on linux platform'''
    gcc_dir = get_gcc_dir("lib64")
    all_files = os.listdir(gcc_dir)
    output = []
    exclude = ("crtfastmath", "crtprec32", "crtprec64", "crtprec80",
               "crtbeginT", "crtbeginS", "crtendS", "crtendT")
    
    # note: this *could* be a one-liner, it would just be ugly.
    for file in all_files:
        if '.' not in file: continue
        name, ext = file.split('.')
        if ext!='o': # skip non .o files
            continue
        if name.startswith('crt') and name not in exclude:
            
            output.append(f'{gcc_dir}/{file}')

    all_libs = os.listdir('/lib/')
    for file in all_libs:
        if file.startswith("crt") and (".o" in file) and file[3].isdigit():
            output.append(f"/lib/{file}")
            break
    else: # no break
        errors.error("Unable to find a valid crt file in '/lib/'")

    for file in output:
        errors.developer_info(f"found crt file: {file}")

    return output


def link_all(file: str, objects: list[str], additional_args: list[str] = []) -> str:
    '''detect host machine and run the correct linking function. Return output file name'''
    system = platform.system()

    if system == "Linux":
        link_linux(file, objects, additional_args)
        return file
    
    errors.error("Linking is currently unsupported on Non-Linux platforms.\n\
                  Even on linux platforms, linking may fail.\n\
                  If you encounter bugs, use --emit-object and your own linker.")
    return "" # needed for the IDE to not freak out.