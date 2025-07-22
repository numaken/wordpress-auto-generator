#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投稿ステータス一括修正スクリプト (fix_post_status.py)
ハードコーディングされた status="draft" を設定ファイルから読み取るように修正
"""

import os
import re
import shutil
from datetime import datetime

# 修正対象ファイル
TARGET_FILES = [
    "generate_articles.py",
    "generate_js_articles.py", 
    "generate_python_articles.py",
    "generate_react_articles.py",
    "generate_vue_articles.py"
]

def backup_file(file_path):
    """ファイルのバックアップを作成"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    print(f"📁 バックアップ作成: {backup_path}")
    return backup_path

def fix_post_to_wordpress_function(content):
    """post_to_wordpress関数の修正"""
    
    # 1. 関数の引数を修正（status: str = "draft" → status: str = None）
    pattern1 = r'def post_to_wordpress\(([^)]*?)status:\s*str\s*=\s*"draft"([^)]*?)\)'
    replacement1 = r'def post_to_wordpress(\1status: str = None\2)'
    content = re.sub(pattern1, replacement1, content)
    
    # 2. 関数内でステータス設定を追加
    pattern2 = r'(def post_to_wordpress.*?\n.*?\n.*?""".*?""")\n'
    replacement2 = r'''\1
    # 🆕 ステータスが指定されていない場合は設定から取得
    if status is None:
        status = config.post_status
    
'''
    content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)
    
    # 3. ログメッセージを修正
    old_log_pattern = r'status_text = "下書き保存" if status == "draft" else "投稿"'
    new_log_pattern = r'status_text = "下書き保存" if status == "draft" else "公開" if status == "publish" else f"ステータス: {status}"'
    content = content.replace(old_log_pattern, new_log_pattern)
    
    return content

def fix_generate_and_post_function(content):
    """generate_and_post系関数の修正"""
    
    # post_to_wordpress の呼び出しからstatusパラメータを削除
    patterns = [
        (r'post_to_wordpress\(([^,]+),([^,]+),([^,]+),\s*"draft"\)', r'post_to_wordpress(\1,\2,\3)'),
        (r'post_to_wordpress\(([^,]+),([^,]+),([^,]+),\s*"publish"\)', r'post_to_wordpress(\1,\2,\3)'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    return content

def fix_file(file_path):
    """単一ファイルの修正"""
    if not os.path.exists(file_path):
        print(f"⚠️  ファイルが見つかりません: {file_path}")
        return False
    
    print(f"🔧 修正中: {file_path}")
    
    # バックアップ作成
    backup_path = backup_file(file_path)
    
    try:
        # ファイル読み込み
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 修正適用
        content = fix_post_to_wordpress_function(content)
        content = fix_generate_and_post_function(content)
        
        # 変更があった場合のみ書き込み
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 修正完了: {file_path}")
            return True
        else:
            print(f"ℹ️  変更なし: {file_path}")
            # バックアップ削除
            os.remove(backup_path)
            return False
            
    except Exception as e:
        print(f"❌ 修正失敗: {file_path} - {e}")
        # エラー時は元ファイルを復元
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
            print(f"🔄 ファイルを復元しました: {file_path}")
        return False

def main():
    """メイン実行"""
    print("🚀 投稿ステータス設定対応の一括修正開始")
    print("=" * 50)
    
    success_count = 0
    total_count = len(TARGET_FILES)
    
    for file_name in TARGET_FILES:
        if fix_file(file_name):
            success_count += 1
    
    print("=" * 50)
    print(f"🎉 修正完了: {success_count}/{total_count} ファイル")
    
    if success_count > 0:
        print("\n次の手順:")
        print("1. .envファイルに POST_STATUS=publish を追加")
        print("2. config.pyを新しいバージョンに置き換え")
        print("3. 記事生成スクリプトをテスト実行")
    
    print("\n⚠️  問題がある場合は .backup_* ファイルから復元できます")

if __name__ == "__main__":
    main()