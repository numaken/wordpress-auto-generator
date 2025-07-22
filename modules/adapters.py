#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generator Adapters
既存の関数ベースジェネレーターをクラスベースでラップするアダプター
"""

import logging
from typing import Optional, Any

# 既存の関数ベースジェネレーターをインポート
try:
    from modules.wordpress.generator import generate_and_post as wp_generate
    from modules.javascript.generator import generate_and_post_js as js_generate
    from modules.python.generator import generate_and_post_python as py_generate
except ImportError:
    # Python ジェネレーターが generate_and_post_python でない場合の対応
    try:
        from modules.python.generator import generate_and_post as py_generate
    except ImportError:
        py_generate = None

try:
    from modules.react.generator import generate_and_post_react as react_generate
except ImportError:
    try:
        from modules.react.generator import generate_and_post as react_generate
    except ImportError:
        react_generate = None

try:
    from modules.vue.generator import generate_and_post_vue as vue_generate
except ImportError:
    try:
        from modules.vue.generator import generate_and_post as vue_generate
    except ImportError:
        vue_generate = None

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class BaseGeneratorAdapter:
    """ジェネレーターアダプターの基底クラス"""
    
    def __init__(self, technology: str):
        self.technology = technology
        self.generated_count = 0
        logging.info(f"🎯 {technology} ジェネレーターアダプター初期化")
    
    def generate_article(self, topic: Optional[str] = None) -> bool:
        """
        記事生成メソッド（サブクラスでオーバーライド）
        
        Args:
            topic (str, optional): 生成したいトピック
            
        Returns:
            bool: 成功かどうか
        """
        raise NotImplementedError("Subclass must implement generate_article method")
    
    def generate_articles(self, count: int = 1) -> bool:
        """
        複数記事生成
        
        Args:
            count (int): 生成数
            
        Returns:
            bool: 成功かどうか
        """
        success_count = 0
        
        for i in range(count):
            try:
                if self.generate_article():
                    success_count += 1
                    self.generated_count += 1
                    logging.info(f"✅ {self.technology} 記事 {i+1}/{count} 生成完了")
                else:
                    logging.warning(f"⚠️ {self.technology} 記事 {i+1}/{count} 生成失敗")
            except Exception as e:
                logging.error(f"❌ {self.technology} 記事 {i+1}/{count} エラー: {e}")
        
        return success_count > 0
    
    def generate_article_with_topic(self, topic: str) -> bool:
        """
        トピック指定で記事生成
        
        Args:
            topic (str): トピック
            
        Returns:
            bool: 成功かどうか
        """
        return self.generate_article(topic)


class WordPressGenerator(BaseGeneratorAdapter):
    """WordPress ジェネレーターアダプター"""
    
    def __init__(self):
        super().__init__("WordPress")
        self.generate_function = wp_generate
    
    def generate_article(self, topic: Optional[str] = None) -> bool:
        """WordPress記事生成"""
        try:
            # トピックがない場合はデフォルトトピックを使用
            if not topic:
                # デフォルトトピックをいくつか用意
                default_topics = [
                    "WordPressでカスタム投稿タイプを作成する方法",
                    "WordPressフックの使い方とベストプラクティス", 
                    "WordPressのREST APIを活用した開発手法",
                    "WordPressプラグイン開発の基礎知識",
                    "WordPressテーマ開発で知っておくべきポイント"
                ]
                import random
                topic = random.choice(default_topics)
                logging.info(f"📝 デフォルトトピックを使用: {topic}")
            
            # 既存の関数を直接topicを引数として呼び出し
            result = self.generate_function(topic)
            
            return result is not False  # Noneや正常終了をTrueとして扱う
            
        except Exception as e:
            logging.error(f"❌ WordPress記事生成エラー: {e}")
            # 環境変数方式で再試行
            try:
                logging.info("🔄 環境変数方式で再試行...")
                import os
                original_topic = os.environ.get("SINGLE_TOPIC")
                os.environ["SINGLE_TOPIC"] = topic
                
                # 引数なしで呼び出し
                result = self.generate_function()
                
                # 環境変数を元に戻す
                if original_topic is not None:
                    os.environ["SINGLE_TOPIC"] = original_topic
                elif "SINGLE_TOPIC" in os.environ:
                    del os.environ["SINGLE_TOPIC"]
                
                return result is not False
                
            except Exception as e2:
                logging.error(f"❌ 環境変数方式でも失敗: {e2}")
                return False


class JavaScriptGenerator(BaseGeneratorAdapter):
    """JavaScript ジェネレーターアダプター"""
    
    def __init__(self):
        super().__init__("JavaScript")
        self.generate_function = js_generate
    
    def generate_article(self, topic: Optional[str] = None) -> bool:
        """JavaScript記事生成"""
        try:
            # トピック指定がある場合は環境変数に設定
            if topic:
                import os
                os.environ["SINGLE_TOPIC"] = topic
            
            # 既存の関数を呼び出し
            result = self.generate_function()
            
            # 環境変数をクリア
            if topic and "SINGLE_TOPIC" in os.environ:
                del os.environ["SINGLE_TOPIC"]
            
            return result is not False
            
        except Exception as e:
            logging.error(f"❌ JavaScript記事生成エラー: {e}")
            return False


class PythonGenerator(BaseGeneratorAdapter):
    """Python ジェネレーターアダプター"""
    
    def __init__(self):
        super().__init__("Python")
        self.generate_function = py_generate
    
    def generate_article(self, topic: Optional[str] = None) -> bool:
        """Python記事生成"""
        if not self.generate_function:
            logging.error("❌ Python ジェネレーター関数が見つかりません")
            return False
        
        try:
            # トピック指定がある場合は環境変数に設定
            if topic:
                import os
                os.environ["SINGLE_TOPIC"] = topic
            
            # 既存の関数を呼び出し
            result = self.generate_function()
            
            # 環境変数をクリア
            if topic and "SINGLE_TOPIC" in os.environ:
                del os.environ["SINGLE_TOPIC"]
            
            return result is not False
            
        except Exception as e:
            logging.error(f"❌ Python記事生成エラー: {e}")
            return False


class ReactGenerator(BaseGeneratorAdapter):
    """React ジェネレーターアダプター"""
    
    def __init__(self):
        super().__init__("React")
        self.generate_function = react_generate
    
    def generate_article(self, topic: Optional[str] = None) -> bool:
        """React記事生成"""
        if not self.generate_function:
            logging.error("❌ React ジェネレーター関数が見つかりません")
            return False
        
        try:
            # トピック指定がある場合は環境変数に設定
            if topic:
                import os
                os.environ["SINGLE_TOPIC"] = topic
            
            # 既存の関数を呼び出し
            result = self.generate_function()
            
            # 環境変数をクリア
            if topic and "SINGLE_TOPIC" in os.environ:
                del os.environ["SINGLE_TOPIC"]
            
            return result is not False
            
        except Exception as e:
            logging.error(f"❌ React記事生成エラー: {e}")
            return False


class VueGenerator(BaseGeneratorAdapter):
    """Vue.js ジェネレーターアダプター"""
    
    def __init__(self):
        super().__init__("Vue.js")
        self.generate_function = vue_generate
    
    def generate_article(self, topic: Optional[str] = None) -> bool:
        """Vue.js記事生成"""
        if not self.generate_function:
            logging.error("❌ Vue.js ジェネレーター関数が見つかりません")
            return False
        
        try:
            # トピック指定がある場合は環境変数に設定
            if topic:
                import os
                os.environ["SINGLE_TOPIC"] = topic
            
            # 既存の関数を呼び出し
            result = self.generate_function()
            
            # 環境変数をクリア
            if topic and "SINGLE_TOPIC" in os.environ:
                del os.environ["SINGLE_TOPIC"]
            
            return result is not False
            
        except Exception as e:
            logging.error(f"❌ Vue.js記事生成エラー: {e}")
            return False


class SQLGenerator(BaseGeneratorAdapter):
    """SQL ジェネレーターアダプター（将来実装予定）"""
    
    def __init__(self):
        super().__init__("SQL")
    
    def generate_article(self, topic: Optional[str] = None) -> bool:
        """SQL記事生成（未実装）"""
        logging.warning("⚠️ SQL記事生成機能は現在開発中です")
        return False


# ジェネレーター取得関数
def get_generator(technology: str) -> BaseGeneratorAdapter:
    """
    指定された技術のジェネレーターを取得
    
    Args:
        technology (str): 技術名
        
    Returns:
        BaseGeneratorAdapter: ジェネレーターインスタンス
    """
    generators = {
        'wordpress': WordPressGenerator,
        'javascript': JavaScriptGenerator,
        'python': PythonGenerator,
        'react': ReactGenerator,
        'vue': VueGenerator,
        'sql': SQLGenerator
    }
    
    if technology not in generators:
        raise ValueError(f"未対応の技術: {technology}")
    
    return generators[technology]()


if __name__ == "__main__":
    # テスト実行
    print("🧪 Generator Adapters テスト")
    print("=" * 40)
    
    # WordPress テスト
    try:
        wp_gen = WordPressGenerator()
        print(f"✅ WordPress アダプター初期化成功")
    except Exception as e:
        print(f"❌ WordPress アダプターエラー: {e}")
    
    # JavaScript テスト
    try:
        js_gen = JavaScriptGenerator()
        print(f"✅ JavaScript アダプター初期化成功")
    except Exception as e:
        print(f"❌ JavaScript アダプターエラー: {e}")
    
    print("\n✅ アダプターテスト完了")