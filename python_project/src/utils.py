import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
import time


def seed_torch(seed: int = 42) -> None:
    """
    Set the random seed for reproducibility.

    Args:
        seed (int): The seed value to set. Default is 42.
    """
    import os
    import random

    import numpy as np
    import torch

    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def setup_logging(
    log_level: int = logging.INFO,
    log_dir: str = "logs",
    log_filename: str = "log.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    file_format: str = "%(levelname)s - [%(asctime)s][%(name)s:%(lineno)s] - %(message)s",
    console_format: str = "%(levelname)s - [%(name)s:%(lineno)s] - %(message)s",
) -> None:
    """
    ログ設定を初期化し、ファイルへの出力とローテーションを設定する。

    Args:
        log_level: ログレベル（デフォルト: logging.INFO）
        log_dir: ログディレクトリ（デフォルト: "logs"）
        log_filename: ログファイル名（デフォルト: "log.log"）
        max_bytes: ローテーションサイズ（デフォルト: 10MB）
        backup_count: 保持するバックアップファイル数（デフォルト: 5）
        file_format: ファイル用ログフォーマット文字列
        console_format: コンソール用ログフォーマット文字列

    Notes:
        - ログディレクトリが存在しない場合は自動的に作成される
        - ローテーションされたファイルは log.log.YYYY-MM-DD-HH-MM 形式で保存される
    """
    # プロジェクトルートからの相対パスを解決
    project_root = Path(__file__).parent.parent
    log_path = project_root / log_dir

    # ログディレクトリの作成
    log_path.mkdir(parents=True, exist_ok=True)

    # ログファイルのフルパス
    log_file = log_path / log_filename

    # ルートロガーの設定をクリア（既存の設定との競合を避ける）
    logger = logging.getLogger()
    logger.handlers.clear()

    # カスタムローテーションハンドラー
    class CustomRotatingFileHandler(logging.handlers.RotatingFileHandler):
        """カスタムローテーティングファイルハンドラー"""

        def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding='utf-8', delay=False):
            """コンストラクタでencodingを設定"""
            super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)

        def _open(self):
            """ファイルを開く際にencodingを確実に指定"""
            return open(self.baseFilename, self.mode, encoding=self.encoding)

        def doRollover(self) -> None:
            """
            ログファイルのローテーション処理を行う。

            ファイル名に日付を付与し、古いバックアップファイルを削除する。
            """
            if self.stream:
                self.stream.close()
                self.stream = None

            # 新しいファイル名を生成（秒まで含める）
            current_time = time.strftime("%Y-%m-%d-%H-%M-%S")
            base_filename = Path(self.baseFilename)
            dfn = base_filename.parent / f"{base_filename.name}.{current_time}"
            
            # 同じ秒に複数のローテーションが発生した場合の対策
            counter = 0
            original_dfn = dfn
            while dfn.exists():
                counter += 1
                dfn = Path(f"{original_dfn}_{counter}")

            # ファイルをリネーム
            if Path(self.baseFilename).exists():
                os.rename(self.baseFilename, dfn)

            # 古いバックアップファイルを削除
            self._delete_old_backups()

            # 新しいストリームを開く
            if not self.delay:
                self.stream = self._open()

        def _delete_old_backups(self):
            """古いバックアップファイルを削除"""
            base_dir = os.path.dirname(self.baseFilename)
            base_name = os.path.basename(self.baseFilename)

            # バックアップファイルのリストを取得
            backup_files = []
            for filename in os.listdir(base_dir):
                if filename.startswith(f"{base_name}.") and filename != base_name:
                    file_path = os.path.join(base_dir, filename)
                    backup_files.append((file_path, os.path.getmtime(file_path)))

            # 更新時刻でソート（古い順）
            backup_files.sort(key=lambda x: x[1])

            # 保持数を超えたファイルを削除
            while len(backup_files) > self.backupCount:
                os.remove(backup_files[0][0])
                backup_files.pop(0)

    # ファイルハンドラーの設定
    file_handler = CustomRotatingFileHandler(
        str(log_file), maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
    )
    file_handler.setLevel(log_level)

    # ファイル用フォーマッターの設定
    file_formatter = logging.Formatter(file_format)
    file_handler.setFormatter(file_formatter)

    # コンソールハンドラーの設定
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    # コンソール用フォーマッターの設定
    console_formatter = logging.Formatter(console_format)
    console_handler.setFormatter(console_formatter)

    # ルートロガーに設定
    logger.setLevel(log_level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # 設定完了のログ
    logger.info(f"ログ設定が完了しました。ログファイル: {log_file}")


def setup_debug_logging(logger_name: str = "debug") -> logging.Logger:
    """
    デバッグ専用のログ設定を行う。

    この関数は既存のログ設定に影響を与えず、独立したデバッグログを作成します。
    実行時に過去のdebug.logをすべて削除し、単一のログファイルとして管理します。
    これにより、参照する情報を削減し、デバッグ作業を効率化します。

    Args:
        logger_name: デバッグロガーの名前（デフォルト: "debug"）

    Returns:
        logging.Logger: 設定済みのデバッグロガー
    """
    # プロジェクトルートからの相対パスを解決
    project_root = Path(__file__).parent.parent
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)

    # debug.logファイルのパス
    debug_log_file = log_dir / "debug.log"

    # 既存のdebug.logを削除（単一ログファイルとして管理）
    if debug_log_file.exists():
        debug_log_file.unlink()

    # 独立したロガーを作成（ルートロガーとは別）
    debug_logger = logging.getLogger(logger_name)
    debug_logger.setLevel(logging.DEBUG)
    debug_logger.handlers.clear()  # 既存のハンドラーをクリア

    # ファイルハンドラーの設定
    file_handler = logging.FileHandler(debug_log_file, mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)

    # コンソールハンドラーの設定
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # フォーマッターの設定
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # ハンドラーをロガーに追加
    debug_logger.addHandler(file_handler)
    debug_logger.addHandler(console_handler)

    # propagateをFalseにして、ルートロガーへの伝播を防ぐ
    debug_logger.propagate = False

    debug_logger.info(f"デバッグログ設定が完了しました。ログファイル: {debug_log_file}")

    return debug_logger
