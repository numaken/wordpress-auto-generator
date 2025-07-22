#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import文一括修正スクリプト
modules内のファイルを新しいディレクトリ構造に対応
"""

import os
import re
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def fix_imports_in_file(file_path):
    """
    単一ファイルのimport文を修正
    
    Args:
        file_path (str): 修正対象ファイルのパス
        
    Returns:
        bool: 修正が行われたかどうか
    """
    try:
        # ファイル読み込み
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        modifications = []
        
        # パターン1: from config import config
        if 'from config import config' in content:
            content = content.replace('from config import config', 'from core.config import config')
            modifications.append('config import修正')
        
        # パターン2: from duplicate_checker import
        old_patterns = [
            ('from duplicate_checker import', 'from core.duplicate_checker import'),
            ('import duplicate_checker', 'from core import duplicate_checker'),
            ('from wrapper import', 'from core.wrapper import'),
            ('import wrapper', 'from core import wrapper')
        ]
        
        for old_pattern, new_pattern in old_patterns:
            if old_pattern in content:
                content = content.replace(old_pattern, new_pattern)
                modifications.append(f'{old_pattern} 修正')
        
        # 修正があった場合のみファイル更新
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logging.info(f"✅ {file_path}: {', '.join(modifications)}")
            return True
        else:
            logging.info(f"   {file_path}: 修正不要")
            return False
            
    except Exception as e:
        logging.error(f"❌ {file_path} エラー: {e}")
        return False

def main():
    """メイン処理"""
    print("🔧 Import文一括修正スクリプト")
    print("=" * 50)
    
    # 修正対象ファイル一覧
    target_files = [
        'modules/advanced/bulk_tools.py',
        'modules/tools/post_updater.py', 
        'modules/wordpress/generator.py',
        'modules/python/generator.py',
        'modules/vue/generator.py',
        'modules/javascript/generator.py',
        'modules/react/generator.py'
    ]
    
    total_files = 0
    fixed_files = 0
    
    for file_path in target_files:
        if os.path.exists(file_path):
            total_files += 1
            logging.info(f"🔍 処理中: {file_path}")
            
            if fix_imports_in_file(file_path):
                fixed_files += 1
        else:
            logging.warning(f"⚠️ ファイルが見つかりません: {file_path}")
    
    print("=" * 50)
    print(f"🎉 修正完了!")
    print(f"   処理ファイル数: {total_files}")
    print(f"   修正ファイル数: {fixed_files}")
    
    if fixed_files > 0:
        print("\n✅ 修正が完了しました。以下のコマンドでテストしてください:")
        print("   python3 main.py --info")
        print("   python3 main.py --tech wordpress --count 1")
    else:
        print("\nℹ️ 修正が必要なファイルは見つかりませんでした。")

if __name__ == "__main__":
    main()