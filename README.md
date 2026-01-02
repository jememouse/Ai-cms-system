# Deepseek-Feisu 自动化部署指南

本项目已支持 Docker 容器化部署，可独立运行于任何支持 Docker 的服务器或 VPS 上。

## 目录结构

- `Dockerfile`: 构建镜像的蓝图
- `docker-compose.yml`: 服务编排配置
- `main_scheduler.py`: 主调度程序
- `trends_data.json` & `generated_seo_data.json`: 数据持久化文件

## 快速开始

### 1. 环境准备

确保服务器已安装:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (本地开发推荐)

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入必要的 API Key:

```bash
cp .env.example .env
# 编辑 .env 文件
# DEEPSEEK_API_KEY=your_key
# FEISHU_APP_ID=your_id
# ...
```

### 3. 启动服务

#### 方式 A: 使用 uv (本地开发推荐)

`uv` 是一个极速的 Python 包管理器，自动处理虚拟环境。

```bash
# 同步依赖
uv sync

# 运行主程序
uv run main_scheduler.py
```

#### 方式 B: 使用 Docker (生产部署推荐)

```bash
docker-compose up -d --build
```

该命令将:

1. 构建 Docker 镜像
2. 后台启动容器 (`-d`)
3. 自动设置时区为 Asia/Shanghai
4. 根据配置，启动时可能会立即运行一次任务 (`RUN_ON_STARTUP=true`)

### 4. 查看状态与日志

查看容器运行状态:

```bash
docker-compose ps
```

查看实时日志:

```bash
docker-compose logs -f
```

## 数据持久化

`docker-compose.yml` 已经配置了 Volume 挂载，以下文件在容器重启后不会丢失，且可以在宿主机直接查看:

- `trends_data.json`
- `generated_seo_data.json`

## 常见问题

**Q: 容器启动后立即退出了?**
A: 请检查日志 `docker-compose logs`。常见原因是 `.env` 文件未配置或 API Key 无效导致程序报错退出。

**Q: 想手动触发一次任务?**
A: 可以进入容器手动运行:

```bash
docker exec -it deepseek-feisu-worker python main_scheduler.py
```

(注意: 这样会启动一个新的调度进程，如果只是想测试，建议修改代码或等待下一次定时触发)
