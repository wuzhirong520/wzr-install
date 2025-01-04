import os
import re
import json
from tqdm import tqdm
from datetime import datetime
import urllib.parse
from utils import *

class Package:
    def __init__(self, package_name, version=None, version_cmp=None):
        self.package_name = package_name
        self.version = version
        self.version_cmp = version_cmp
    def __str__(self):
        s = f"Package : {self.package_name}"
        if self.version is not None:
            s += f", version {self.version_cmp} {self.version}"
        return s

class Deb:
    def __init__(self, package_name, version, filename, url, depends = [], provides = []):
        self.package_name = package_name
        self.version = version
        self.filename = filename
        self.url = url
        self.depends = depends
        self.provides = provides
    def __str__(self):
        s = f"Deb : {self.package_name}, version={self.version}, url={self.url},"
        if len(self.depends)>0:
            s += " Depends="
            for d in self.depends:
                s += f"[{d}],"
        if len(self.provides)>0 :
            s += " Provides="
            for p in self.provides:
                s += f"[{p}],"
        return s

class PackageInstaller:
    def __init__(self, is_load_meta=True, is_update_from_url = False):
        self.arch_name = "amd64"
        # self.ubuntu_names = ["jammy","jammy-backports", "jammy-proposed", "jammy-security", "jammy-updates"]
        self.ubuntu_names = ["jammy"]
        self.channels = ["main", "multiverse", "restricted", "universe"]
        # self.mirror_url = "https://mirrors.pku.edu.cn/ubuntu/"
        self.mirror_url = "https://mirrors.tuna.tsinghua.edu.cn/ubuntu/"
        # self.mirror_url = "http://mirrors.ustc.edu.cn/ubuntu/"
        self.root_path = os.path.dirname(os.path.dirname(__file__))
        self.meta_dir = os.path.join(self.root_path, "meta")
        self.debs_download_dir = os.path.join(self.root_path, "debs")
        self.debs_installs_dir = os.path.join(self.root_path, "installs")
        self.vm_dir = os.path.join(self.root_path, "vm")
        self.section_bar_len = max(os.get_terminal_size().columns,100)
        os.makedirs(self.meta_dir, exist_ok=True)
        os.makedirs(self.debs_download_dir, exist_ok=True)
        os.makedirs(self.debs_installs_dir, exist_ok=True)
        os.makedirs(self.vm_dir, exist_ok=True)
        if is_update_from_url:
            self.update_meta_from_mirror_url()
        if is_load_meta:
            self.logging_section_bar("Loading Deb Meta Info")
            self.debs_meta, self.debs_provides_meta = self.get_all_debs_meta()
            self.sys_installed_debs = self.get_all_debs_system_installed()
            self.wzr_installed_debs = self.get_all_debs_wzr_installed()
            self.logging_section_end()

    def logging_section_bar(self, sec_name : str):
        n = len(sec_name)
        n1 = (self.section_bar_len - n)//2
        n2 = self.section_bar_len - n - n1
        s = ""
        for i in range(n1):
            s+="="
        s+=sec_name
        for i in range(n2):
            s+="="
        print(s)

    def logging_section_end(self):
        s = ""
        for i in range(self.section_bar_len):
            s+="="
        s+='\n'
        print(s)
    
    def logging(self, *args, **kwargs):
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{formatted_datetime}] : ", end="")
        print(*args, **kwargs)
         
    def parse_pacakges_string(self, depends_string):
        deb_depends = []
        depends = str(depends_string).split(', ')
        depends = [d.split(' | ') for d in depends]
        # print(depends)
        for depend in depends:
            depend_package_name = depend[0].split(' ')[0]
            depend_package_name = str(depend_package_name).replace(":any","")
            depend_version_strings = re.findall(r'\((.*?)\)', depend[0])
            depend_version_string = depend_version_strings[0] if len(depend_version_strings)>0 else None
            depend_package = Package(depend_package_name)
            if depend_version_string is not None:
                depend_version_info = depend_version_string.split(' ')
                depend_package.version = depend_version_info[1]
                depend_package.version_cmp = depend_version_info[0]
            # print(depend_package_name, depend_version_strings)
            deb_depends.append(depend_package)
        return deb_depends

    def get_all_debs_meta(self):
        self.logging("Loading all debs from mirror...")
        debs_meta = {}
        debs_provides_meta = {}
        n = 0
        n_provides = 0
        for ubuntu_name in self.ubuntu_names:
            for channel in self.channels:
                meta_file_path = os.path.join(self.meta_dir, f"{ubuntu_name}/{channel}")
                with open(meta_file_path, "r") as f:
                    while True:
                        line = f.readline()
                        if line=="":
                            break
                        line = line[:-1]
                        if line.startswith("Package: "):
                            package_name = line[9:]
                            deb_depends = []
                            provides = []
                            version = ""
                            url = ""
                            while True:
                                line = f.readline()
                                if line=="\n" or line=="":
                                    break
                                line = line[:-1]
                                if line.startswith("Version: "):
                                    version = line[9:]
                                if line.startswith("Filename: "):
                                    url = line[10:]
                                if line.startswith("Depends: "):
                                    depends_string = line[9:]
                                    deb_depends = self.parse_pacakges_string(depends_string)
                                if line.startswith("Provides: "):
                                    provides_string = line[10:]
                                    provides = self.parse_pacakges_string(provides_string)
                            filename = url.split('/')[-1]
                            deb = Deb(package_name, version, filename, url, deb_depends, provides)
                            # print(deb)
                            if package_name not in debs_meta.keys():
                                debs_meta[package_name]=[]
                            debs_meta[package_name].append(deb)
                            n += 1
                            for p in provides:
                                if p.package_name not in debs_provides_meta.keys():
                                    debs_provides_meta[p.package_name] = []
                                debs_provides_meta[p.package_name].append(
                                    {
                                        "version" : p.version,
                                        "package" : Package(package_name, version, version_cmp="=")
                                    }
                                )
                                n_provides += 1
        self.logging(f"Loaded {len(debs_meta)} packages, {n} deb files, provides {n_provides} packages")
        return debs_meta, debs_provides_meta

        base_url = ""
        meta_file_path = os.path.join(self.meta_dir,"ls-lR")
        if not os.path.exists(meta_file_path):
            self.update_meta_from_mirror_url()
        n = 0
        self.logging("Loading all debs from mirror...")
        with open(meta_file_path, "r") as f, tqdm(
                total=os.path.getsize(meta_file_path),
                unit='B',
                unit_scale=True,
            ) as bar:
            while True:
                line = f.readline()
                if line=="":
                    break
                bar.update(len(line))
                line = line[:-1]
                # print(line)
                if line.endswith(':'):
                    base_url = line[:-1]
                if line.endswith(f'{self.arch_name}.deb') or line.endswith(f'all.deb'):
                    deb_name = line.split(' ')[-1]
                    name = deb_name.split('_')[0]
                    version = deb_name.split('_')[1]
                    # version = urllib.parse.unquote(version)
                    url = base_url[2:]+'/'+deb_name
                    deb = Deb(name, version, deb_name, url)
                    if name not in debs_meta.keys():
                        debs_meta[name]=[]
                    debs_meta[name].append(deb)
                    n += 1
        self.logging(f"Loaded {len(debs_meta)} packages, {n} deb files")
        return debs_meta

    def get_all_debs_wzr_installed(self):
        self.logging("Loading wzr installed debs ... ")
        meta_file_path = os.path.join(self.meta_dir, "wzr_installed.json")
        if not os.path.exists(meta_file_path):
            return {}
        with open(meta_file_path, "r") as f:
            pkgs = json.load(f)
        pkgs_ = {}
        for k,v in pkgs.items():
            pkgs_[k] = Deb(k,v['version'],v['filename'],v['url'])
        self.logging(f"Loaded {len(pkgs_)} debs")
        return pkgs_

    def get_all_debs_system_installed(self):
        self.logging("Loading all system installed debs ... ")
        res = run_command(f"dpkg -l | grep \'ii \'")
        res = str(res).split('\n')
        pkgs = {}
        for r in res:
            s = str(r).split(' ')
            pp = []
            for p in s:
                if len(p)>0:
                    pp.append(p)
            pp = pp[1:3]
            if len(pp):
                name = pp[0].split(':')[0]
                version = pp[1].split(':')[-1]
                deb = Deb(name, version, None, None)
                pkgs[name]=deb
        self.logging(f"Loaded {len(pkgs)} debs")
        return pkgs

    def check_deb_version(self, deb: Deb, package: Package):
        if package.version is None:
            return True
        c = cmp_version(deb.version, package.version)
        if c==0 and package.version_cmp=="=":
            return True
        elif c>=0 and package.version_cmp==">=":
            return True
        elif c<=0 and package.version_cmp=="<=":
            return True
        elif c==-1 and package.version_cmp=="<<":
            return True
        elif c>0 and package.version_cmp==">>":
            return True
        return False

    def get_deb_of_package(self, package : Package):
        if package.package_name not in self.debs_meta.keys():
            return None
        debs_of_package = self.debs_meta[package.package_name]
        for d in debs_of_package:
            print(d)
        selected_debs = []
        if package.version is not None and package.version_cmp is not None:
            for deb in debs_of_package:
                if self.check_deb_version(deb, package):
                    selected_debs.append(deb)
        else:
            selected_debs = debs_of_package
        max_version_deb = None
        for deb in selected_debs:
            if max_version_deb is None:
                max_version_deb = deb
            else:
                c = cmp_version(deb.version, max_version_deb.version)
                if c>=0:
                    max_version_deb = deb
        return max_version_deb
        
    def check_installed(self, package : Package):
        if package.package_name not in self.wzr_installed_debs.keys():
            return False
            if package.package_name not in self.sys_installed_debs.keys():
                return False
            return self.check_deb_version(self.sys_installed_debs[package.package_name], package)
        else:
            return self.check_deb_version(self.wzr_installed_debs[package.package_name], package)

    def get_deb_info(self, deb: Deb):
        deb_download_path = os.path.join(self.debs_download_dir, deb.filename)
        res = run_command(f"dpkg-deb --info \'{deb_download_path}\'")
        if res == "" :
            download_file_with_progress(self.mirror_url+deb.url, deb_download_path)
            res = run_command(f"dpkg-deb --info \'{deb_download_path}\'")
        return res
    
    def get_debs_to_install(self, package : Package, debs_to_install : dict = {}, no_found_packages : list = []):
        if package.package_name in debs_to_install.keys():
            if self.check_deb_version(debs_to_install[package.package_name], package):
                return debs_to_install, no_found_packages
        if self.check_installed(package):
            return debs_to_install, no_found_packages
        self.logging(f"{package} Not Installed")
        deb = self.get_deb_of_package(package)
        if deb is None:
            if package.package_name in self.debs_provides_meta.keys():
                p = self.debs_provides_meta[package.package_name][0]['package']
                return self.get_debs_to_install(p,debs_to_install,no_found_packages)
        if deb is None:
            no_found_packages.append(package)
            self.logging(f"Error {package} Is Not Found !!!")
            return debs_to_install, no_found_packages
        debs_to_install[package.package_name] = deb
        info = self.get_deb_info(deb)
        for depends in deb.depends:
            debs_to_install, no_found_packages = self.get_debs_to_install(depends, debs_to_install, no_found_packages)
        return debs_to_install, no_found_packages
    
    def uninstall_deb(self, package_name):
        deb_install_path = os.path.join(self.debs_installs_dir, package_name)
        if not os.path.exists(deb_install_path):
            return
        res = run_command(f"cd \'{deb_install_path}\' && find . -type f -o -type l")
        res = res.split('\n')
        res = [r[2:] for r in res if len(r)>0]
        # print(res)
        for p in res:
            path = os.path.join(self.vm_dir, p)
            run_command(f"rm -f \'{path}\'")
        run_command(f"rm -rf \'{deb_install_path}\'")
    
    def uninstall_package(self, package_name):
        self.logging_section_bar(f"Uninstalling {package_name}")
        if package_name not in self.wzr_installed_debs.keys():
            self.logging(f"{package_name} not Found")
        else:
            self.wzr_installed_debs.pop(package_name)
            self.uninstall_deb(package_name)
            self.logging(f"{package_name} uninstalled")
        self.logging_section_end()
        self.update_wzr_installed_pkgs_meta()
    
    def update_wzr_installed_pkgs_meta(self):
        wzr_installed_debs_json = {}
        for k,v in self.wzr_installed_debs.items():
            wzr_installed_debs_json[k]={
                'version':v.version,
                'filename':v.filename,
                'url':v.url,
            }
        with open(os.path.join(self.meta_dir,"wzr_installed.json"),"w") as f:
            json.dump(wzr_installed_debs_json, f, indent=2)

    def install_debs(self, debs_to_install : dict):
        for deb in debs_to_install.values():
            self.logging(f"Installing {deb}")
            deb_download_path = os.path.join(self.debs_download_dir, deb.filename)
            deb_install_path = os.path.join(self.debs_installs_dir, deb.package_name)
            self.uninstall_deb(deb.package_name)
            run_command(f"dpkg -x \'{deb_download_path}\' \'{deb_install_path}\'")
            run_command(f"cp -r {deb_install_path}/* {self.vm_dir}/")
        for k,v in debs_to_install.items():
            self.wzr_installed_debs[k] = v
        self.update_wzr_installed_pkgs_meta()
            
    def install_package(self, package : Package):
        self.logging_section_bar(f"Solving Depends of {package}")
        depends, nofound = self.get_debs_to_install(package)
        if len(depends)==0 and len(nofound)==0:
            self.logging(f"{package} has already installed")
            self.logging_section_end()
            return
        if len(nofound)>0:
            self.logging("The Following Packages Not Found : ")
            for nf in nofound:
                self.logging(f"       {nf}")
            if len(depends)==0:
                self.logging_section_end()
                return
            else:
                self.logging("Do you want to ignore them, and install the founded pacakges ? (Y/N)")
                c = input()
                if c.lower()!="y":
                    self.logging_section_end()
                    return
        self.logging_section_end()
        self.logging_section_bar(f"Installing All Packages")
        self.install_debs(depends)
        self.logging_section_end()

    def update_meta_from_mirror_url(self):
        self.logging_section_bar("Updating Meta Info from Mirror URL")
        # meta_gz_file_name = "ls-lR.gz"
        # download_file_with_progress(self.mirror_url + meta_gz_file_name, os.path.join(self.meta_dir, meta_gz_file_name))
        # os.system(f"gzip -df {os.path.join(self.meta_dir, meta_gz_file_name)}")
        for ubuntu_name in self.ubuntu_names:
            meta_save_dir = os.path.join(self.meta_dir,ubuntu_name)
            os.makedirs(meta_save_dir, exist_ok=True)
            for channel in self.channels:
                meta_url = self.mirror_url + "dists/" + ubuntu_name + "/" + channel + "/binary-" + self.arch_name + "/Packages.gz"
                # print(meta_url)
                meta_save_path = os.path.join(meta_save_dir, f"{channel}.gz")
                # print(meta_save_path)
                download_file_with_progress(meta_url, meta_save_path)
                os.system(f"gzip -df {meta_save_path}")
        
        self.logging_section_end()
