import os
import re

root_path = os.path.dirname(os.path.dirname(__file__))

vm_dir = os.path.join(root_path,"vm")
os.makedirs(vm_dir, exist_ok=True)
os.makedirs(os.path.join(vm_dir,"usr"), exist_ok=True)
os.makedirs(os.path.join(vm_dir,"usr/bin"), exist_ok=True)
os.makedirs(os.path.join(vm_dir,"usr/include"), exist_ok=True)
os.system(f"cp -r /usr/bin/* {os.path.join(vm_dir,"usr/bin")}")
os.system(f"cp -r /usr/include/* {os.path.join(vm_dir,"usr/include")}")

print("Root Dir : ", root_path)

print("")
# s  = f"export PATH=$PATH:{root_path}/bin:{root_path}/vm/usr/bin:{root_path}/vm/usr/local/bin\n"
# s += f"export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:{root_path}/vm/usr/lib:{root_path}/vm/usr/local/lib:{root_path}/vm/usr/lib/x86_64-linux-gnu\n"
# s += f"export C_INCLUDE_PATH=$C_INCLUDE_PATH:{root_path}/vm/usr/include\n"
# s += f"export CPLUS_INCLUDE_PATH=$CPLUS_INCLUDE_PATH:{root_path}/vm/usr/include\n"
# s += f"export MANPATH=$MANPATH:{root_path}/vm/usr/share/man\n"

s  = f"export PATH={root_path}/bin:{root_path}/vm/usr/bin:{root_path}/vm/usr/local/bin\n"
s += f"export LD_LIBRARY_PATH={root_path}/vm/usr/lib:{root_path}/vm/usr/local/lib:{root_path}/vm/usr/lib/x86_64-linux-gnu\n"
s += f"export C_INCLUDE_PATH={root_path}/vm/usr/include\n"
s += f"export CPLUS_INCLUDE_PATH={root_path}/vm/usr/include\n"
s += f"export MANPATH={root_path}/vm/usr/share/man\n"

print(s)

header = "\n################ WZR install Tools ###################\n"
tailer = "######################################################\n"

user_home = os.path.expanduser("~")
bashrc_path = os.path.join(user_home, ".bashrc")

if os.path.exists(bashrc_path):
    with open(os.path.join(user_home, ".bashrc"),"r") as f:
        bashrc_data = f.read()
else:
    bashrc_data = ""


# print(bashrc_data)

if bashrc_data.find(header)>=0:
    newbashrc_data = re.sub(f'{header}.*?{tailer}', f'{header}{s}{tailer}', bashrc_data, flags=re.DOTALL)
else:
    newbashrc_data = bashrc_data + header + s + tailer

# print(newbashrc_data)

# with open(os.path.join(user_home, ".bashrc"),"w") as f:
#     f.write(newbashrc_data)