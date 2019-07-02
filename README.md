### 自动设置nxp mcu dhcp server config

### 功能说明
- 一次性新部署板卡，根据插入板卡数量，DHCP网段从100开始顺序递增
- 部署过程中，出现有问题板卡无法设置，移除问题板卡，重新运行脚本部署
- 部署过程中，出现问题板卡，移除问题板卡，更换新的板卡，重新运行脚本部署
- 使用过程中，更换板卡，重新运行脚本部署

### 注意事项
- 板卡的插拔需要在服务器断电的情况下操作，不支持热插拔
- 测试发现板卡数量增加后，ifconfig down/up 生效的时间很长，所以脚本里面有很多延时，请耐心等等
- Debian 9.8 网络启动或重启如果有这条错误, 需要更新 realtek firmware, 我们测试发现，这个错误也会导致网络生效变慢
  错误“firmware : failed to load rtl_nic/rtl18168h-2.fw(-2)”

  更新地址：https://packages.debian.org/stretch/all/firmware-realtek/download

  下载包 **firmware-realtek_20161130-5_all.deb** 安装
