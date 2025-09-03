#!/bin/bash

export UV_EXTRA_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"

# 优化 UV 执行 - 避免同步检查
export UV_NO_SYNC=1                    # 禁用自动同步
export UV_FROZEN=1                     # 使用冻结模式，不检查依赖变化
export UV_NO_PROGRESS=1                # 禁用进度条显示
export UV_CACHE_DIR="$HOME/.cache/uv"  # 确保缓存目录

# DB-GPT Webserver 管理脚本 (优化版)
# 配置
APP_NAME="dbgpt-webserver"
CONFIG_FILE="configs/dbgpt-proxy-xinference160-2.toml"
PID_FILE="/tmp/${APP_NAME}.pid"
LOG_DIR="logs"
LOG_FILE="${LOG_DIR}/log_file_${APP_NAME}.log"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

# 检查进程是否在运行
is_running() {
    [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1
}

# 启动服务
start() {
    if is_running; then
        echo "$APP_NAME 已经在运行中 (PID: $(cat "$PID_FILE"))."
    else
        echo "正在启动 $APP_NAME..."
        
        # 方法1: 使用环境变量优化 UV
        echo "使用优化的 UV 启动 (跳过同步检查)..."
        nohup uv run --frozen dbgpt start webserver --config "$CONFIG_FILE" >> "$LOG_FILE" 2>&1 &
        
        # 方法2: 如果上面不行，可以尝试这个
        # nohup uv run --no-sync dbgpt start webserver --config "$CONFIG_FILE" >> "$LOG_FILE" 2>&1 &
        
        # 方法3: 或者使用这个组合
        # nohup uv run --frozen --no-progress dbgpt start webserver --config "$CONFIG_FILE" >> "$LOG_FILE" 2>&1 &
        
        echo $! > "$PID_FILE"
        sleep 2
        if is_running; then
            echo "$APP_NAME 启动成功 (PID: $(cat "$PID_FILE"))."
        else
            echo "$APP_NAME 启动失败，请检查日志: $LOG_FILE"
        fi
    fi
}

# 快速启动 (最小化检查)
quick_start() {
    if is_running; then
        echo "$APP_NAME 已经在运行中 (PID: $(cat "$PID_FILE"))."
    else
        echo "正在快速启动 $APP_NAME (跳过所有检查)..."
        
        # 使用最激进的优化参数
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

# 停止服务
stop() {
    if [ -f "$PID_FILE" ]; then
        echo "正在停止 $APP_NAME (PID: $(cat "$PID_FILE"))..."
        # 终止整个进程组
        PGID=$(ps -o pgid= $(cat "$PID_FILE") | grep -o '[0-9]*')
        kill -- -$PGID 2>/dev/null || true
        sleep 2
        # 强制终止残留进程
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
}

# 根据参数执行相应的操作
case "$1" in
    start)
        start
        ;;
    quick|fast)
        quick_start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    quick-restart|fast-restart)
        quick_restart
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
        echo "用法: $0 {start|quick|stop|restart|quick-restart|status|log|clean|uv-info}"
        echo ""
        echo "命令说明:"
        echo "  start          - 正常启动 (优化版)"
        echo "  quick/fast     - 快速启动 (跳过所有检查)"
        echo "  quick-restart  - 快速重启"
        echo "  uv-info        - 显示 UV 优化配置信息"
        exit 1
        ;;
esac

exit 0
