#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import time
from typing import Dict, List
from datetime import datetime

# 各技術スタック用の記事生成関数をインポート
from generate_articles import generate_and_post  # WordPress版
from generate_js_articles import generate_and_post_js  # JavaScript版
from generate_python_articles import generate_and_post_python  # Python版
from generate_react_articles import generate_and_post_react  # React版
from generate_vue_articles import generate_and_post_vue  # Vue.js版

# 技術スタック設定
TECH_STACKS = {
    "wordpress": {
        "name": "WordPress",
        "category_id": 2,
        "generator_func": generate_and_post,
        "topics": [
            "get_posts() でカスタム投稿を取得する方法",
            "WP REST API から特定ユーザーの投稿をフェッチする",
            "add_shortcode() でオリジナルショートコードを作成する",
            "wp_enqueue_script() で JS を読み込むベストプラクティス",
            "カスタム投稿タイプでメタボックスを追加する方法",
            "WordPress カスタムフィールドを効率的に活用する方法",
            "WooCommerce の商品データを REST API で操作する",
            "WordPressプラグイン開発でのセキュリティ対策",
        ]
    },
    "javascript": {
        "name": "JavaScript",
        "category_id": 6,
        "generator_func": generate_and_post_js,
        "topics": [
            "async/await を使った非同期処理のベストプラクティス",
            "React Hooks useEffect の正しい使い方と依存配列",
            "TypeScript の型定義でAPIレスポンスを安全に扱う方法",
            "JavaScript ES6+ の分割代入（Destructuring）活用術",
            "Node.js Express でミドルウェアを自作する方法",
            "Vite + React + TypeScript で最速開発環境を構築する方法 2025",
            "JavaScript の Optional Chaining と Nullish Coalescing 完全活用ガイド",
            "Web Components を TypeScript で作成する実践的な開発手法",
        ]
    },
    "python": {
        "name": "Python",
        "category_id": 7,
        "generator_func": generate_and_post_python,  # ✅ 実装済み
        "topics": [
            "FastAPI でREST APIを構築する基本パターン",
            "Pandas で大量データを効率的に処理する方法",
            "Django ORM でN+1問題を回避するクエリ最適化",
            "Pythonでスクレイピング：BeautifulSoupとSelenium使い分け",
            "pytest を使った効果的なテスト駆動開発",
            "Python 3.12+ の新機能と型ヒント活用法",
            "Pydantic v2 でデータバリデーションとシリアライゼーション",
            "FastAPI + SQLAlchemy 2.0 で非同期データベース操作",
        ]
    },
    "react": {
        "name": "React",
        "category_id": 8,
        "generator_func": generate_and_post_react,  # ✅ 実装済み
        "topics": [
            "React Server Components の基本概念と使い方",
            "useContext と useReducer でグローバル状態管理",
            "React.memo と useMemo でパフォーマンス最適化",
            "Custom Hooks で再利用可能なロジックを作成する方法",
            "React Router v6 でネストしたルーティングを実装",
            "React 18.3+ の concurrent features 完全活用ガイド",
            "Next.js 14 App Router と React Server Components 実践",
            "Zustand を使った軽量でシンプルな状態管理",
        ]
    },
    "vue": {
        "name": "Vue.js",
        "category_id": 9,
        "generator_func": generate_and_post_vue,  # ✅ 実装済み
        "topics": [
            "Vue 3 Composition API でカスタムフックを作成する方法",
            "Pinia で型安全な状態管理を実装する",
            "Nuxt 3 でSSR・SSGの使い分けとパフォーマンス最適化",
            "Vue Router 4 でルートガードとナビゲーション制御",
            "Vue 3 + TypeScript でコンポーネント設計のベストプラクティス",
            "Vue 3.4+ の最新機能と defineModel マクロ活用法",
            "Nuxt 3.10+ の Server Components とサーバーサイドレンダリング",
            "VueUse を活用した再利用可能なComposition関数集",
        ]
    }
}

class MultiTechGenerator:
    """マルチテック記事生成システム"""
    
    def __init__(self):
        self.tech_stacks = TECH_STACKS
        
    def generate_daily_content(self, distribution: Dict[str, int] = None):
        """
        日次コンテンツ生成（技術ごとの記事数を指定）
        
        Args:
            distribution: {"wordpress": 2, "javascript": 2, "python": 1} のような指定
        """
        if distribution is None:
            # デフォルト配分：1日5記事
            distribution = {
                "wordpress": 1,
                "javascript": 1,
                "python": 1,
                "react": 1,
                "vue": 1
            }
        
        logging.info(f"🚀 マルチテック記事生成開始: {distribution}")
        
        total_success = 0
        total_failed = 0
        
        for tech, count in distribution.items():
            if tech not in self.tech_stacks:
                logging.warning(f"⚠️  未対応技術: {tech}")
                continue
                
            stack_info = self.tech_stacks[tech]
            generator_func = stack_info["generator_func"]
            
            if not generator_func:
                logging.warning(f"⚠️  {stack_info['name']} の生成機能は未実装です")
                continue
            
            logging.info(f"📝 {stack_info['name']} 記事を {count} 件生成中...")
            
            # 重複チェック付きトピック選択
            from duplicate_checker import filter_duplicate_topics
            available_topics = filter_duplicate_topics(stack_info["topics"])
            
            # 必要数だけトピックを選択
            selected_topics = available_topics[:count]
            
            if len(selected_topics) < count:
                logging.warning(f"⚠️  {stack_info['name']}: 利用可能トピック不足 ({len(selected_topics)}/{count})")
            
            # 記事生成実行
            for i, topic in enumerate(selected_topics):
                logging.info(f"▶ {stack_info['name']} [{i+1}/{len(selected_topics)}]: {topic}")
                
                # カテゴリIDを環境変数に設定
                os.environ["CATEGORY_ID"] = str(stack_info["category_id"])
                
                try:
                    if generator_func(topic):
                        total_success += 1
                        logging.info(f"✅ {stack_info['name']} 記事生成成功")
                    else:
                        total_failed += 1
                        logging.error(f"❌ {stack_info['name']} 記事生成失敗")
                except Exception as e:
                    total_failed += 1
                    logging.error(f"❌ {stack_info['name']} 記事生成エラー: {e}")
                
                # レート制限対策
                if i < len(selected_topics) - 1:
                    logging.info("⏳ 3秒待機中...")
                    time.sleep(3)
        
        logging.info("=" * 60)
        logging.info(f"🎉 マルチテック記事生成完了!")
        logging.info(f"✅ 総成功: {total_success} 件")
        logging.info(f"❌ 総失敗: {total_failed} 件")
        
        return {
            "success": total_success,
            "failed": total_failed,
            "distribution": distribution
        }
    
    def generate_weekly_schedule(self):
        """週間スケジュール実行"""
        weekly_plan = {
            "monday": {"wordpress": 2, "javascript": 2, "python": 1},
            "tuesday": {"react": 2, "vue": 1, "javascript": 1},
            "wednesday": {"python": 2, "wordpress": 2},
            "thursday": {"javascript": 2, "react": 1, "vue": 1},
            "friday": {"wordpress": 1, "python": 1, "react": 1, "vue": 1},
            "saturday": {"javascript": 1, "react": 1, "vue": 1},
            "sunday": {"wordpress": 1, "python": 1}  # 軽めの日
        }
        
        today = datetime.now().strftime("%A").lower()
        
        if today in weekly_plan:
            logging.info(f"📅 {today.capitalize()} の記事生成を実行")
            return self.generate_daily_content(weekly_plan[today])
        else:
            logging.info("📅 今日は記事生成の予定はありません")
            return {"success": 0, "failed": 0, "distribution": {}}

    def generate_tech_focus(self, tech: str, count: int = 3):
        """
        特定技術に集中した記事生成
        
        Args:
            tech: 技術名 ('javascript', 'python', 'react', 'vue', 'wordpress')
            count: 生成する記事数
        """
        if tech not in self.tech_stacks:
            logging.error(f"❌ 未対応技術: {tech}")
            return {"success": 0, "failed": 1, "distribution": {}}
        
        distribution = {tech: count}
        logging.info(f"🎯 {tech.upper()} 集中記事生成: {count}件")
        
        return self.generate_daily_content(distribution)

    def show_available_topics(self):
        """利用可能なトピック一覧を表示"""
        from duplicate_checker import filter_duplicate_topics
        
        logging.info("📋 利用可能なトピック一覧:")
        logging.info("=" * 60)
        
        for tech, stack_info in self.tech_stacks.items():
            available_topics = filter_duplicate_topics(stack_info["topics"])
            logging.info(f"\n🔧 {stack_info['name']} ({len(available_topics)} 件利用可能):")
            for i, topic in enumerate(available_topics, 1):
                logging.info(f"   {i}. {topic}")
        
        logging.info("=" * 60)

def main():
    """メイン実行"""
    import sys
    
    generator = MultiTechGenerator()
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        
        if mode == "--weekly":
            # 週間スケジュール実行
            result = generator.generate_weekly_schedule()
        elif mode == "--custom":
            # カスタム配分実行
            # 例: python3 generate_multi_tech.py --custom wordpress:3,javascript:2
            if len(sys.argv) > 2:
                custom_dist = {}
                for item in sys.argv[2].split(","):
                    tech, count = item.split(":")
                    custom_dist[tech] = int(count)
                result = generator.generate_daily_content(custom_dist)
            else:
                logging.error("カスタム配分の指定が必要です")
                logging.info("使用例: python3 generate_multi_tech.py --custom wordpress:2,python:1")
                sys.exit(1)
        elif mode == "--focus":
            # 特定技術集中実行
            # 例: python3 generate_multi_tech.py --focus python 3
            if len(sys.argv) > 3:
                tech = sys.argv[2]
                count = int(sys.argv[3])
                result = generator.generate_tech_focus(tech, count)
            else:
                logging.error("技術名と件数の指定が必要です")
                logging.info("使用例: python3 generate_multi_tech.py --focus python 3")
                sys.exit(1)
        elif mode == "--topics":
            # 利用可能トピック表示
            generator.show_available_topics()
            sys.exit(0)
        elif mode == "--help":
            print("🚀 マルチテック記事生成システム")
            print("=" * 40)
            print("使用方法:")
            print("  python3 generate_multi_tech.py                     # デフォルト実行（各技術1件ずつ）")
            print("  python3 generate_multi_tech.py --weekly            # 週間スケジュール実行")
            print("  python3 generate_multi_tech.py --custom wordpress:2,python:1  # カスタム配分")
            print("  python3 generate_multi_tech.py --focus python 3    # 特定技術集中（Python 3件）")
            print("  python3 generate_multi_tech.py --topics            # 利用可能トピック表示")
            print("  python3 generate_multi_tech.py --help              # このヘルプ")
            print("\n対応技術: wordpress, javascript, python, react, vue")
            sys.exit(0)
        else:
            logging.error(f"未知のモード: {mode}")
            logging.info("--help でヘルプを表示")
            sys.exit(1)
    else:
        # デフォルト実行
        result = generator.generate_daily_content()
    
    # 実行結果に応じた終了コード
    sys.exit(0 if result["failed"] == 0 else 1)

if __name__ == "__main__":
    main()