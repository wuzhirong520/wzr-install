rm /data/zr
ln -s /home/user/wuzhirong/wzr-install/vm/usr/bin /data/zr
sed -i s:/usr/bin:/data/zr: "./vm/usr/bin/Xvfb"