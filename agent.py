# agent.py
import fnmatch
import glob
import os
import re
import sys
import warnings

from prompt_forest import prompt_templates


def replace_top_folder(path, old_folder="src", new_folder="/var/www"):
    """Replace the top-level folder in a path."""
    is_absolute = os.path.isabs(path)
    parts = path.strip(os.sep).split(os.sep)
    if parts and parts[0] == old_folder:
        parts[0] = new_folder
    adjusted_path = os.sep.join(parts)
    if is_absolute:
        adjusted_path = os.sep + adjusted_path.lstrip(os.sep)
    return adjusted_path


def select_prompt(prompts):
    """プロンプトを選択する関数"""
    print("\n利用可能なプロンプト:")
    for num, (_, desc) in prompts.items():
        print(f"{num}: {desc}")
    while True:
        prompt_num = input("\nプロンプト番号を選択してください (1-5): ")
        if prompt_num in prompts:
            prompt_name = prompts[prompt_num][0]
            break
        print("無効な番号です。1-5の番号を入力してください。")
    return prompt_name


def get_required_variables(prompt_template):
    """プロンプトから必要な変数を抽出する関数"""
    pattern = r"\{(.*?)\}"
    variables = re.findall(pattern, prompt_template)
    allowed_vars = {
        "code",
        "error",
        "input",
        "directory_structure",
        "not_found_files_prompt",
        "not_found_files",
        "conditional_file_path_request_prompt",
        "file_path_request_prompt",
    }
    disallowed_vars = set(variables) - allowed_vars
    if disallowed_vars:
        ex_values = " ".join(str(elem) for elem in disallowed_vars)
        print(f"指定できない変数{ex_values}がプロンプト内に入っています。")
        raise ValueError(f"Invalid variables found: {ex_values}")
    return variables


def _decode_with_warning(byte_data: bytes) -> str:
    """
    bytes を UTF-8 でデコードする。strict デコードが失敗した場合は ignore で再デコードし、
    ユーザーに characters が削除された旨を警告する。
    """
    try:
        return byte_data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        warnings.warn("Some characters were removed due to decode errors.", UserWarning)
        return byte_data.decode("utf-8", errors="ignore")


def sanitize_string(s):
    """
    文字列(またはバイト列)からデコードエラーを引き起こす部分を削除し、
    その際は警告を表示する関数。
    """
    if isinstance(s, bytes):
        return _decode_with_warning(s)
    try:
        s.encode("utf-8", errors="strict")
        return s
    except UnicodeEncodeError:
        warnings.warn(
            "Some characters in string were removed due to encode errors.", UserWarning
        )
        return s.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")


def sanitize_input(prompt=""):
    """
    ユーザーへの入力プロンプトを表示し、1行入力を受け取り、
    デコードエラー部分を削除（警告付き）して返す関数。
    """
    print(prompt, end="", flush=True)
    line = sys.stdin.buffer.readline()
    if not line:
        return ""
    return _decode_with_warning(line).rstrip("\n")


def read_lines():
    """
    複数行入力を受け取り、デコードエラー部分を削除（警告付き）して返す関数。
    Ctrl+C(KeyboardInterrupt) で抜ける。
    """
    lines = []
    try:
        for line in sys.stdin.buffer:
            if not line:
                break
            line_decoded = _decode_with_warning(line).rstrip("\n")
            lines.append(line_decoded)
    except KeyboardInterrupt:
        pass
    return lines


def get_input_for_variable(
    var_name, folder_mapping, include_ignore=False, prompt_name=None
):
    """各変数に対してユーザ入力を取得する関数"""
    if var_name == "code":
        # ヒントメッセージを表示
        print(
            "【ヒント】\n"
            "ファイル名は空白または改行で区切って入力できます。空行で入力終了です。\n"
            "注：ファイル名に @ を付けると「与えられたコードのみで考えさせる（ファイルパスを受け付けない）」、\n"
            "! を付けると「必ずファイルパスを提供するようにする」オプションになります。\n"
        )
        # ユーザーからの入力受付
        file_specs = []
        while True:
            line = sanitize_input().strip()
            if not line:  # 空行で終了
                break
            file_specs.extend(line.split())
        # コードを読み込む
        file_path_option = "1"  # デフォルト
        if file_specs:
            # @と!の検出
            contains_at = any("@" in spec for spec in file_specs)
            contains_bang = any("!" in spec for spec in file_specs)
            if contains_at and contains_bang:
                print("エラー：ファイル名に@と!の両方を含めることはできません。")
                sys.exit(1)
            elif contains_at:
                file_path_option = "3"
                # '@'を削除
                file_specs = [
                    spec.replace("@", "") for spec in file_specs if "@" != spec
                ]
            elif contains_bang:
                file_path_option = "2"
                # '!'を削除
                file_specs = [
                    spec.replace("!", "") for spec in file_specs if "!" != spec
                ]
            else:
                file_path_option = "1"
            # コードを読み込む
            code_content = read_code_as_markdown(
                file_list=file_specs,
                folder_mapping=folder_mapping,
            )
            return code_content, file_path_option
        else:
            # ファイル指定がない場合
            file_path_option = "1"
            return "", file_path_option
    elif var_name in ["input", "error"]:
        print(f"{var_name}を入力してください。Ctrl+Cで入力終了:")
        lines = read_lines()
        return "\n".join(lines) + "\n"
    elif var_name == "directory_structure":
        include_dir = (
            sanitize_input(
                "ディレクトリ構造を追加しますか？ y(default)/n/specific path: "
            )
            or "y"
        )
        if include_dir.lower() == "y":
            dir_path = folder_mapping[0]
            return list_directory_structure(
                dir_path, folder_mapping=folder_mapping, include_ignore=include_ignore
            )
        elif include_dir and include_dir.lower() != "n":
            return list_directory_structure(
                include_dir,
                folder_mapping=folder_mapping,
                include_ignore=include_ignore,
            )
        else:
            return ""
    else:
        return ""


def generate_prompt(prompt_template, input_values):
    """プロンプトテンプレートにユーザ入力を埋め込む関数"""
    formatted_prompt = prompt_template
    if "code" in input_values and not input_values["code"]:
        formatted_prompt = formatted_prompt.replace("\n# 該当コード\n{code}", "")

    for key, value in input_values.items():
        # 値が空文字列でも置換を行う
        formatted_prompt = formatted_prompt.replace(f"{{{key}}}", value)
    return formatted_prompt


def create_input_prompt(folder_mapping=("src", "/var/www"), include_ignore=False):
    """プロンプトファイルから入力を生成する関数"""
    prompts = {
        "1": ("review_prompt", "コードレビュー"),
        "2": ("revise_prompt", "コード修正・作成"),
        "3": ("error_prompt", "エラー解析"),
        "4": ("ask_prompt", "コードについての質問"),
        "5": ("code_prompt", "コードのみの提示"),
    }
    prompt_name = select_prompt(prompts)
    prompt_template = prompt_templates[prompt_name]
    # file_path_optionの初期化
    file_path_option = "1"
    input_values = {}
    # 必要な変数を取得
    required_vars = get_required_variables(prompt_template)
    for var in required_vars:
        if var in ["conditional_file_path_request_prompt", "file_path_request_prompt"]:
            continue  # 後で設定
        if var == "code":
            input_values[var], file_path_option = get_input_for_variable(
                var, folder_mapping, include_ignore, prompt_name
            )
        else:
            input_values[var] = get_input_for_variable(
                var, folder_mapping, include_ignore, prompt_name
            )
        input_values[var] = sanitize_string(input_values[var])
    # file_path_optionに応じてプロンプトを設定
    if file_path_option == "1":
        conditional_file_path_request_prompt_text = prompt_templates[
            "conditional_file_path_request_prompt"
        ]
        file_path_request_prompt_text = ""
    elif file_path_option == "2":
        conditional_file_path_request_prompt_text = prompt_templates[
            "conditional_file_path_request_prompt"
        ]
        file_path_request_prompt_text = prompt_templates["file_path_request_prompt"]
    else:  # "3"
        conditional_file_path_request_prompt_text = ""
        file_path_request_prompt_text = ""
    input_values["conditional_file_path_request_prompt"] = (
        conditional_file_path_request_prompt_text
    )
    input_values["file_path_request_prompt"] = file_path_request_prompt_text
    formatted_prompt = generate_prompt(prompt_template, input_values)
    return formatted_prompt


def is_ignored(path, ignore_patterns, new_folder):
    """
    パスが ignore_patterns のいずれかに一致するかをチェックする関数。
    """
    relative_path = os.path.relpath(path, new_folder)
    for pattern in ignore_patterns:
        if pattern.endswith("/"):
            base_pattern = os.path.basename(os.path.normpath(pattern))
            base_path = os.path.basename(os.path.normpath(relative_path))
            if fnmatch.fnmatch(base_path, base_pattern):
                return True
        elif "*" in pattern or "?" in pattern:
            if fnmatch.fnmatch(relative_path, pattern):
                return True
        else:
            if relative_path == pattern:
                return True
    return False


def get_directory_structure(new_folder, ignore_patterns):
    """ディレクトリ構造を取得する関数"""
    dir_structure = []
    for dirpath, dirnames, filenames in os.walk(new_folder):
        if is_ignored(dirpath, ignore_patterns, new_folder):
            continue
        dirnames[:] = [
            d
            for d in dirnames
            if not is_ignored(os.path.join(dirpath, d), ignore_patterns, new_folder)
        ]
        filenames[:] = [
            f
            for f in filenames
            if not is_ignored(os.path.join(dirpath, f), ignore_patterns, new_folder)
        ]
        depth = dirpath[len(new_folder) :].count(os.sep)
        dir_info = {
            "depth": depth,
            "dirname": os.path.basename(dirpath),
            "files": filenames,
        }
        dir_structure.append(dir_info)
    return dir_structure


def format_directory_structure(dir_structure, new_folder):
    """ディレクトリ構造を文字列に整形する関数"""
    output = ""
    for i, dir_info in enumerate(dir_structure):
        indent = " " * 4 * dir_info["depth"]
        if i == 0:  # 最初のディレクトリの場合
            output += "{}/\n".format(new_folder.rstrip(os.sep))  # フルパスを表示
        else:
            output += "{}{}/\n".format(indent, dir_info["dirname"])
        for filename in dir_info["files"]:
            sub_indent = " " * 4 * (dir_info["depth"] + 1)
            output += "{}{}\n".format(sub_indent, filename)
    return "# ディレクトリ構造\n" + output


def list_directory_structure(
    work_directory: str, folder_mapping=("src", "/var/www"), include_ignore=False
) -> str:
    """ディレクトリ構造をツリー形式で出力（.ignoreに準拠)"""
    old_folder, new_folder = folder_mapping
    new_folder = replace_top_folder(work_directory, old_folder, new_folder)
    if not os.path.exists(new_folder):
        raise FileNotFoundError(
            f"'{new_folder}' does not exist. You should input full path."
        )
    try:
        ignore_patterns = []
        if not include_ignore:
            if os.path.exists(".gitignore"):
                with open(".gitignore", "r") as f:
                    ignore_patterns += [
                        line.strip()
                        for line in f.readlines()
                        if line.strip() and not line.startswith("#")
                    ]
            if os.path.exists(".dirignore"):
                with open(".dirignore", "r") as f:
                    ignore_patterns += [
                        line.strip()
                        for line in f.readlines()
                        if line.strip() and not line.startswith("#")
                    ]
        ignore_patterns = [".git/", "agent_simple/"] + ignore_patterns
        dir_structure = get_directory_structure(new_folder, ignore_patterns)
        output = format_directory_structure(dir_structure, new_folder)
        return output
    except Exception as e:
        return f"An error occurred: {e}"


def get_files_from_spec(file_spec):
    """ファイルスペックからファイルリストを取得する関数"""
    if os.path.isdir(file_spec):
        files = [
            os.path.join(file_spec, f)
            for f in os.listdir(file_spec)
            if os.path.isfile(os.path.join(file_spec, f))
        ]
    elif os.path.isfile(file_spec):
        files = [file_spec]
    else:
        exact_match = glob.glob(file_spec)
        if exact_match:
            files = exact_match
        else:
            if '*' in file_spec or '?' in file_spec:
                files = glob.glob(file_spec)
            else:
                files = []
    return files


def read_code_as_markdown(file_list: list, folder_mapping=("src", "/var/www")):
    """コードをMarkdown形式で読み込む関数"""
    old_folder, new_folder = folder_mapping
    markdown_content = ""
    not_found_files = []
    if file_list:
        for file_spec in file_list:
            adjusted_file_spec = replace_top_folder(file_spec, old_folder, new_folder)
            files = get_files_from_spec(adjusted_file_spec)
            if not files:
                print(f"警告: '{file_spec}'に該当するファイルが見つかりませんでした。")
                not_found_files.append(adjusted_file_spec)
                continue
            for f in files:
                code = read_file(f)
                if code is None:
                    not_found_files.append(f)
                    continue
                markdown_content = add_markdown_block(
                    markdown_content,
                    title=f"File {os.path.basename(f)}",
                    code=code,
                )
        return markdown_content
    else:
        return ""


def read_file(file_path):
    """ファイルを読み込む関数"""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            return file.read()
    except FileNotFoundError as e:
        print(f"ファイル'{file_path}'の読み込み中にエラーが発生しました: {e}")
        return None


def add_markdown_block(markdown_content, title, code):
    """Markdownブロックを追加する関数"""
    markdown_content += f"\n## {title}\n"
    markdown_content += "```\n"
    markdown_content += code + "\n"
    markdown_content += "```"
    return markdown_content


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create input prompt")
    parser.add_argument(
        "--old_folder", type=str, default="src", help="Old folder name to be replaced"
    )
    parser.add_argument(
        "--new_folder",
        type=str,
        default=os.path.dirname(os.path.dirname(__file__)),
        help="New folder name to replace with",
    )
    parser.add_argument(
        "--include_ignore",
        action="store_true",
        help="Whether to use .gitignore and .dirignore",
    )
    args = parser.parse_args()
    result = create_input_prompt(
        folder_mapping=(args.old_folder, args.new_folder),
        include_ignore=args.include_ignore,
    )
    with open(
        os.path.join(args.new_folder, "agent_simple/.aa_prompt.md"),
        "w",
        encoding="utf-8",
        errors="ignore",
    ) as f:
        f.write(result)
    print(
        "\nプロンプトが {}/agent_simple/.aa_prompt.md に保存されました。".format(
            args.new_folder
        )
    )

# --------------------------------------------------------------------------------------------------
# 使い方（Usage）
# 【概要】
# このスクリプトは対話形式で「コードレビュー・エラー解析・質問」などのプロンプトテンプレートを選び、
# 必要な変数（コードやエラー文など）を埋め込んだテキストファイル（.md）を出力するためのものです。

# 【手順】
# 1. コマンドラインから本スクリプトを実行します。
#    例）python agent.py --old_folder src --new_folder /var/www
#      - --old_folder で変換前のトップフォルダ名を指定（デフォルトは"src"）。
#      - --new_folder で変換後のトップフォルダ名を**絶対パス**で指定（デフォルトは本スクリプトの１つ上のディレクトリ）。
#      - --include_ignore フラグを付けると.gitignoreや.dirignoreのパターンに従い、表示／取得から除外されます。

# 2. プロンプトの番号を入力（1〜5）して、利用したいテンプレートを選択します。
#    - 1: コードレビュー
#    - 2: コード修正・作成
#    - 3: エラー解析
#    - 4: コードについての質問
#    - 5: コードのみの提示

# 3. 選んだテンプレートに応じて必要な変数（{code}, {error}, {input}, {directory_structure}など）を対話形式で入力します。
#    - {code} 入力の際は、読み込みたいファイルやフォルダを**相対パス**で指定してください。
#      ファイル名は空白または改行で区切って入力し、空行で入力終了です。
#      注：ファイル名に **`@`** を付けると「与えられたコードのみで考えさせる（ファイルパスを受け付けない）」、
#          **`!`** を付けると「必ずファイルパスを提供するようにする」オプションになります。
#    - {error} や {input} では複数行を入力したい場合は、**Ctrl+C（または Ctrl+D）**で入力終了します。
#    - {directory_structure} ではディレクトリ構造を出力するかどうか、もしくは特定パスを指定するか選択します。

# 4. 入力が完了すると、最終的に生成されたプロンプト文字列が"`{new_folder}/agent_simple/.aa_prompt.md`"に書き込まれます。
#    例）"--new_folder /var/www" の場合、"`/var/www/agent_simple/.aa_prompt.md`" に出力されます。

# 5. もし「ファイルが見つからない」旨が表示された場合、指定パスやファイル名が正しいかご確認ください。
#    特に複数ファイルを指定する際はスペースまたは改行で区切って入力し、相対パス指定が正しいか注意してください。

# 【コマンド実行例】
#  python agent.py --old_folder src --new_folder /var/www --include_ignore

# 上記の例では、 src → /var/www ディレクトリに置換し、
# .gitignore と .dirignore に基づく無視リストを考慮してディレクトリ構造を確認します。

# 【出力】
#  ・対話形式で入力・処理した結果が、"`--new_folder`" で指定した場所の "`agent_simple/.aa_prompt.md`" に保存されます。
#    例）"--new_folder /var/www" の場合、"`/var/www/agent_simple/.aa_prompt.md`" に出力されます。
# --------------------------------------------------------------------------------------------------
