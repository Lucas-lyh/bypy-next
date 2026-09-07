# 发布 bypy-next

发布名为 `bypy-next`；安装后的命令为 `bypy` / `bypygui`，导入包为 `bypy`。
不要与原版 `bypy` 安装到同一个环境。

## 配置与版本

`pyproject.toml` 是打包配置入口，版本从 `bypy/const.py` 的 `__version__` 读取，
运行依赖从 `requirements.txt` 读取。当前沿用版本 `1.8.9`，每次后续发布递增版本。
Python 最低版本为 3.8；发布工作流在 Python 3.8–3.14 上测试已安装的 wheel。构建工具在 Python 3.14 上运行。
证书是运行资源，需要随包发布；`bypy/test` 中的整合测试及授权配置不打包。

## 本地检查与构建

先安装 uv，然后在仓库根目录运行：

```bash
uv sync --locked
uv run --locked python -m unittest discover -s tests -v
./release.sh
```

脚本只构建并检查，不上传，不打 Git 标签。产物包含 wheel 和源码包，
每次输出至独立的 `dist/release.XXXXXXXX/`，避免混入旧版本。
应在独立环境安装本次 wheel，并在仓库外验证 `bypy -V`、`bypy --help` 和
`python -c 'from bypy import ByPy'`。从源码包再次构建 wheel 可检查源码分发是否完整。
不要运行旧的 `python -m bypy.test` 作为发布检查：它会操作真实网盘并删除应用目录内容。

## GitHub Actions 自动发布（推荐）

在 PyPI 的 Trusted Publisher / Pending Publisher 表单填写：

| 字段 | 值 |
| --- | --- |
| PyPI Project Name | `bypy-next` |
| Owner | `Lucas-lyh` |
| Repository name | `bypy-next` |
| Workflow name | `publish.yml` |
| Environment name | `pypi` |

Workflow name 是文件名，不是工作流内的 `name`，也不包含 `.github/workflows/` 前缀。
在 GitHub 仓库 Settings → Environments 中创建 `pypi` 环境。
将 `.github/workflows/publish.yml` 和发布代码提交推送至 GitHub 后，
可以在 Actions 手动运行工作流：手动运行只构建和测试，不上传。
正式发布时创建 GitHub Release，标签必须与版本对应，例如 `v1.8.9`。
发布 Release 后，工作流先构建、检查、测试 wheel，再通过 OIDC 上传正式 PyPI；不需要 API token。
这些字段必须与实际仓库、工作流和环境名称一致。

## 本地手动上传（API token 方式）

注册 PyPI / TestPyPI 账号并验证邮箱，设置双因素认证，创建各自平台的 API token。
首次新建项目使用账号范围 token；项目创建后可换用项目范围 token。
不要将 token 写入仓库。Twine 提示认证时输入 token；如果询问用户名，使用 `__token__`。

先上传 TestPyPI：

```bash
./release.sh testpypi
```

测试安装：先在独立环境从正式 PyPI 安装 `requirements.txt` 中的依赖，
再通过 `pip install --index-url https://test.pypi.org/simple/ --no-deps bypy-next==1.8.9`
安装测试包（后续发布替换版本号）。

确认后上传正式 PyPI：

```bash
./release.sh pypi
```

以上两个命令会重新构建并上传。如果要上传已经验证过的同一批产物，使用其具体目录：

```bash
uv tool run twine upload --repository testpypi dist/release.XXXXXXXX/*
uv tool run twine upload dist/release.XXXXXXXX/*
```

上传前确认目录对应本次发布。已上传的发行文件不能覆盖；修复后需要新版本。
首次上传是否能注册名称，以 PyPI 实际校验为准。

参考：[Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
与 [PyPI 帮助](https://pypi.org/help/)。
