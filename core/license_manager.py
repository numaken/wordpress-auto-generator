#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
License Manager for WordPress Auto Generator System
ライセンス管理システム - エディション別機能制限とアップセル機能
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class LicenseManager:
    """
    ライセンス管理システム
    エディション別機能制限とアップセル機能を提供
    """
    
    # エディション設定
    EDITIONS = {
        'entry': {
            'name': 'エントリー版',
            'price': 12800,
            'monthly_limit': 50,
            'technologies': ['wordpress'],
            'features': ['basic_generation', 'duplicate_check'],
            'description': 'WordPress記事のみ、月50記事まで'
        },
        'standard': {
            'name': 'スタンダード版', 
            'price': 24800,
            'monthly_limit': 200,
            'technologies': ['wordpress', 'javascript', 'python', 'react', 'vue', 'sql'],
            'features': ['basic_generation', 'duplicate_check', 'multi_tech', 'bulk_publish'],
            'description': '6技術対応、月200記事まで'
        },
        'pro': {
            'name': 'プロ版',
            'price': 49800,
            'monthly_limit': float('inf'),
            'technologies': ['wordpress', 'javascript', 'python', 'react', 'vue', 'sql'],
            'features': ['basic_generation', 'duplicate_check', 'multi_tech', 'bulk_publish', 'advanced_tools', 'tag_management'],
            'description': '全機能、無制限'
        }
    }
    
    def __init__(self, edition: str = None):
        """
        ライセンスマネージャー初期化
        
        Args:
            edition (str): エディション指定 (entry/standard/pro)
        """
        self.edition = edition or os.getenv('EDITION', 'entry')
        self.usage_file = f"usage_{self.edition}.json"
        
        # エディション検証
        if self.edition not in self.EDITIONS:
            logging.error(f"❌ 無効なエディション: {self.edition}")
            raise ValueError(f"無効なエディション: {self.edition}")
        
        # 使用状況読み込み
        self.usage_data = self._load_usage_data()
        
        logging.info(f"🔐 ライセンス管理システム初期化完了")
        logging.info(f"📋 現在のエディション: {self.get_edition_info()['name']}")
    
    def get_edition_info(self) -> Dict[str, Any]:
        """現在のエディション情報を取得"""
        return self.EDITIONS[self.edition].copy()
    
    def get_available_technologies(self) -> List[str]:
        """利用可能な技術スタックを取得"""
        return self.EDITIONS[self.edition]['technologies'].copy()
    
    def get_available_features(self) -> List[str]:
        """利用可能な機能を取得"""
        return self.EDITIONS[self.edition]['features'].copy()
    
    def check_technology_access(self, technology: str) -> bool:
        """
        技術スタックへのアクセス権限確認
        
        Args:
            technology (str): 技術名 (wordpress, javascript, python, react, vue, sql)
            
        Returns:
            bool: アクセス可能かどうか
        """
        available_techs = self.get_available_technologies()
        has_access = technology.lower() in available_techs
        
        if not has_access:
            logging.warning(f"🚫 技術スタック '{technology}' は {self.get_edition_info()['name']} では利用できません")
            self._show_upsell_message(technology)
        
        return has_access
    
    def check_feature_access(self, feature: str) -> bool:
        """
        機能へのアクセス権限確認
        
        Args:
            feature (str): 機能名
            
        Returns:
            bool: アクセス可能かどうか
        """
        available_features = self.get_available_features()
        has_access = feature in available_features
        
        if not has_access:
            logging.warning(f"🚫 機能 '{feature}' は {self.get_edition_info()['name']} では利用できません")
            self._show_upsell_message(feature)
        
        return has_access
    
    def check_usage_limit(self, requested_count: int = 1) -> bool:
        """
        月間使用制限チェック
        
        Args:
            requested_count (int): 生成予定記事数
            
        Returns:
            bool: 制限内かどうか
        """
        current_month = datetime.now().strftime('%Y-%m')
        monthly_limit = self.EDITIONS[self.edition]['monthly_limit']
        
        # 無制限の場合
        if monthly_limit == float('inf'):
            return True
        
        # 現在の使用量取得
        current_usage = self.usage_data.get(current_month, 0)
        total_after_request = current_usage + requested_count
        
        if total_after_request > monthly_limit:
            remaining = monthly_limit - current_usage
            logging.warning(f"🚫 月間制限に達します")
            logging.warning(f"   現在の使用量: {current_usage}/{monthly_limit}")
            logging.warning(f"   残り使用可能: {remaining}記事")
            logging.warning(f"   リクエスト: {requested_count}記事")
            self._show_usage_upsell_message(current_usage, monthly_limit)
            return False
        
        logging.info(f"✅ 使用制限OK: {total_after_request}/{monthly_limit}")
        return True
    
    def record_usage(self, count: int = 1) -> None:
        """
        使用量を記録
        
        Args:
            count (int): 生成した記事数
        """
        current_month = datetime.now().strftime('%Y-%m')
        
        if current_month not in self.usage_data:
            self.usage_data[current_month] = 0
        
        self.usage_data[current_month] += count
        self._save_usage_data()
        
        monthly_limit = self.EDITIONS[self.edition]['monthly_limit']
        current_usage = self.usage_data[current_month]
        
        if monthly_limit != float('inf'):
            logging.info(f"📊 使用量記録: {current_usage}/{monthly_limit} (+{count})")
        else:
            logging.info(f"📊 使用量記録: {current_usage} (+{count}) [無制限]")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """使用統計取得"""
        current_month = datetime.now().strftime('%Y-%m')
        current_usage = self.usage_data.get(current_month, 0)
        monthly_limit = self.EDITIONS[self.edition]['monthly_limit']
        
        stats = {
            'edition': self.get_edition_info(),
            'current_month': current_month,
            'current_usage': current_usage,
            'monthly_limit': monthly_limit,
            'remaining': monthly_limit - current_usage if monthly_limit != float('inf') else float('inf'),
            'usage_percentage': (current_usage / monthly_limit * 100) if monthly_limit != float('inf') else 0
        }
        
        return stats
    
    def show_edition_info(self) -> None:
        """エディション情報表示"""
        info = self.get_edition_info()
        stats = self.get_usage_stats()
        
        print("\n" + "="*60)
        print(f"🏷️  {info['name']} (¥{info['price']:,}/月)")
        print("="*60)
        print(f"📝 {info['description']}")
        print(f"\n📊 今月の使用状況:")
        
        if info['monthly_limit'] == float('inf'):
            print(f"   使用量: {stats['current_usage']}記事 [無制限]")
        else:
            print(f"   使用量: {stats['current_usage']}/{stats['monthly_limit']}記事")
            print(f"   残り: {stats['remaining']}記事")
            print(f"   使用率: {stats['usage_percentage']:.1f}%")
        
        print(f"\n🛠️  利用可能な技術:")
        for tech in info['technologies']:
            print(f"   ✅ {tech}")
        
        print(f"\n⚡ 利用可能な機能:")
        for feature in info['features']:
            print(f"   ✅ {feature}")
        
        print("="*60 + "\n")
    
    def _load_usage_data(self) -> Dict[str, int]:
        """使用データ読み込み"""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logging.warning(f"⚠️ 使用データ読み込みエラー: {e}")
        
        return {}
    
    def _save_usage_data(self) -> None:
        """使用データ保存"""
        try:
            with open(self.usage_file, 'w', encoding='utf-8') as f:
                json.dump(self.usage_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"❌ 使用データ保存エラー: {e}")
    
    def _show_upsell_message(self, requested_feature: str) -> None:
        """アップセル メッセージ表示"""
        current_edition = self.get_edition_info()
        
        # 上位エディションでアクセス可能かチェック
        upgrade_suggestions = []
        
        for edition_key, edition_info in self.EDITIONS.items():
            if (edition_key != self.edition and 
                (requested_feature in edition_info.get('technologies', []) or 
                 requested_feature in edition_info.get('features', []))):
                upgrade_suggestions.append(edition_info)
        
        if upgrade_suggestions:
            print(f"\n💡 アップグレードのご案内")
            print(f"━━━━━━━━━━━━━━━━━━━━")
            print(f"'{requested_feature}' は上位エディションでご利用いただけます:")
            
            for suggestion in upgrade_suggestions:
                print(f"\n🚀 {suggestion['name']} (¥{suggestion['price']:,}/月)")
                print(f"   {suggestion['description']}")
            
            print(f"\n現在のプラン: {current_edition['name']} (¥{current_edition['price']:,}/月)")
            print(f"━━━━━━━━━━━━━━━━━━━━\n")
    
    def _show_usage_upsell_message(self, current_usage: int, limit: int) -> None:
        """使用量制限時のアップセルメッセージ"""
        current_edition = self.get_edition_info()
        
        # 上位エディションの提案
        upgrade_options = []
        for edition_key, edition_info in self.EDITIONS.items():
            if (edition_key != self.edition and 
                edition_info['monthly_limit'] > limit):
                upgrade_options.append(edition_info)
        
        if upgrade_options:
            print(f"\n💡 より多くの記事生成をご希望の場合")
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            for option in upgrade_options:
                if option['monthly_limit'] == float('inf'):
                    limit_text = "無制限"
                else:
                    limit_text = f"{option['monthly_limit']}記事/月"
                
                print(f"\n🚀 {option['name']} (¥{option['price']:,}/月)")
                print(f"   制限: {limit_text}")
                print(f"   {option['description']}")
            
            print(f"\n現在のプラン: {current_edition['name']} ({limit}記事/月)")
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n")


def get_license_manager() -> LicenseManager:
    """ライセンスマネージャーのインスタンス取得"""
    return LicenseManager()


if __name__ == "__main__":
    # テスト実行
    print("🔐 ライセンス管理システム テスト")
    print("="*50)
    
    # 各エディションでテスト
    for edition in ['entry', 'standard', 'pro']:
        print(f"\n🧪 {edition}版 テスト")
        print("-" * 30)
        
        # 環境変数設定
        os.environ['EDITION'] = edition
        
        # マネージャー作成
        manager = LicenseManager(edition)
        
        # 情報表示
        manager.show_edition_info()
        
        # 技術スタックアクセステスト
        print("🔍 技術スタックアクセステスト:")
        for tech in ['wordpress', 'javascript', 'python']:
            result = manager.check_technology_access(tech)
            status = "✅" if result else "❌"
            print(f"   {status} {tech}")
        
        # 使用制限テスト
        print("\n🔍 使用制限テスト:")
        result = manager.check_usage_limit(5)
        status = "✅" if result else "❌"
        print(f"   {status} 5記事生成リクエスト")
        
        print("\n" + "="*50)