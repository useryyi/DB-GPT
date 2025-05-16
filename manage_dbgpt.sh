#!/bin/bash

# DB-GPT 服务器管理脚本

# 配置
ACTIVATE_PATH="/home/yannic/install/anaconda3/bin/activate"
ENV_NAME="dbgpt"
APP_NAME="dbgpt-server"
PYTHON_CMD="python"
SCRIPT_PATH="dbgpt/app/dbgpt_server.py"
PID_FILE="/tmp/${APP_NAME}.pid"
LOG_DIR="logs"
LOG_FILE="${LOG_DIR}/${APP_NAME}.log"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 检查进程是否在运行
is_running() {
    [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1
}

# 启动服务
start() {
    if is_running; then
        echo "$APP_NAME 已经在运行中。"
    else
        echo "正在启动 $APP_NAME..."
		source "$ACTIVATE_PATH"
        conda activate "$ENV_NAME"
        cd "$SCRIPT_DIR"
        nohup $PYTHON_CMD $SCRIPT_PATH >> "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        sleep 2
        if is_running; then
            echo "$APP_NAME 启动成功。"
        else
            echo "$APP_NAME 启动失败，请检查日志。"
        fi
    fi
}

# 停止服务
stop() {
    if is_running; then
        echo "正在停止 $APP_NAME..."
        kill $(cat "$PID_FILE")
        rm -f "$PID_FILE"
        sleep 2
        if is_running; then
            echo "$APP_NAME 无法正常停止，正在强制终止..."
            kill -9 $(cat "$PID_FILE")
            rm -f "$PID_FILE"
        fi
        echo "$APP_NAME 已停止。"
    else
        echo "$APP_NAME 未在运行。"
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
        echo "$APP_NAME 正在运行。"
    else
        echo "$APP_NAME 未在运行。"
    fi
}

# 查看日志
view_log() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "日志文件不存在。"
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
    *)
        echo "用法: $0 {start|stop|restart|status|log}"
        exit 1
        ;;
esac

exit 0
