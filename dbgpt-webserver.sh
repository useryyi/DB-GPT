#!/bin/bash

# export UV_EXTRA_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"

# DB-GPT Webserver 管理脚本 (简化版，不使用 conda)

# 配置
APP_NAME="dbgpt-webserver"
CONFIG_FILE="configs/dbgpt-proxy-xinference.toml"
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
        nohup uv run --no-deps dbgpt start webserver --config "$CONFIG_FILE" >> "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        sleep 2
        if is_running; then
            echo "$APP_NAME 启动成功 (PID: $(cat "$PID_FILE"))."
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

# 根据参数执行相应的操作
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
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
    *)
        echo "用法: $0 {start|stop|restart|status|log|clean}"
        exit 1
        ;;
esac

exit 0
