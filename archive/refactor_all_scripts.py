#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import shutil
from datetime import datetime

def backup_file(filepath):
    """ファイルをバックアップ"""
    backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print(f"✅ バックアップ作成: {backup_path}")
    return backup_path

def refactor_script_to_use_tag_utils(filepath):
    """
    スクリプトファイルをtag_utils使用に修正
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # バックアップ作成
        backup_file(filepath)
        
        # 技術タイプを判定
        tech_mapping = {
            'js_articles': 'javascript',
            'python_articles': 'python', 
            'react_articles': 'react',
            'vue_articles': 'vue',
            'generate_articles': 'wordpress'
        }
        
        tech_type = 'general'
        for key, value in tech_mapping.items():
            if key in filepath:
                tech_type = value
                break
        
        # 1. インポート追加
        import_pattern = r'(from duplicate_checker import.*?\n)'
        if re.search(import_pattern, content):
            tag_utils_import = """
# タグ処理モジュールをインポート
try:
    from tag_utils import post_to_wordpress_with_tags
except ImportError:
    logging.error("❌ tag_utils.py が見つかりません")
    sys.exit(1)
"""
            content = re.sub(import_pattern, r'\1' + tag_utils_import, content)
        
        # 2. 重複関数を削除
        # get_or_create_tag_id 関数を削除
        tag_id_pattern = r'def get_or_create_tag_id\(.*?\n(?:.*?\n)*?    return None\n\n'
        content = re.sub(tag_id_pattern, '', content, flags=re.MULTILINE | re.DOTALL)
        
        # get_tag_ids 関数を削除
        tag_ids_pattern = r'def get_tag_ids\(.*?\n(?:.*?\n)*?    return tag_ids\n\n'
        content = re.sub(tag_ids_pattern, '', content, flags=re.MULTILINE | re.DOTALL)
        
        # post_to_wordpress 関数を削除
        post_pattern = r'def post_to_wordpress\(.*?\n(?:.*?\n)*?        return False\n\n'
        content = re.sub(post_pattern, '', content, flags=re.MULTILINE | re.DOTALL)
        
        # 3. 新しい投稿関数呼び出しに置換
        old_call_pattern = r'post_to_wordpress\(topic, html_content, CATEGORY_ID, "draft"\)'
        new_call = f'''post_to_wordpress_with_tags(
        title=topic,
        content=html_content,
        category_id=CATEGORY_ID,
        tag_category="{tech_type}",
        config=config,
        status="draft"
    )'''
        content = re.sub(old_call_pattern, new_call, content)
        
        # 4. ファイルに書き戻し
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ {filepath} をリファクタリングしました")
        print(f"   - 技術タイプ: {tech_type}")
        print(f"   - 重複関数を削除")
        print(f"   - tag_utils.py を使用するように修正")
        return True
        
    except Exception as e:
        print(f"❌ {filepath} のリファクタリングエラー: {e}")
        return False

def main():
    print("🔧 全スクリプト tag_utils.py 対応リファクタリングツール")
    print("=" * 60)
    
    # 対象ファイルを検索
    target_files = []
    for file in os.listdir('.'):
        if file.endswith('.py') and 'generate' in file and 'article' in file:
            if file != 'generate_multi_tech.py':  # マルチテックスクリプトは除外
                target_files.append(file)
    
    if not target_files:
        print("⚠️  対象ファイルが見つかりません")
        return
    
    print(f"📁 対象ファイル: {len(target_files)}個")
    for file in target_files:
        print(f"   - {file}")
    
    # 実行確認
    response = input("\nリファクタリングを実行しますか？ (y/N): ")
    if response.lower() != 'y':
        print("リファクタリングをキャンセルしました")
        return
    
    print("\n🔧 リファクタリング実行中...")
    print("-" * 40)
    
    success_count = 0
    for file in target_files:
        if refactor_script_to_use_tag_utils(file):
            success_count += 1
    
    print(f"\n🎉 リファクタリング完了!")
    print(f"✅ 成功: {success_count}/{len(target_files)}個")
    print("\n📝 次のステップ:")
    print("1. 各スクリプトをテスト実行してエラーがないか確認")
    print("2. tag_utils.py が正しく動作するか確認")
    print("3. 不要になったバックアップファイルを削除")

if __name__ == "__main__":
    main()