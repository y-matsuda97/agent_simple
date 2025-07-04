### デバッグの実施ルール
- ```scripts\debug```ファイル直下にdebugファイルを作成して、実施する。
- 必要なログや出力はすべて```logs\debug.log```に出力する。
- デバッグログの出力は```src\utils.py```の```setup_debug_logging```関数を使用する。
- デバッグコードを作成したあとは実施するコマンドを提示する。

##### 関連コード
```python
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
```
