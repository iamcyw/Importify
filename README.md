# Importify



一个从网易云导出歌单到Spotify的简陋脚本。初衷是大致比较自己的网易云歌单里的歌在Spotify美区和港区的资源情况。

严格匹配，必须要歌名和歌手名完全相同才匹配成功，所以歌名后有括号简介、歌手一人以上、华语歌手在Spotify里为英文名等情况都会匹配失败。



## 使用

1. 安装依赖

   `pip3 install zhconv requests pyquery`

2. 获取spotify帐号的user id，access token

   进入[spotify web api console](https://developer.spotify.com/web-api/console/get-playlists/)，点击 `GET OAUTH TOKEN`，选择`playlist-modify-public`和`playlist-modify-private`。点击`request token`后登陆自己帐号，跳转回控制台页面后`Owner ID`一栏即`User ID`，`OAuth Token`即`access token`。

   填入`migrate.py`相应区域：

   ```python
   user_id = ''  # user id
   access_token = ''  # access token
   ```

3. 获取网易云歌单页面HTML

   进入将导入歌单的页面，复制页面`<body>`字段，在`migrate.py`同文件夹下新建`<新歌单名>.html`。

4. 运行脚本

   `python3 migrate.py <html文件>`

   生成日志文件`log.txt`，记录匹配成功歌曲，匹配失败歌曲。

   ​

   ​

如果只想搜索资源情况而不在Spotify上新建歌单，可以在脚本尾部修改：

`migrate(log, user_id, access_token, songs, playlist_name, add=True)`

====>

`migrate(log, user_id, access_token, songs, playlist_name, add=False)`

