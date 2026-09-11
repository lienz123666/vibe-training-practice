#!/usr/bin/env bash
set -euo pipefail

echo "==> 拉取最新代码"
git pull

echo "==> 构建镜像"
docker compose build

echo "==> 启动服务"
docker compose up -d

echo "==> 当前状态"
docker compose ps