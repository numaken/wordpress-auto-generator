#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
import time
import sys
import html
import logging

# 設定を外部ファイルから読み込み
try:
    from core.config import config
except ImportError:
    logging.error("❌ config.py が見つかりません")
    logging.error("   config.py ファイルを作成してください")
    sys.exit(1)

# 重複チェックモジュールをインポート
try:
    from core.duplicate_checker import check_single_topic, filter_duplicate_topics
except ImportError:
    logging.error("❌ duplicate_checker.py が見つかりません")
    logging.error("   duplicate_checker.py ファイルを作成してください")
    sys.exit(1)

# 単一トピック処理用（wrapper.pyから環境変数で受け取る）
SINGLE_TOPIC = os.getenv('SINGLE_TOPIC')
CATEGORY_ID = int(os.getenv('CATEGORY_ID', config.category_id))

#――――――――――――――――――――――
# デフォルトトピック一覧（SINGLE_TOPICが未設定の場合のフォールバック）
#――――――――――――――――――――――
default_topics = [
    "get_posts() でカスタム投稿を取得する方法",
    "WP REST API から特定ユーザーの投稿をフェッチする",
    "add_shortcode() でオリジナルショートコードを作成する",
    "wp_enqueue_script() で JS を読み込むベストプラクティス",
    "テーマのヘッダー内にメタタグを自動出力する関数",
    "WordPressでAPIキー管理を安全に行う方法 2025年版",
    "カスタムフィールドをJSONで一括エクスポート・インポートする機能",
    "WordPress管理画面にダークモード切替を実装する方法",
]

def md2html(md: str) -> str:
    """
    Markdown → HTML 変換関数
    - 見出し (#, ##, ###) を <h1>〜<h3> に
    - リスト (- ) を <ul><li> に
    - ```php``` コードブロックを <pre><code> に
    - 通常テキストを <p> に変換
    """
    html_lines = []
    lines = md.split('\n')
    in_code = False
    in_list = False

    for line in lines:
        # コードブロック開始
        if line.startswith("```php"):
            html_lines.append('<pre class="language-php line-numbers" data-line="2-3"><code class="language-php">')
            in_code = True
            continue
        # コードブロック終了
        if in_code and line.strip() == "```":
            html_lines.append('</code></pre>')
            in_code = False
            continue
        # コード内部
        if in_code:
            html_lines.append(html.escape(line))
            continue

        # 見出し
        if line.startswith("### "):
            html_lines.append(f'<h3>{html.escape(line[4:].strip())}</h3>')
            continue
        if line.startswith("## "):
            html_lines.append(f'<h2>{html.escape(line[3:].strip())}</h2>')
            continue
        if line.startswith("# "):
            html_lines.append(f'<h1>{html.escape(line[2:].strip())}</h1>')
            continue

        # リスト項目
        if line.strip().startswith("- "):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            html_lines.append(f'<li>{html.escape(line.strip()[2:].strip())}</li>')
            continue
        # リスト終了
        if in_list:
            html_lines.append('</ul>')
            in_list = False

        # 空行
        if not line.strip():
            html_lines.append('<p></p>')
            continue

        # 通常テキスト
        html_lines.append(f'<p>{html.escape(line)}</p>')

    # リストが閉じていなければ閉じる
    if in_list:
        html_lines.append('</ul>')

    return "\n".join(html_lines)

def generate_article_content(topic: str) -> str:
    """
    OpenAI API を使って記事コンテンツを生成
    """
    system_content = "あなたはWordPressエンジニア向けの実務ナレッジ記事作成アシスタントです。"
    user_content = f"""
以下のフォーマットで日本語記事を生成してください。  
トピック: {topic}

---
# 概要  
- ユースケース（なぜこのスニペットが必要か）  
- 前提条件（必要なプラグインや設定）

## サンプルコード  
```php  
# ここに完全版の PHP コードを載せてください  
```  

## 解説  
- 各コード行／セクションのポイントを箇条書きで説明  

## ベストプラクティス  
- 運用上の注意点や拡張例  
---

上記フォーマットに従い、可能な限り具体的に出力してください。  
"""

    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ],
        "max_tokens": 2000,
        "temperature": 0.7
    }

    try:
        # OpenAI API 呼び出し
        res = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=config.get_openai_headers(),
            json=payload,
            timeout=60
        )

        logging.info(f"OpenAI API HTTPステータス: {res.status_code}")

        if res.status_code != 200:
            logging.error(f"OpenAI API エラー ({res.status_code}): {res.text}")
            return None

        data = res.json()
        
        if "choices" not in data:
            logging.error("API レスポンスに choices が含まれていません")
            logging.error(json.dumps(data, ensure_ascii=False, indent=2))
            return None

        raw_content = data["choices"][0]["message"]["content"].strip()
        return raw_content
        
    except requests.exceptions.Timeout:
        logging.error("OpenAI API タイムアウトエラー")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"OpenAI API リクエストエラー: {e}")
        return None
    except Exception as e:
        logging.error(f"OpenAI API 予期しないエラー: {e}")
        return None

# generate_articles.py の修正版（追加する部分のみ）

def get_or_create_tag_id(tag_name: str) -> int:
    """
    タグ名からタグIDを取得、存在しなければ作成
    """
    try:
        # 既存タグを検索
        response = requests.get(
            f"{config.wp_site_url}/wp-json/wp/v2/tags",
            headers=config.get_auth_header(),
            params={"search": tag_name},
            timeout=30
        )
        
        if response.status_code == 200:
            tags = response.json()
            for tag in tags:
                if tag["name"] == tag_name:
                    logging.debug(f"既存タグ見つかりました: {tag_name} (ID: {tag['id']})")
                    return tag["id"]
        
        # タグが存在しない場合は作成
        logging.info(f"新しいタグを作成中: {tag_name}")
        create_response = requests.post(
            f"{config.wp_site_url}/wp-json/wp/v2/tags",
            headers=config.get_auth_header(),
            json={"name": tag_name},
            timeout=30
        )
        
        if create_response.status_code in (200, 201):
            new_tag = create_response.json()
            logging.info(f"✅ タグ作成成功: {tag_name} (ID: {new_tag['id']})")
            return new_tag["id"]
        else:
            logging.error(f"❌ タグ作成失敗: {tag_name} - ステータス: {create_response.status_code}")
        
    except Exception as e:
        logging.error(f"❌ タグ処理エラー ({tag_name}): {e}")
    
    return None

def get_tag_ids(tag_names: list) -> list:
    """
    タグ名のリストからタグIDのリストを取得
    """
    if not tag_names:
        return []
    
    tag_ids = []
    logging.info(f"🏷️  タグID取得開始: {len(tag_names)}個のタグを処理")
    
    for tag_name in tag_names:
        tag_id = get_or_create_tag_id(tag_name)
        if tag_id:
            tag_ids.append(tag_id)
    
    logging.info(f"🎯 タグID変換完了: {len(tag_names)}個中{len(tag_ids)}個成功")
    return tag_ids

# generate_articles.py の修正箇所

def post_to_wordpress(title: str, content: str, category_id: int, status: str = None) -> bool:
    """
    WordPress REST API 経由で記事を投稿
    """
    # 🆕 ステータスが指定されていない場合は設定から取得
    if status is None:
        status = config.post_status
    
    # WordPress/PHP用のタグを取得
    tag_names = ["WordPress", "PHP", "開発", "プログラミング"]
    tag_ids = get_tag_ids(tag_names)
    
    post_data = {
        "title": title,
        "content": content,
        "status": status,  # 🆕 設定値を使用
        "categories": [category_id],
        "tags": tag_ids,
    }
    
    try:
        post_res = requests.post(
            f"{config.wp_site_url}/wp-json/wp/v2/posts",
            headers=config.get_auth_header(),
            data=json.dumps(post_data),
            timeout=30
        )
        
        if post_res.status_code in (200, 201):
            status_text = "下書き保存" if status == "draft" else "公開" if status == "publish" else f"ステータス: {status}"
            logging.info(f"✅ {status_text}成功: {title}")
            return True
        else:
            logging.error(f"❌ 投稿失敗 ({post_res.status_code}):")
            logging.error(post_res.text)
            return False
            
    except requests.exceptions.Timeout:
        logging.error("❌ WordPress API タイムアウトエラー")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ WordPress API リクエストエラー: {e}")
        return False
    except Exception as e:
        logging.error(f"❌ WordPress API 予期しないエラー: {e}")
        return False

def generate_and_post(topic: str) -> bool:
    """
    # 🆕 ステータスが指定されていない場合は設定から取得
    if status is None:
        status = config.post_status
    
    # 🆕 ステータスが指定されていない場合は設定から取得
    if status is None:
        status = config.post_status
    
    # 🆕 ステータスが指定されていない場合は設定から取得
    if status is None:
        status = config.post_status
    
    # 🆕 ステータスが指定されていない場合は設定から取得
    if status is None:
        status = config.post_status
    
    # 🆕 ステータスが指定されていない場合は設定から取得
    if status is None:
        status = config.post_status
    
    # 🆕 ステータスが指定されていない場合は設定から取得
    if status is None:
        status = config.post_status
    
    1) OpenAI に記事生成をリクエスト
    2) Markdown → HTML に変換
    3) WP REST API 経由で投稿
    """
    logging.info(f"▶ 記事生成開始: {topic}")

    # 1. OpenAI API で記事コンテンツを生成
    raw_content = generate_article_content(topic)
    if not raw_content:
        logging.error(f"❌ 記事生成失敗: {topic}")
        return False

    # 2. Markdown → HTML 変換
    html_content = md2html(raw_content)

    # 3. WordPressに投稿（🆕 ステータスを省略して設定値を使用）
    success = post_to_wordpress(topic, html_content, CATEGORY_ID)
    
    if success:
        logging.info(f"✅ 処理完了: {topic}")
    else:
        logging.error(f"❌ 処理失敗: {topic}")
    
    return success

def main():
    logging.info("🎯 WordPress記事生成スクリプト開始")
    
    # 単一トピック処理（wrapper.pyから呼び出される場合）
    if SINGLE_TOPIC:
        logging.info(f"📝 単一トピック処理: {SINGLE_TOPIC}")
        logging.info(f"📁 カテゴリID: {CATEGORY_ID}")
        
        # 🔍 重複チェック実行
        if not check_single_topic(SINGLE_TOPIC):
            logging.error("❌ 重複により処理をスキップしました")
            sys.exit(1)
        
        success = generate_and_post(SINGLE_TOPIC)
        
        if success:
            logging.info("✅ 処理完了: 成功")
            sys.exit(0)
        else:
            logging.error("❌ 処理完了: 失敗")
            sys.exit(1)
    
    # フォールバック処理（単体実行の場合）
    else:
        logging.info("🧪 フォールバックモード: デフォルトトピックで処理")
        logging.info(f"📊 処理予定: {len(default_topics)}個のトピック")
        
        # 🔍 重複チェック実行
        logging.info("🔍 既存記事との重複チェックを実行中...")
        unique_topics = filter_duplicate_topics(default_topics)
        
        if not unique_topics:
            logging.warning("⚠️  重複チェック後、処理可能なトピックがありません")
            logging.info("すべてのデフォルトトピックが既存記事と重複しています")
            return
        
        if len(unique_topics) < len(default_topics):
            logging.info(f"📋 処理対象を絞り込み: {len(default_topics)} → {len(unique_topics)} 件")
        
        logging.info("=" * 50)
        
        success_count = 0
        failed_count = 0
        
        for i, topic in enumerate(unique_topics):
            logging.info(f"▶ [{i+1}/{len(unique_topics)}] 処理中...")
            
            if generate_and_post(topic):
                success_count += 1
            else:
                failed_count += 1
            
            # 最後の記事以外は待機
            if i < len(unique_topics) - 1:
                logging.info("⏳ 5秒待機中...")
                time.sleep(5)
        
        logging.info("=" * 50)
        logging.info(f"🎉 処理完了!")
        logging.info(f"✅ 成功: {success_count}件")
        logging.info(f"❌ 失敗: {failed_count}件")
        
        if len(default_topics) > len(unique_topics):
            skipped = len(default_topics) - len(unique_topics)
            logging.info(f"⚠️  重複スキップ: {skipped}件")
        
        logging.info("📝 記事は下書き状態で保存されました。WordPress管理画面で確認してください。")

if __name__ == "__main__":
    main()