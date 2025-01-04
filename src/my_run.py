import sys
import os
import subprocess

args = sys.argv[1:]
n_args = len(args)

# print(n_args, args)

if n_args<1 :
    raise ValueError("Please Passing Parameters")

root_path = os.path.dirname(os.path.dirname(__file__))
# print(root_path)

current_env = os.environ.copy()


# current_env["PATH"] += ":" + os.path.join(root_path,"vm/usr/bin")
current_env["PATH"] = os.path.join(root_path,"vm/usr/bin")
current_env["PATH"] += ":" + os.path.join(root_path,"vm/bin")

current_env["LD_LIBRARY_PATH"] = os.path.join(root_path,"vm/usr/lib")
current_env["LD_LIBRARY_PATH"] += ":" + os.path.join(root_path,"vm/usr/lib/x86_64-linux-gnu")
current_env["LD_LIBRARY_PATH"] += ":" + os.path.join(root_path,"vm/lib/x86_64-linux-gnu")
current_env["LD_LIBRARY_PATH"] += ":" + os.path.join(root_path,"vm/usr/lib64")
current_env["LD_LIBRARY_PATH"] += ":" + os.path.join(root_path,"vm/lib")
current_env["LD_LIBRARY_PATH"] += ":" + os.path.join(root_path,"vm/lib64")

current_env["C_INCLUDE_PATH"] = os.path.join(root_path,"vm/usr/include")
current_env["CPLUS_INCLUDE_PATH"] = os.path.join(root_path,"vm/usr/include")
current_env["MANPATH"] = os.path.join(root_path,"vm/usr/share/man")

current_env["CMAKE_PREFIX_PATH"] = os.path.join(root_path,"vm/usr")

current_env["LD_LIBRARY_PATH"] += ":/home/user/wuzhirong/CUDA/cuda_12.3.0/lib64"
current_env["PATH"] += ":/home/user/wuzhirong/CUDA/cuda_12.3.0/bin"
current_env["CUDA_HOME"] = "/home/user/wuzhirong/CUDA/cuda_12.3.0"

# current_env["C_INCLUDE_PATH"] += ":" + os.path.join(root_path,"vm/usr/include/gtk-3.0")
# current_env["CPLUS_INCLUDE_PATH"] += ":" + os.path.join(root_path,"vm/usr/include/gtk-3.0")
# current_env["C_INCLUDE_PATH"] += ":" + os.path.join(root_path,"vm/usr/include/glib-2.0")
# current_env["CPLUS_INCLUDE_PATH"] += ":" + os.path.join(root_path,"vm/usr/include/glib-2.0")

current_env["C_INCLUDE_PATH"] += ":" + os.path.join(root_path,"vm/usr/lib/x86_64-linux-gnu/glib-2.0/include")
current_env["CPLUS_INCLUDE_PATH"] += ":" + os.path.join(root_path,"vm/usr/lib/x86_64-linux-gnu/glib-2.0/include")

def add_include(include_path):
    if not os.path.exists(include_path):
        return
    for entry in os.scandir(include_path):
        if entry.is_dir():
            include_path_ = entry.path
            if include_path_.find("x86_64-linux-gnu")>=0 or include_path_.find("linux") < 0:
                current_env["C_INCLUDE_PATH"] += ":" + include_path_
                current_env["CPLUS_INCLUDE_PATH"] += ":" + include_path_
            # add_include(include_path_)

add_include(os.path.join(root_path,"vm/usr/include"))


# print(current_env["PATH"])
# print(current_env["LD_LIBRARY_PATH"])

# s += f"export LD_LIBRARY_PATH={root_path}/vm/usr/lib:{root_path}/vm/usr/local/lib:{root_path}/vm/usr/lib/x86_64-linux-gnu\n"
# s += f"export C_INCLUDE_PATH={root_path}/vm/usr/include\n"
# s += f"export CPLUS_INCLUDE_PATH={root_path}/vm/usr/include\n"
# s += f"export MANPATH={root_path}/vm/usr/share/man\n"

# command = "ldd --version"

print(args)

result = subprocess.run(
            args,
            shell=False,
            env=current_env
        )