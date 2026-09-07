bypy-next - Python client for Baidu Yun (Personal Cloud Storage) 百度云/百度网盘Python客户端
====================================================================================

极简说明
-------

- 安装: `pip install bypy-next`
- 运行: `bypy`

TL;DR
-----

- To install: `pip install bypy-next`
- To use: `bypy`

本项目是 [houtianze/bypy](https://github.com/houtianze/bypy) 的分叉，发布名为 `bypy-next`，命令仍为 `bypy` / `bypygui`，Python 导入仍为 `from bypy import ByPy`。保留原项目的 MIT 许可证和版权声明。请使用独立虚拟环境，不要与原版 `bypy` 同时安装。

This fork is distributed as `bypy-next`, retaining the `bypy` module and command names. Install it in a separate environment from the original `bypy`. See [PUBLISHING.md](PUBLISHING.md) for build and release instructions.

---

bypy-next 分叉说明 / About this fork
------------------------------------

本分叉在原版基础上修复/增强了以下两点：

1. **修复分片上传与秒传**：百度已下线旧 PCS 上传接口（分片上传 `upload&type=tmpfile` 恒返回 `31064 file is not authorized`，秒传 `method=rapidupload` 恒返回 `31023 param error`）。现已按[百度官方文档](https://pan.baidu.com/union/doc)迁移到 xpan 新流程：`precreate` → `locateupload` → `superfile2`（带 `uploadid`/`partseq`）→ `create`；秒传改由 `precreate` 实现（`return_type == 2` 即命中）；默认分片大小改为 4MB（普通用户的限制，会员可用 `--slice` 调大）；断点续传改为服务端方案——保存 `uploadid`，重跑时 `precreate` 会只返回剩余分片。
2. **分片并发上传**：新增 `--upload-threads N` 选项（默认 4），单文件的分片并发上传；实测 100MB 文件从 22s 降至 6s（约 3.7x）。`--upload-threads 1` 可回到串行。

This fork contains two changes on top of the original bypy:

1. **Fix broken slice upload / rapidupload** by migrating to the current xpan API (`precreate` → `locateupload` → `superfile2` with `uploadid`/`partseq` → `create`). Rapid-upload now goes through `precreate`, the default slice size is 4MB (required for normal users), and resumable upload is handled server-side via `uploadid`.
2. **Parallel slice upload**: new `--upload-threads N` option (default: 4) uploads the slices of a single file concurrently (~3.7x faster in a 100MB test). Use `--upload-threads 1` for the old sequential behavior.

跳过秒传尝试 / Skip the initial rapid-upload attempt:

```bash
python -m bypy --skip-rapid-upload upload ./example.zip /example.zip
```

`--skip-rapid-upload` 跳过客户端额外的秒传尝试，直接走普通上传，适用于文件上传、目录上传和 `syncup`。默认仍先尝试秒传，不能与 `--rapid-upload-only` 同时使用。大文件分片上传必需的 `precreate` 仍可能由服务端命中秒传，因此此选项不保证传输全部字节。Python 调用可使用 `ByPy(skip_rapid_upload=True)`。

This option skips the client's initial rapid-upload attempt for file/directory uploads and `syncup`. It is mutually exclusive with `--rapid-upload-only`. Required slice precreation can still deduplicate on the server; this does not force every byte to be transferred. Python callers can use `ByPy(skip_rapid_upload=True)`.

---

授权与应用凭据 / Authorization and application credentials
----------------------------------------------------------

客户端直接调用百度 OAuth 接口完成授权码兑换和 token 刷新，用户 token 默认保存在本机 `~/.bypy/bypy.json`。

**`bypy-next` 暂时沿用原仓库 `houtianze/bypy` 内置的 API Key 和 SecretKey，并非本分叉独立申请的百度应用。** 这些默认凭据来自上游 2022 年 9 月 1 日的提交 `108e289`（`No more server auth`）。本分叉的默认授权能力仍依赖该上游应用及其凭据保持可用。

如使用自己的百度应用，可在启动前通过 `BAIDU_API_KEY` 和 `BAIDU_API_SECRET` 环境变量覆盖凭据，并将 `bypy/const.py` 中的 `AppPcsPath` 改成该应用对应的目录。两项凭据均须非空。应用 SecretKey 与用户授权后生成的 access token / refresh token 是不同的凭据。

The client exchanges authorization codes and refreshes tokens directly with Baidu OAuth. User tokens are stored locally in `~/.bypy/bypy.json` by default. **For now, `bypy-next` reuses the API Key and SecretKey bundled in upstream `houtianze/bypy`; this fork does not have its own Baidu application.** The defaults come from upstream commit `108e289` dated September 1, 2022, and depend on that application's continued availability. To use your own app, set nonempty `BAIDU_API_KEY` and `BAIDU_API_SECRET` environment variables before startup and adjust `AppPcsPath` in `bypy/const.py` to your app's directory.

---

中文说明 (English readme is at the bottom)
-----------------------------------------

- 最新: 目录上传/下载/同步加入了多进程支持（`--processes`）

---
这是一个百度云/百度网盘的Python客户端。主要的目的就是在Linux环境下（Windows下应该也可用，但没有仔细测试过）通过命令行来使用百度云盘的2TB的巨大空间。比如，你可以用在Raspberry Pi树莓派上。它提供文件列表、下载、上传、比较、向上同步、向下同步，等操作。

**由于百度PCS API权限限制，程序只能存取百度云端`/apps/bypy`目录下面的文件和目录。**

**（已解决）~~据说百度PCS API最多返回目录下1000个文件（ #285 )，如果属实，百度云盘上若有超过1000个文件的目录，将有一部分文件无法被看到 / 下载~~**

**特征: 支持Unicode/中文；失败重试；递归上传/下载；目录比较; 哈希缓存。**

界面是英文的，主要是因为这个是为了Raspberry Pi树莓派开发的。

程序依赖
------

**重要：需要把系统的区域编码设置为UTF-8。（参见：<http://perlgeek.de/en/article/set-up-a-clean-utf8-environment>)**

安装
---

- 通过`pip`来安装：`pip install bypy-next` （本分叉当前声明 Python 3.8+）

运行
---

- 作为独立程序: 运行 `bypy` (或者`python -m bypy`，或者`python3 -m bypy`）

  可以看到命令行支持的全部命令和参数。
- 作为一个包，在代码中使用: `import bypy`

简单的图形界面：
运行 `bypygui`

基本操作
------

显示使用帮助和所有命令（英文）:

```bash
bypy
```

第一次运行时需要授权，只需跑任何一个命令（比如 `bypy info`）然后跟着说明（登陆等）来授权即可。授权只需一次，一旦成功，以后不会再出现授权提示.

更详细的了解某一个命令：

```bash
bypy help <command>
```

显示在云盘（程序的）根目录下文件列表：

```bash
bypy list
```

把当前目录同步到云盘：

```bash
bypy syncup
```

or

```bash
bypy upload
```

把云盘内容同步到本地来：

```bash
bypy syncdown
```

or

```bash
bypy downdir /
```

**比较本地当前目录和云盘（程序的）根目录（个人认为非常有用）：**

```bash
bypy compare
```

更多命令和详细解释请见运行`bypy`的输出。

调试
---

- 运行时添加`-v`参数，会显示进度详情。
- 运行时添加`-d`，会显示一些调试信息。
- 运行时添加`-ddd`，还会会显示HTTP通讯信息（**警告：非常多**）

整合测试（15 - 30分钟）
-------------------

- 在主目录下跑：`python -m bypy.test`

直接在Python程序中调用
-------------------

```python
from bypy import ByPy
bp=ByPy()
bp.list() # or whatever instance methods of ByPy class
```

经验分享
-------

请移步至[wiki](../../wiki)，方便分享/交流。

授权许可
-------

请阅: [LICENSE](LICENSE)

---

PCS API文档（已失效）: <http://developer.baidu.com/wiki/index.php?title=docs/pcs/rest/file_data_apis_list> (以前保存的离线版： [baidudoc](baidudoc) directory)

---

Introduction
------------

- Latest feature: Multiprocessing added to directory upload / download / sync（`--processes`）

---
This is a Python client for Baidu Yun (a.k.a PCS - Personal Cloud Storage), an online storage website offering 2 TB (fast) free personal storage. This main purpose is to be able to utilize this storage service under Linux environment (console), e.g. Raspberry Pi.

**Due to Baidu PC permission restrictions, this program can only access your `/apps/bypy` directory at Baidu PCS**

**(Fixed) ~~It's said the Baidu PCS API won't return more than 1000 items inside a directory ( #285 )，if this is true，you won't be able to see / download some files if you have a directory with more than 1000 files on Baidu Cloud~~**

**Features: Unicode / Chinese support; Retry on failures; Recursive down/up-load; Directory comparison; Hash caching.**

Prerequisite
------------

**Important: You need to set you system locale encoding to UTF-8 for this to work (You can refer here: <http://perlgeek.de/en/article/set-up-a-clean-utf8-environment>)**

Installation
------------

- `pip install bypy-next` (This fork currently requires Python 3.8+)

Usage
-----

- Standalone program
  - Simply run `bypy`  (or `python -m bypy`, or `python3 -m bypy`）
  You will see all the commands and parameters it supports

- As a package in your code
  - `import bypy`

Simple GUI:
Run `bypygui`

Getting started
---------------

To get help and a list of available commands:

```bash
bypy
```

To authorize for first time use, run any commands e.g. `bypy info` and follow the instructions (login etc). This is a one-time requirement only.

To get more details about certain command:

```bash
bypy help <command>
```

List files at (App's) root directory at Baidu PCS:

```bash
bypy list
```

To sync up to the cloud (from the current directory):

```bash
bypy syncup
```

or

```bash
bypy upload
```

To sync down from the cloud (to the current directory):

```bash
bypy syncdown
```

or

```bash
bypy downdir /
```

**To compare the current directory to (App's) root directory at Baidu PCS (which I think is very useful):**

```bash
bypy compare
```

To get more information about the commands, check the output of `bypy`.

Debug
-----

- Add in `-v` parameter, it will print more details about the progress.
- Add in `-d` parameter, it will print some debug messages.
- Add in `-ddd`, it will display HTTP messages as well (**Warning: A lot**）

Integration Test (15-30min)
--------------------------

- (In the project root directory) run: `python -m bypy.test`

To call from Python code
------------------------

```python
from bypy import ByPy
bp=ByPy()
bp.list() # or whatever instance methods of ByPy class
```

Tips / Sharing
--------------

Please go to [wiki](../../wiki)

License
---

Please refer to [LICENSE](LICENSE)

---

PCS API Document (link dead 404): <http://developer.baidu.com/wiki/index.php?title=docs/pcs/rest/file_data_apis_list> (Offline pdf retrieved before: [baidudoc](baidudoc) directory)
