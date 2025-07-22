#!/usr/bin/env python3
"""
WordPress記事自動生成システム - 改善版設定管理
.envファイルから環境変数を自動読み込み
"""
import os
import sys
import logging
from typing import Optional
from base64 import b64encode

# python-dotenvがある場合は.envファイルを読み込み
try:
    from dotenv import load_dotenv
    load_dotenv()  # .envファイルから環境変数を読み込み
    print("✅ .envファイルを読み込みました")
except ImportError:
    print("⚠️  python-dotenvがインストールされていません")
    print("   pip install python-dotenv で実行してください")

class Config:
    """システム設定クラス"""
    
    def __init__(self):
        # 必須環境変数のチェック
        self.openai_api_key = self._get_required_env("OPENAI_API_KEY")
        self.wp_app_pass = self._get_required_env("WP_APP_PASS")
        
        # オプション環境変数（デフォルト値あり）
        self.wp_site_url = os.getenv("WP_SITE_URL", "https://numaken.net")
        self.wp_user = os.getenv("WP_USER", "numaken")
        self.category_id = int(os.getenv("CATEGORY_ID", "2"))
        self.new_count = int(os.getenv("NEW_COUNT", "5"))
        self.script_name = os.getenv("SCRIPT_NAME", "generate_articles.py")
        
        # 🆕 投稿ステータス設定を追加
        self.post_status = os.getenv("POST_STATUS", "publish")  # draft, publish, private, pending
        
        # ログ設定
        self._setup_logging()
        
        # 設定値の表示（デバッグ用）
        self._log_config()
    
    def _get_required_env(self, key: str) -> str:
        """必須環境変数を取得"""
        value = os.getenv(key)
        if not value:
            logging.error(f"❌ 環境変数 {key} が設定されていません")
            logging.error(f"   .envファイルに {key}=your_value を追加してください")
            sys.exit(1)
        return value
    
    def _setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def _log_config(self):
        """設定値をログ出力（APIキーは伏せる）"""
        logging.info(f"🔧 設定読み込み完了:")
        logging.info(f"   サイトURL: {self.wp_site_url}")
        logging.info(f"   ユーザー: {self.wp_user}")
        logging.info(f"   カテゴリID: {self.category_id}")
        logging.info(f"   生成数: {self.new_count}")
        logging.info(f"   投稿ステータス: {self.post_status}")  # 🆕 投稿ステータスを表示
        logging.info(f"   APIキー: {self.openai_api_key[:10]}...")
    
    def get_auth_header(self) -> dict:
        """WordPress認証ヘッダーを生成"""
        auth_str = f"{self.wp_user}:{self.wp_app_pass}"
        auth_header = "Basic " + b64encode(auth_str.encode()).decode()
        
        return {
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    
    def get_openai_headers(self) -> dict:
        """OpenAI認証ヘッダーを生成"""
        return {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
    
    def validate_openai_key(self) -> bool:
        """OpenAI APIキーの形式チェック"""
        if not self.openai_api_key.startswith('sk-'):
            logging.error("❌ 無効なOpenAI APIキー形式です")
            return False
        return True
    
    def validate_post_status(self) -> bool:
        """投稿ステータスの有効性チェック"""
        valid_statuses = ["draft", "publish", "private", "pending"]
        if self.post_status not in valid_statuses:
            logging.error(f"❌ 無効な投稿ステータス: {self.post_status}")
            logging.error(f"   有効な値: {', '.join(valid_statuses)}")
            return False
        return True

# グローバル設定インスタンス
config = Config()

# 設定の妥当性チェック
if not config.validate_openai_key():
    sys.exit(1)

if not config.validate_post_status():
    sys.exit(1)