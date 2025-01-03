from utils import *
import sys
from package_installer import Package, PackageInstaller

args = sys.argv[1:]
n_args = len(args)

# print(n_args, args)

if n_args<1 :
    raise ValueError("Please Passing Parameters")

if args[0]=="update":
    installer = PackageInstaller(is_load_meta=False, is_update_from_url=True)
elif args[0]=="install":
    installer = PackageInstaller()
    pkgs = args[1:]
    for p in pkgs:
        package = Package(p)
        cmp_list = [">=","<=","=",">>", "<<"]
        for c_i in range(len(cmp_list)):
            c = cmp_list[c_i]
            if p.find(c) >= 0:
                package.package_name = p.split(c)[0]
                package.version = p.split(c)[1]
                package.version_cmp = c
                break
        installer.install_package(package)
elif args[0]=="uninstall":
    installer = PackageInstaller()
    pkgs = args[1:]
    for p in pkgs:
        installer.uninstall_package(p)
elif args[0]=="list":
    installer = PackageInstaller()
    package_name = args[1]
    if package_name not in installer.debs_meta.keys():
        print(f"No Found {package_name}")
    else:
        pkgs = installer.debs_meta[package_name]
        for p in pkgs:
            print(f"{p}")
else:
    raise ValueError(f"Invalid Option : {args[0]}")