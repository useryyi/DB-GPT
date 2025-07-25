#!/bin/bash

# ----------------------------
# DB-GPT Webserver 管理脚本 (优化版)，新增本地代码启动命令
# ----------------------------

export UV_EXTRA_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"

# 优化 UV 执行 - 避免同步检查
export UV_NO_SYNC=1                    # 禁用自动同步
export UV_FROZEN=1                     # 使用冻结模式，不检查依赖变化
export UV_NO_PROGRESS=1                # 禁用进度条显示
export UV_CACHE_DIR="$HOME/.cache/uv"  # 缓存目录

# ----------------------------
# 配置
APP_NAME="dbgpt-webserver"
CONFIG_FILE="configs/dbgpt-proxy-xinference.toml"
PID_FILE="/tmp/${APP_NAME}.pid"
LOG_DIR="logs"
LOG_FILE="${LOG_DIR}/log_file_${APP_NAME}.log"

# 脚本与项目根目录（假设脚本放在项目根或子目录，根据实际情况调整）
SCRIPT_DIR=$(cd "$(dirname "$0")"; pwd)
# 如果脚本位于项目根，WORKSPACE_DIR=SCRIPT_DIR；否则可自行修改
WORKSPACE_DIR="${SCRIPT_DIR}"

# 优先使用虚拟环境中的 Python，可由环境变量覆盖
if [ -n "$PYTHON_INTERPRETER" ]; then
    PYTHON_INTERPRETER="$PYTHON_INTERPRETER"
else
    # 这里假定虚拟环境在项目根下 .venv
    if [ -x "${WORKSPACE_DIR}/.venv/bin/python" ]; then
        PYTHON_INTERPRETER="${WORKSPACE_DIR}/.venv/bin/python"
    else
        PYTHON_INTERPRETER="python"
    fi
fi

# 确保日志目录存在
mkdir -p "$LOG_DIR"

# 检查进程是否在运行（基于 PID_FILE）
is_running() {
    [ -f "$PID_FILE" ] && ps -p "$(cat "$PID_FILE")" > /dev/null 2>&1
}

# ----------------------------
# 启动服务 (原有 uv run 启动方式)
start() {
    if is_running; then
        echo "$APP_NAME 已经在运行中 (PID: $(cat "$PID_FILE"))."
    else
        echo "正在启动 $APP_NAME..."
        echo "使用优化的 UV 启动 (跳过同步检查)..."
        nohup uv run --frozen dbgpt start webserver --config "$CONFIG_FILE" >> "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        sleep 2
        if is_running; then
            echo "$APP_NAME 启动成功 (PID: $(cat "$PID_FILE"))."
        else
            echo "$APP_NAME 启动失败，请检查日志: $LOG_FILE"
        fi
    fi
}

# 快速启动 (跳过更多检查)
quick_start() {
    if is_running; then
        echo "$APP_NAME 已经在运行中 (PID: $(cat "$PID_FILE"))."
    else
        echo "正在快速启动 $APP_NAME (跳过所有检查)..."
        UV_NO_SYNC=1 UV_FROZEN=1 UV_NO_PROGRESS=1 \
        nohup uv run --frozen --no-sync --quiet dbgpt start webserver --config "$CONFIG_FILE" >> "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        sleep 1
        if is_running; then
            echo "$APP_NAME 快速启动成功 (PID: $(cat "$PID_FILE"))."
        else
            echo "$APP_NAME 启动失败，请检查日志: $LOG_FILE"
        fi
    fi
}

# ----------------------------
# 本地代码启动（直接运行 Python 脚本），类似 VSCode debug 启动
# 可在项目开发或测试时使用
local_start() {
    if is_running; then
        echo "$APP_NAME 已经在运行中 (PID: $(cat "$PID_FILE"))."
    else
        echo "正在使用本地代码启动 $APP_NAME..."
        # 拼接脚本路径：请根据实际位置调整
        SERVER_SCRIPT="${WORKSPACE_DIR}/packages/dbgpt-app/src/dbgpt_app/dbgpt_server.py"
        # 如果需要调试，可以在这里插入 debugpy 监听，例如：
        # nohup "$PYTHON_INTERPRETER" -m debugpy --listen 5678 --wait-for-client "$SERVER_SCRIPT" --config "$CONFIG_FILE" >> "$LOG_FILE" 2>&1 &
        # 若不需要 remote debug，直接运行：
        nohup "$PYTHON_INTERPRETER" "$SERVER_SCRIPT" --config "$CONFIG_FILE" >> "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        sleep 2
        if is_running; then
            echo "$APP_NAME 本地代码启动成功 (PID: $(cat "$PID_FILE"))."
            echo "使用 Python: $PYTHON_INTERPRETER"
            echo "脚本路径: $SERVER_SCRIPT"
            echo "配置文件: $CONFIG_FILE"
        else
            echo "$APP_NAME 启动失败，请检查日志: $LOG_FILE"
        fi
    fi
}

# ----------------------------
# 停止服务
stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        echo "正在停止 $APP_NAME (PID: $PID)..."
        # 先尝试以进程组方式终止
        PGID=$(ps -o pgid= "$PID" | tail -n1 | tr -d ' ')
        if [ -n "$PGID" ]; then
            kill -- -"$PGID" 2>/dev/null || true
        fi
        sleep 2
        # 强制终止残留进程（示例中 lyric worker，可根据实际调整）
        pkill -f "lyric/default_python_worker.py" 2>/dev/null || true
        rm -f "$PID_FILE"
        echo "$APP_NAME 已停止."
    else
        echo "$APP_NAME 未在运行."
    fi
}

# 重启服务
restart() {
    stop
    sleep 2
    start
}

# 快速重启
quick_restart() {
    stop
    sleep 1
    quick_start
}

# 本地重启
local_restart() {
    stop
    sleep 1
    local_start
}

# 查看服务状态
status() {
    if is_running; then
        echo "$APP_NAME 正在运行 (PID: $(cat "$PID_FILE"))."
    else
        echo "$APP_NAME 未在运行."
    fi
}

# 查看日志
view_log() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "日志文件不存在: $LOG_FILE"
    fi
}

# 清理日志
clean_log() {
    if [ -f "$LOG_FILE" ]; then
        rm "$LOG_FILE"
        echo "已清除日志文件."
    else
        echo "日志文件不存在，无需清理."
    fi
}

# 显示 UV 优化信息
show_uv_info() {
    echo "当前 UV 优化配置:"
    echo "  UV_NO_SYNC: $UV_NO_SYNC"
    echo "  UV_FROZEN: $UV_FROZEN"
    echo "  UV_NO_PROGRESS: $UV_NO_PROGRESS"
    echo "  UV_CACHE_DIR: $UV_CACHE_DIR"
    echo ""
    echo "UV 版本信息:"
    uv --version 2>/dev/null || echo "UV 未安装或不在 PATH 中"
    echo ""
    echo "本地 Python 解释器: $PYTHON_INTERPRETER"
}

# ----------------------------
# 用法说明
show_usage() {
    cat <<EOF
用法: $0 {start|quick|dev|stop|restart|quick-restart|dev-restart|status|log|clean|uv-info}
命令说明:
  start            - 正常启动 (优化版 uv run)
  quick 或 fast    - 快速启动 (跳过更多检查)
  dev 或 local     - 本地代码启动，直接用 Python 运行 dbgpt_server.py
  restart          - 停止后再正常启动
  quick-restart    - 停止后再快速启动
  dev-restart      - 停止后再本地代码启动
  status           - 查看服务运行状态
  log              - tail -f 实时查看日志
  clean            - 清理日志文件
  uv-info          - 显示 UV 优化相关配置信息及本地 Python 解释器
EOF
}

# ----------------------------
# 根据参数执行相应操作
case "$1" in
    start)
        start
        ;;
    quick|fast)
        quick_start
        ;;
    dev|local)
        local_start
        ;;
    restart)
        restart
        ;;
    quick-restart|fast-restart)
        quick_restart
        ;;
    dev-restart|local-restart)
        local_restart
        ;;
    stop)
        stop
        ;;
    status)
        status
        ;;
    log)
        view_log
        ;;
    clean)
        clean_log
        ;;
    uv-info)
        show_uv_info
        ;;
    *)
        show_usage
        exit 1
        ;;
esac

exit 0

