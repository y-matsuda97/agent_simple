import os
import argparse

def create_input_prompt(folder_mapping=None, include_ignore=True):
    """
    プロンプト生成関数。
    デフォルトで現在の作業ディレクトリを基準とし、必要に応じて引数で指定されたディレクトリを利用。
    """
    prompts = {
        "1": ("review_prompt", "コードレビュー"),
        "2": ("revise_prompt", "コード修正"),
        "3": ("error_prompt", "エラー解析"),
        "4": ("ask_prompt", "コードについての質問"),
        "5": ("code_prompt", "コードのみの提示"),
    }

    # プロンプト選択
    prompt_name = select_prompt(prompts)
    prompt_template = prompt_templates[prompt_name]

    # 必要な変数を取得
    required_vars = get_required_variables(prompt_template)

    # 引数またはデフォルトのフォルダマッピングを使用
    old_folder, new_folder = folder_mapping or (os.getcwd(), os.getcwd())

    # 各変数に対してユーザー入力を取得
    input_values = {}
    for var in required_vars:
        input_values[var] = get_input_for_variable(var, folder_mapping=(old_folder, new_folder), include_ignore=include_ignore)

    # プロンプト生成
    formatted_prompt = generate_prompt(prompt_template, input_values)
    return formatted_prompt

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="プロンプト生成スクリプト")
    parser.add_argument(
        "--old_folder",
        type=str,
        default=os.getcwd(),
        help="解析対象の元のディレクトリ（デフォルト: 現在の作業ディレクトリ）",
    )
    parser.add_argument(
        "--new_folder",
        type=str,
        default=os.getcwd(),
        help="置換後のディレクトリ（デフォルト: 現在の作業ディレクトリ）",
    )
    parser.add_argument(
        "--include_ignore",
        action="store_true",
        help=".gitignore と .dirignore を適用するフラグ",
    )

    args = parser.parse_args()

    try:
        # プロンプトを生成
        result = create_input_prompt(
            folder_mapping=(args.old_folder, args.new_folder),
            include_ignore=args.include_ignore
        )

        # 結果を保存
        output_file = ".aa_prompt.txt"
        with open(output_file, "w", encoding="utf-8", errors="ignore") as f:
            f.write(result)

        print(f"\nプロンプトが {output_file} に保存されました。")
    except Exception as e:
        print(f"Error: {e}")
