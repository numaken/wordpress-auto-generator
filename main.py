#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WordPress Auto Generator System - Main Script
統合実行スクリプト - ライセンス制御 + 全機能統合

Usage:
    python3 main.py --info                    # エディション情報表示
    python3 main.py --tech wordpress --count 3  # WordPress記事生成
    python3 main.py --tech javascript --count 1 # JavaScript記事生成
    python3 main.py --multi-tech --count 2      # マルチ技術記事生成
    python3 main.py --bulk-publish              # 下書き一括公開
"""

import argparse
import sys
import os
import logging
from typing import Optional, Dict, Any

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# コアシステムインポート
from core.license_manager import LicenseManager
from core.config import config
from core.wrapper import ArticleGeneratorWrapper

# モジュールインポート - アダプタークラス使用
from modules.adapters import (
    WordPressGenerator,
    JavaScriptGenerator,
    PythonGenerator,
    ReactGenerator,
    VueGenerator
)

# 高度な機能モジュール
try:
    from modules.advanced.multi_tech import MultiTechGenerator
    from modules.advanced.bulk_tools import BulkPublisher
    from modules.tools.tag_manager import TagManager
    from modules.tools.post_updater import PostUpdater
    ADVANCED_MODULES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"⚠️ 高度な機能モジュールが見つかりません: {e}")
    # ダミークラスを定義
    class MultiTechGenerator:
        def generate_multi_tech_article(self):
            logging.error("❌ MultiTechGenerator は利用できません")
            return False
    
    class BulkPublisher:
        def publish_all_drafts(self):
            logging.error("❌ BulkPublisher は利用できません")
            return False
    
    class TagManager:
        def get_tag_statistics(self):
            logging.error("❌ TagManager は利用できません")
            return {}
    
    class PostUpdater:
        pass
    
    ADVANCED_MODULES_AVAILABLE = False

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class MainController:
    """
    メインコントローラー
    ライセンス管理と全機能を統合
    """
    
    def __init__(self):
        """初期化"""
        self.license_manager = LicenseManager()
        self.wrapper = ArticleGeneratorWrapper()
        
        # 技術スタック別ジェネレーター
        self.generators = {
            'wordpress': WordPressGenerator,
            'javascript': JavaScriptGenerator,
            'python': PythonGenerator,
            'react': ReactGenerator,
            'vue': VueGenerator
        }
        
        logging.info("🚀 WordPress Auto Generator System 起動")
    
    def show_info(self) -> None:
        """エディション情報表示"""
        print("\n🚀 WordPress Auto Generator System")
        print("=" * 60)
        
        # ライセンス情報表示
        self.license_manager.show_edition_info()
        
        # システム情報表示
        edition_info = self.license_manager.get_edition_info()
        print("🛠️  システム情報:")
        print(f"   サイトURL: {config.wp_site_url}")
        print(f"   ユーザー: {config.wp_user}")
        print(f"   カテゴリID: {config.category_id}")
        print(f"   投稿ステータス: {config.post_status}")
        print()
        
        # 使用可能なコマンド例
        print("📋 使用可能なコマンド例:")
        print(f"   エディション情報表示:")
        print(f"     python3 main.py --info")
        print()
        
        for tech in edition_info['technologies']:
            print(f"   {tech.capitalize()}記事生成:")
            print(f"     python3 main.py --tech {tech} --count 1")
        
        if 'multi_tech' in edition_info['features']:
            print(f"   マルチ技術記事生成:")
            print(f"     python3 main.py --multi-tech --count 1")
        
        if 'bulk_publish' in edition_info['features']:
            print(f"   下書き一括公開:")
            print(f"     python3 main.py --bulk-publish")
        
        if 'tag_management' in edition_info['features']:
            print(f"   タグ管理:")
            print(f"     python3 main.py --manage-tags")
        
        print("=" * 60 + "\n")
    
    def generate_articles(self, technology: str, count: int) -> bool:
        """
        記事生成実行
        
        Args:
            technology (str): 技術スタック
            count (int): 生成数
            
        Returns:
            bool: 成功かどうか
        """
        # 技術スタックアクセス確認
        if not self.license_manager.check_technology_access(technology):
            return False
        
        # 使用制限確認
        if not self.license_manager.check_usage_limit(count):
            return False
        
        # SQLの場合は未実装メッセージ
        if technology == 'sql':
            logging.warning("⚠️ SQL記事生成機能は現在開発中です")
            logging.info("近日中にリリース予定です。しばらくお待ちください。")
            return False
        
        # ジェネレーター取得
        if technology not in self.generators:
            logging.error(f"❌ 未対応の技術スタック: {technology}")
            return False
        
        try:
            # 記事生成実行
            generator_class = self.generators[technology]
            generator = generator_class()
            
            logging.info(f"📝 {technology.capitalize()}記事を{count}件生成開始...")
            
            # ラッパー経由で実行（重複チェック付き）
            success = self.wrapper.generate_with_duplicate_check(
                generator=generator,
                count=count,
                technology=technology
            )
            
            if success:
                # 使用量記録
                self.license_manager.record_usage(count)
                logging.info(f"✅ {technology.capitalize()}記事{count}件の生成が完了しました")
                return True
            else:
                logging.error(f"❌ {technology.capitalize()}記事の生成に失敗しました")
                return False
                
        except Exception as e:
            logging.error(f"❌ 記事生成エラー: {e}")
            return False
    
    def generate_multi_tech(self, count: int) -> bool:
        """
        マルチ技術記事生成
        
        Args:
            count (int): 生成数
            
        Returns:
            bool: 成功かどうか
        """
        # 機能アクセス確認
        if not self.license_manager.check_feature_access('multi_tech'):
            return False
        
        # 使用制限確認  
        if not self.license_manager.check_usage_limit(count):
            return False
        
        try:
            logging.info(f"🔄 マルチ技術記事を{count}件生成開始...")
            
            # マルチ技術ジェネレーター実行
            multi_generator = MultiTechGenerator()
            
            success_count = 0
            for i in range(count):
                try:
                    result = multi_generator.generate_multi_tech_article()
                    if result:
                        success_count += 1
                        logging.info(f"✅ マルチ技術記事 {i+1}/{count} 生成完了")
                    else:
                        logging.warning(f"⚠️ マルチ技術記事 {i+1}/{count} 生成失敗")
                except Exception as e:
                    logging.error(f"❌ マルチ技術記事 {i+1}/{count} エラー: {e}")
            
            if success_count > 0:
                # 使用量記録
                self.license_manager.record_usage(success_count)
                logging.info(f"✅ マルチ技術記事{success_count}件の生成が完了しました")
                return True
            else:
                logging.error("❌ マルチ技術記事の生成に失敗しました")
                return False
                
        except Exception as e:
            logging.error(f"❌ マルチ技術記事生成エラー: {e}")
            return False
    
    def bulk_publish(self) -> bool:
        """
        下書き一括公開
        
        Returns:
            bool: 成功かどうか
        """
        # 機能アクセス確認
        if not self.license_manager.check_feature_access('bulk_publish'):
            return False
        
        try:
            logging.info("📤 下書き記事の一括公開を開始...")
            
            bulk_publisher = BulkPublisher()
            result = bulk_publisher.publish_all_drafts()
            
            if result:
                logging.info("✅ 下書き記事の一括公開が完了しました")
                return True
            else:
                logging.error("❌ 下書き記事の一括公開に失敗しました")
                return False
                
        except Exception as e:
            logging.error(f"❌ 一括公開エラー: {e}")
            return False
    
    def manage_tags(self) -> bool:
        """
        タグ管理機能
        
        Returns:
            bool: 成功かどうか
        """
        # 機能アクセス確認
        if not self.license_manager.check_feature_access('tag_management'):
            return False
        
        try:
            logging.info("🏷️ タグ管理機能を実行...")
            
            tag_manager = TagManager()
            # タグ統計表示
            stats = tag_manager.get_tag_statistics()
            
            logging.info(f"📊 タグ統計:")
            logging.info(f"   総タグ数: {stats.get('total_tags', 0)}")
            logging.info(f"   使用済みタグ数: {stats.get('used_tags', 0)}")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ タグ管理エラー: {e}")
            return False


def create_parser() -> argparse.ArgumentParser:
    """コマンドライン引数パーサー作成"""
    parser = argparse.ArgumentParser(
        description='WordPress Auto Generator System - 統合実行スクリプト',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python3 main.py --info                      # エディション情報表示
  python3 main.py --tech wordpress --count 3  # WordPress記事3件生成
  python3 main.py --tech javascript --count 1 # JavaScript記事1件生成
  python3 main.py --multi-tech --count 2      # マルチ技術記事2件生成
  python3 main.py --bulk-publish              # 下書き一括公開
  python3 main.py --manage-tags               # タグ管理
        """
    )
    
    # 情報表示
    parser.add_argument(
        '--info',
        action='store_true',
        help='エディション情報と使用可能な機能を表示'
    )
    
    # 技術スタック指定
    parser.add_argument(
        '--tech',
        choices=['wordpress', 'javascript', 'python', 'react', 'vue', 'sql'],
        help='記事生成する技術スタック'
    )
    
    # 生成数指定
    parser.add_argument(
        '--count',
        type=int,
        default=1,
        help='生成する記事数 (デフォルト: 1)'
    )
    
    # マルチ技術記事生成
    parser.add_argument(
        '--multi-tech',
        action='store_true',
        help='マルチ技術記事生成 (スタンダード版以上)'
    )
    
    # 一括公開
    parser.add_argument(
        '--bulk-publish',
        action='store_true', 
        help='下書き記事の一括公開 (スタンダード版以上)'
    )
    
    # タグ管理
    parser.add_argument(
        '--manage-tags',
        action='store_true',
        help='タグ管理機能 (プロ版のみ)'
    )
    
    return parser


def main():
    """メイン処理"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 引数チェック
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    try:
        # メインコントローラー初期化
        controller = MainController()
        
        # 処理分岐
        if args.info:
            controller.show_info()
            
        elif args.tech:
            if args.count <= 0:
                logging.error("❌ 生成数は1以上を指定してください")
                return
            
            success = controller.generate_articles(args.tech, args.count)
            if not success:
                sys.exit(1)
        
        elif args.multi_tech:
            if args.count <= 0:
                logging.error("❌ 生成数は1以上を指定してください")
                return
            
            success = controller.generate_multi_tech(args.count)
            if not success:
                sys.exit(1)
        
        elif args.bulk_publish:
            success = controller.bulk_publish()
            if not success:
                sys.exit(1)
        
        elif args.manage_tags:
            success = controller.manage_tags()
            if not success:
                sys.exit(1)
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        logging.info("\n⏹️ 処理が中断されました")
    except Exception as e:
        logging.error(f"❌ システムエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()