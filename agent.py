import os
import re
import glob
import fnmatch
import sys
from prompt_forest import prompt_templates, prompts, additional_code_info


def replace_top_folder(path, old_folder="src", new_folder="/app"):
    """Replace the top-level folder in a path."""
    is_absolute = os.path.isabs(path)
    parts = path.strip(os.sep).split(os.sep)
    if parts and parts[0] == old_folder:
        parts[0] = new_folder
    adjusted_path = os.sep.join(parts)
    if is_absolute:
        adjusted_path = os.sep + adjusted_path
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
    disallowed_vars = set(variables) - {
        "code",
        "error",
        "input",
        "directory_structure",
        "not_found_files_prompt",
        "not_found_files",
    }
    if disallowed_vars:
        ex_values = " ".join(str(elem) for elem in disallowed_vars)
        print(f"指定できない変数{ex_values}がプロンプト内に入っています。")
        raise ValueError(f"Invalid variables found: {ex_values}")
    return variables


def get_input_for_variable(var_name, folder_mapping, include_ignore=False, prompt_name=None):
    """各変数に対してユーザ入力を取得する関数"""
    if var_name == "code":
        # ヒントメッセージを表示
        if prompt_name in ["revise_prompt", "error_prompt"]:
            print(
                "【ヒント】\n"
                "このプロンプトでは自動的に追加メッセージ (additional_code_info) が先頭に挿入されます。\n"
                "ファイル名は空白または改行で区切って入力できます。空行で入力終了です。\n"
            )
        else:
            print(
                "【ヒント】\n"
                "ファイル名やフォルダ名の入力に '@' を含めると、先頭に追加メッセージ (additional_code_info) が入ります。\n"
                "例えば '@ main.py utils/helper.py' のように入力すると、まず additional_code_info が挿入され、\n"
                "さらに 'main.py' と 'utils/helper.py' のコードも続けて読み込まれます。\n"
                "単にファイルを指定したい場合は '@' を入れずに 'main.py utils/helper.py' のように入力してください。\n"
                "ファイル名は空白または改行で区切って入力できます。空行で入力終了です。\n"
            )

        # ユーザーからの入力受付
        file_specs = []
        while True:
            line = input().strip()
            if not line:  # 空行で終了
                break
            file_specs.extend(line.split())

        # revise_promptとerror_promptの場合、または「@」を含むファイル指定がある場合
        if prompt_name in ["revise_prompt", "error_prompt"] or any("@" in spec for spec in file_specs):
            # additional_code_info を先頭に追加
            code_content = additional_code_info + "\n\n"

            # ファイル指定があれば、それらのコードをMarkdown形式で追加
            file_list = [spec for spec in file_specs if "@" not in spec]
            if file_list:
                code_content += read_code_as_markdown(
                    file_list=file_list,
                    folder_mapping=folder_mapping,
                )
            return code_content
        else:
            # 通常のファイル読み込み
            return read_code_as_markdown(
                file_list=file_specs,
                folder_mapping=folder_mapping
            )

    elif var_name in ["input", "error"]:
        print(f"{var_name}を入力してください。Ctrl+Dで入力終了:")
        lines = []
        try:
            for line in sys.stdin:
                lines.append(line.rstrip())
        except KeyboardInterrupt:
            pass
        return "\n".join(lines)
    elif var_name == "directory_structure":
        include_dir = (
            input("ディレクトリ構造を追加しますか？ y(default)/n/specific path: ")
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


def get_multiline_input(prompt_text):
    """複数行のユーザ入力を取得する関数"""
    print(prompt_text)
    lines = []
    try:
        for line in sys.stdin:
            lines.append(line.rstrip())
    except KeyboardInterrupt:
        pass
    return "\n".join(lines)


def generate_prompt(prompt_template, input_values):
    """プロンプトテンプレートにユーザ入力を埋め込む関数"""
    formatted_prompt = prompt_template
    for key, value in input_values.items():
        if value:
            formatted_prompt = formatted_prompt.replace(f"{{{key}}}", value)
        else:
            formatted_prompt = re.sub(
                r"^.*\{" + key + r"\}.*\n?", "", formatted_prompt, flags=re.MULTILINE
            )
    return formatted_prompt


def create_input_prompt(folder_mapping=("src", "/app"), include_ignore=False):
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

    required_vars = get_required_variables(prompt_template)

    input_values = {}
    for var in required_vars:
        input_values[var] = get_input_for_variable(var, folder_mapping, include_ignore, prompt_name)

    formatted_prompt = generate_prompt(prompt_template, input_values)
    return formatted_prompt


def is_ignored(path, ignore_patterns, new_folder):
    """
    パスが ignore_patterns のいずれかに一致するかをチェックする関数。
    """
    relative_path = os.path.relpath(path, new_folder)

    for pattern in ignore_patterns:
        if pattern.endswith("/"):
            dir_path = os.path.join(new_folder, pattern.strip("/"))
            if os.path.commonpath([path, dir_path]) == dir_path:
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


def format_directory_structure(dir_structure):
    """ディレクトリ構造を文字列に整形する関数"""
    output = ""
    for dir_info in dir_structure:
        indent = " " * 4 * dir_info["depth"]
        output += "{}{}/\n".format(indent, dir_info["dirname"])
        for filename in dir_info["files"]:
            sub_indent = " " * 4 * (dir_info["depth"] + 1)
            output += "{}{}\n".format(sub_indent, filename)
    return output


def list_directory_structure(
    work_directory: str, folder_mapping=("src", "/app"), include_ignore=False
) -> str:
    """ディレクトリ構造をツリー形式で出力（.ignoreに準拠)"""
    old_folder, new_folder = folder_mapping
    new_folder = replace_top_folder(work_directory, old_folder, new_folder)

    if not os.path.exists(new_folder):
        return (
            f"The directory '{new_folder}' does not exist. You should input full path."
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

        dir_structure = get_directory_structure(new_folder, ignore_patterns)
        output = format_directory_structure(dir_structure)
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
        files = glob.glob(f"{file_spec}*")
    return files


def read_code_as_markdown(file_list: list, folder_mapping=("src", "/app")):
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

    if not_found_files:
        not_found_files_str = "\n".join(not_found_files)
        markdown_content = (
            prompt_templates["not_found_files_prompt"].replace(
                "{not_found_files}", not_found_files_str
            )
            + markdown_content
        )
    return markdown_content


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
    markdown_content += f"## {title}\n"
    markdown_content += "```\n"
    markdown_content += code + "\n"
    markdown_content += "```\n\n"
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
    try:
        result = create_input_prompt(
            folder_mapping=(args.old_folder, args.new_folder),
            include_ignore=args.include_ignore,
        )
        with open(
            os.path.join(args.new_folder, "agent_simple/.aa_prompt.txt"),
            "w",
            encoding="utf-8",
            errors="ignore",
        ) as f:
            f.write(result)
        print("\nプロンプトが.aa_prompt.txtに保存されました。")
    except Exception as e:
        print(f"Error: {e}")

# --------------------------------------------------------------------------------------------------
# 使い方（Usage）
#
# 【概要】
# このスクリプトは対話形式で「コードレビュー・エラー解析・質問」などのプロンプトテンプレートを選び、
# 必要な変数（コードやエラー文など）を埋め込んだテキストファイル（.aa_prompt.txt）を出力するためのものです。
#
# 【手順】
# 1. コマンドラインから本スクリプトを実行します。
#    例）python main.py --old_folder src --new_folder ../app
#      - --old_folder で変換前のトップフォルダ名を指定（デフォルトは"src"）。
#      - --new_folder で変換後のトップフォルダ名を相対パスで指定（デフォルトは本スクリプトの１つ上のディレクトリ）。
#      - --include_ignore フラグを付けると.gitignoreや.dirignoreのパターンに従い、表示／取得から除外されます。
#
# 2. プロンプトの番号を入力（1〜5）して、利用したいテンプレートを選択します。
#    - 1: コードレビュー
#    - 2: コード修正
#    - 3: エラー解析
#    - 4: コードへの質問
#    - 5: コードのみの提示
#
# 3. 選んだテンプレートに応じて必要な変数（{code}, {error}, {input}, {directory_structure}など）を対話形式で入力します。
#    - {code} 入力の際は、読み込みたいファイルやフォルダを相対パスで指定してください。
#      （例：main.py や utils/helper.py など）
#      コード修正（2）とエラー解析（3）では自動的に additional_code_info が先頭に挿入されます。
#      その他のプロンプトでは「@」を含めて入力することで additional_code_info が先頭に入ります。
#      例）"@ main.py utils/helper.py" → additional_code_info のあと、main.py と utils/helper.py のコードを続けて出力。
#      ファイル名は空白または改行で区切って入力でき、空行で入力終了です。
#    - {error} や {input} では複数行を入力したい場合は、Ctrl+Dで入力終了します。
#    - {directory_structure} ではディレクトリ構造を出力するかどうか、もしくは特定パスを指定するか選択します。
#
# 4. 入力が完了すると、最終的に生成されたプロンプト文字列が"agent_simple/.aa_prompt.txt"に書き込まれます。
#
# 5. もし「ファイルが見つからない」旨が表示された場合、指定パスやファイル名が正しいかご確認ください。
#    特に複数ファイルを指定する際はスペースまたは改行で区切って入力し、相対パス指定が正しいか注意してください。
#
# 【コマンド実行例】
#   python main.py --old_folder src --new_folder ../my_app --include_ignore
#
#  上記の例では、 src → ../my_app ディレクトリに置換し、
#  .gitignore と .dirignore に基づく無視リストを考慮してディレクトリ構造を確認します。
#
# 【出力】
#  ・対話形式で入力・処理した結果が、"--new_folder" で指定した場所の "agent_simple/.aa_prompt.txt" に保存されます。
#  ・例えば "--new_folder ../my_app" の場合は、"../my_app/agent_simple/.aa_prompt.txt" に出力されます。
#
# --------------------------------------------------------------------------------------------------
