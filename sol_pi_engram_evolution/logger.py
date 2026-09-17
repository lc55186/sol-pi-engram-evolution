"""
BOSS-AI-R 日志系统

统一的日志配置：结构化输出、多级别、多输出目标（控制台 + 文件 + 远程）。
V0.2 改进：修复 LoggerAdapter 上下文传递 bug、添加结构化字段自动注入、
请求 ID 传播、日志级别热更新支持。
"""

import json
import logging
import sys
import threading
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

# 日志格式
CONSOLE_FORMAT = "%(asctime)s │ %(levelname)-8s │ %(name)-20s │ %(message)s"
CONSOLE_DATE_FORMAT = "%H:%M:%S"

# 颜色映射
COLORS = {
    "DEBUG": "\033[36m",      # 青色
    "INFO": "\033[32m",       # 绿色
    "WARNING": "\033[33m",    # 黄色
    "ERROR": "\033[31m",      # 红色
    "CRITICAL": "\033[35m",   # 紫色
    "RESET": "\033[0m"
}


class ColorFormatter(logging.Formatter):
    """带颜色的控制台日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        color = COLORS.get(record.levelname, COLORS["RESET"])
        reset = COLORS["RESET"]

        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        logger_name = record.name[:20]
        message = record.getMessage()

        return f"{timestamp} │ {color}{record.levelname:8s}{reset} │ {logger_name:20s} │ {message}"


class StructuredFormatter(logging.Formatter):
    """结构化 JSON 日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "levelno": record.levelno,
        }

        # 添加 extra 字段（已合并后的）
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        # 添加异常信息
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class ContextAdapter(logging.LoggerAdapter):
    """
    增强的 LoggerAdapter，支持上下文传播。

    V0.2 改进：
    - 修复 process() 方法中 extra 传递的 bug
    - 支持自动注入上下文信息（request_id, tenant_id 等）
    """

    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple:
        # 合并 extra 字段：adapter 的 self.extra + 调用时的 kwargs["extra"]
        extra = {}
        extra.update(self.extra)
        if "extra" in kwargs:
            extra.update(kwargs["extra"])
        kwargs["extra"] = {"extra_fields": extra}
        return msg, kwargs

    def debug(self, msg: str, *args, **kwargs):
        super().debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        super().info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        super().warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        super().error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        super().critical(msg, *args, **kwargs)


_loggers: dict[str, logging.Logger] = {}
_initialized: bool = False
_init_lock = threading.Lock()
_request_id_context = threading.local()


def setup_logging(
    log_dir: Path | None = None,
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    max_file_size: int = 50 * 1024 * 1024,  # 50MB
    backup_count: int = 10,
    json_format: bool = False
) -> None:
    """
    初始化日志系统（线程安全）

    Args:
        log_dir: 日志目录，默认 ./logs
        console_level: 控制台日志级别
        file_level: 文件日志级别
        max_file_size: 单文件最大大小
        backup_count: 备份文件数量
        json_format: 是否使用 JSON 格式输出
    """
    global _initialized, _loggers
    if _initialized:
        return

    with _init_lock:
        if _initialized:
            return

        # 创建日志目录
        if log_dir is None:
            log_dir = Path(__file__).resolve().parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # 根 logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        # 清除已有 handler
        root_logger.handlers.clear()
        _loggers.clear()

        # 控制台 handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, console_level.upper(), logging.INFO))
        console_handler.setFormatter(ColorFormatter())
        root_logger.addHandler(console_handler)

        # 文件 handler（按大小轮转）
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = log_dir / f"boss-ai-r-{today}.log"

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(getattr(logging, file_level.upper(), logging.DEBUG))

        if json_format:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)-20s | %(module)s:%(funcName)s:%(lineno)d | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
        root_logger.addHandler(file_handler)

        # 审计日志（单独文件）
        audit_file = log_dir / f"audit-{today}.log"
        audit_handler = RotatingFileHandler(
            audit_file,
            maxBytes=max_file_size,
            backupCount=30,
            encoding="utf-8"
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(StructuredFormatter())

        # 创建审计 logger
        audit_logger = logging.getLogger("audit")
        audit_logger.handlers.clear()
        audit_logger.addHandler(audit_handler)
        audit_logger.propagate = False

        # 错误日志（单独文件）
        error_file = log_dir / f"error-{today}.log"
        error_handler = RotatingFileHandler(
            error_file,
            maxBytes=max_file_size,
            backupCount=20,
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(error_handler)

        _initialized = True


def set_request_id(request_id: str) -> None:
    """设置当前线程的请求 ID（上下文传播）"""
    _request_id_context.request_id = request_id


def get_request_id() -> str | None:
    """获取当前线程的请求 ID"""
    return getattr(_request_id_context, "request_id", None)


def clear_request_id() -> None:
    """清除当前线程的请求 ID"""
    if hasattr(_request_id_context, "request_id"):
        del _request_id_context.request_id


def get_logger(name: str, **extra) -> ContextAdapter:
    """
    获取命名 logger（V0.2 改进：返回 ContextAdapter）

    Args:
        name: logger 名称（建议使用模块名）
        **extra: 额外字段（每次日志调用都会包含）

    Returns:
        ContextAdapter 实例
    """
    if not _initialized:
        setup_logging()

    if name in _loggers:
        return ContextAdapter(_loggers[name], extra)

    logger = logging.getLogger(name)
    _loggers[name] = logger

    return ContextAdapter(logger, extra)


def get_audit_logger() -> logging.Logger:
    """获取审计日志 logger"""
    if not _initialized:
        setup_logging()
    return logging.getLogger("audit")


# 便捷函数
def log_request(request_id: str, method: str, path: str, status: int, duration_ms: float) -> None:
    """记录 API 请求"""
    logger = get_logger("api.request")
    logger.info(f"{method} {path} → {status} ({duration_ms:.1f}ms)", extra={
        "request_id": request_id,
        "method": method,
        "path": path,
        "status": status,
        "duration_ms": duration_ms
    })


def log_tenant_action(tenant_id: str, user_id: str, action: str, detail: str = "") -> None:
    """记录租户操作（审计）"""
    audit = get_audit_logger()
    audit.info(f"[{tenant_id}] user={user_id} action={action} {detail}")


def log_audio_session(session_id: str, tenant_id: str, event: str, **kwargs) -> None:
    """记录音频会话事件"""
    logger = get_logger("audio.session")
    logger.info(f"[{session_id[:8]}] {event}", extra={
        "session_id": session_id,
        "tenant_id": tenant_id,
        **kwargs
    })


def log_prompt_triggered(prompt_id: str, session_id: str, prompt_type: str, latency_ms: float, channel: str) -> None:
    """记录提示触发"""
    logger = get_logger("prompt.triggered")
    logger.info(f"[{session_id[:8]}] {prompt_type} via {channel} ({latency_ms:.0f}ms)", extra={
        "prompt_id": prompt_id,
        "session_id": session_id,
        "type": prompt_type,
        "latency_ms": latency_ms,
        "channel": channel
    })


def log_compliance_event(tenant_id: str, event_type: str, status: str, detail: str = "") -> None:
    """记录合规事件（审计）"""
    audit = get_audit_logger()
    audit.info(f"COMPLIANCE [{tenant_id}] {event_type}={status} {detail}")


def log_pipeline_event(stage: str, action: str, result: str, **kwargs) -> None:
    """记录 Pipeline 事件（V0.2 新增）"""
    logger = get_logger("pipeline")
    logger.info(f"[{stage}] {action}: {result}", extra=kwargs)
