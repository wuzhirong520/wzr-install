import os
import re
import json
from tqdm import tqdm
from datetime import datetime
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
    def __init__(self, package_name, version, filename, url):
        self.package_name = package_name
        self.version = version
        self.filename = filename
        self.url = url
    def __str__(self):
        s = f"Deb : {self.package_name}, version={self.version}, url={self.url}"
        return s

class PackageInstaller:
    def __init__(self, is_load_meta=True, is_update_from_url = False):
        self.arch_name = "amd64"
        self.mirror_url = "https://mirrors.pku.edu.cn/ubuntu/"
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
            self.debs_meta = self.get_all_debs_meta()
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
         
    def get_all_debs_meta(self):
        debs_meta = {}
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
            if package.package_name not in self.sys_installed_debs.keys():
                return False
            return self.check_deb_version(self.sys_installed_debs[package.package_name], package)
            return True
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
            no_found_packages.append(package)
            self.logging(f"Error {package} Is Not Found !!!")
            return debs_to_install, no_found_packages
        debs_to_install[package.package_name] = deb
        res = self.get_deb_info(deb)
        # print(res)
        depends_strings = re.findall(r'Depends: (.*?)\n', res)
        if len(depends_strings) > 0:
            depends_string = depends_strings[0]
            depends = str(depends_string).split(', ')
            depends = [d.split(' | ') for d in depends]
            # print(depends)
            for depend in depends:
                depend_package_name = depend[0].split(' ')[0]
                depend_version_strings = re.findall(r'\((.*?)\)', depend[0])
                depend_version_string = depend_version_strings[0] if len(depend_version_strings)>0 else None
                depend_package = Package(depend_package_name)
                if depend_version_string is not None:
                    depend_version_info = depend_version_string.split(' ')
                    depend_package.version = depend_version_info[1]
                    depend_package.version_cmp = depend_version_info[0]
                    depend_package.version = depend_package.version.split(':')[-1]
                # print(depend_package_name, depend_version_strings)
                debs_to_install, no_found_packages = self.get_debs_to_install(depend_package, debs_to_install, no_found_packages)
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
        meta_gz_file_name = "ls-lR.gz"
        download_file_with_progress(self.mirror_url + meta_gz_file_name, os.path.join(self.meta_dir, meta_gz_file_name))
        os.system(f"gzip -df {os.path.join(self.meta_dir, meta_gz_file_name)}")
        self.logging_section_end()
