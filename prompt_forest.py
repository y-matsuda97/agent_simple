# プロンプトテンプレート
review_prompt = """# 指示
1. これから添付するコードを日本語で解説してください。
2. コードをレビューし、懸念点と修正案を提示してください。
3. このコードが正しく動作することをチェックするテストコードを記述してください。
{conditional_file_path_request_prompt}
# 解説の制約条件
わかりやすく
データの流れがわかるように上から順に1行ずつ説明
具体的に値を代入したときの挙動を具体例とともに説明する
引数についても説明する
コード中で不適当な記述があれば指摘する

# レビューの制約条件
1関数1機能になるように注意する
まとめられる関数はまとめる
簡潔でわかりやすいコードになるように提案
説明する際は具体例を示して
必要に応じてドキュメントを検索して情報を入手する

# テストコードの制約条件
修正前のコードをテスト対象とすること
レビュー指摘事項を確認するテストを追加すること
問題が判明した場合は原因も報告すること

{directory_structure}
# 該当コード
{code}
"""

revise_prompt = """# 指示
{file_path_request_prompt}コード修正・作成指示に従い、コードを修正または作成してください。

# 制約条件
なるべく簡潔に
要らない関数は消さずにコメントアウトするように
{conditional_file_path_request_prompt}
# コード修正・作成指示
{input}
{directory_structure}
# 該当コード
{code}
"""

error_prompt = """# 指示
{file_path_request_prompt}これから添付コードとエラー内容を解析し，解決方法を挙げてください。

# 制約条件
エラーの原因について示すこと
わかりやすく
具体例を示して
エラーに直接関係ない不適切なコードも知らせる
{conditional_file_path_request_prompt}
# エラー内容
{error}
{directory_structure}

# 該当コード
{code}
"""

ask_prompt = """# 指示
これから添付するコードを参照し、以下の質問に答えてください。
{conditional_file_path_request_prompt}
# 質問
{input}
{directory_structure}

# 該当コード
{code}
"""

code_prompt = """# 以下に該当コードを示す
{code}
"""

file_path_request_prompt = """与えられたディレクトリ構造やコード（コードがある場合）を参考にして必要なファイルを考え、
/var/wwwからはじまるフルパスを**半角スペース区切り1行**で出力すること。その後、私がファイル内のコードを提供します。
ファイルが提供された**後に**以下の指示を遂行してください。
なお、ファイルはこの指示を遂行できるよう網羅的で十分なものを要求すること。
"""

conditional_file_path_request_prompt = """必要なファイルがある場合は、/var/wwwからはじまるフルパスを**半角スペース区切り1行**で出力すること。
すでに十分な情報がある場合は、そのまま回答を開始すること。
"""  # noqa: E501

# プロンプトテンプレートの辞書
prompt_templates = {
    "review_prompt": review_prompt,
    "revise_prompt": revise_prompt,
    "error_prompt": error_prompt,
    "ask_prompt": ask_prompt,
    "code_prompt": code_prompt,
    "conditional_file_path_request_prompt": conditional_file_path_request_prompt,
    "file_path_request_prompt": file_path_request_prompt,
}
