#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging
import time
from typing import List, Dict

# 設定を外部ファイルから読み込み
try:
    from core.config import config
except ImportError:
    logging.error("❌ config.py が見つかりません")
    exit(1)

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
            logging.error(f"レスポンス: {create_response.text}")
        
    except Exception as e:
        logging.error(f"❌ タグ処理エラー ({tag_name}): {e}")
    
    return None

def get_tag_ids(tag_names: list) -> list:
    """
    タグ名のリストからタグIDのリストを取得
    """
    if not tag_names:
        logging.warning("⚠️  タグ名リストが空です")
        return []
    
    tag_ids = []
    logging.info(f"🏷️  タグID取得開始: {len(tag_names)}個のタグを処理")
    
    for i, tag_name in enumerate(tag_names, 1):
        logging.info(f"🔍 [{i}/{len(tag_names)}] タグ処理中: {tag_name}")
        tag_id = get_or_create_tag_id(tag_name)
        if tag_id:
            tag_ids.append(tag_id)
            logging.info(f"✅ タグID取得成功: {tag_name} → {tag_id}")
        else:
            logging.warning(f"⚠️  タグID取得失敗: {tag_name}")
    
    logging.info(f"🎯 タグID変換完了: {len(tag_names)}個中{len(tag_ids)}個成功")
    return tag_ids

def fetch_posts_without_tags(category_id: int = None) -> List[Dict]:
    """
    タグが設定されていない投稿を取得
    
    Args:
        category_id: 特定カテゴリのみ対象にする場合
    
    Returns:
        List[Dict]: タグなし投稿のリスト
    """
    posts_without_tags = []
    page = 1
    
    logging.info("🔍 タグなし投稿を検索中...")
    
    while True:
        url = f"{config.wp_site_url}/wp-json/wp/v2/posts"
        params = {
            "per_page": 100,
            "page": page,
            "status": "publish,draft",  # 公開・下書き両方
        }
        
        if category_id:
            params["categories"] = category_id
        
        try:
            response = requests.get(
                url,
                headers=config.get_auth_header(),
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                break
            
            posts = response.json()
            if not posts:
                break
            
            # タグが設定されていない投稿をフィルタ
            for post in posts:
                if not post.get("tags") or len(post.get("tags", [])) == 0:
                    posts_without_tags.append({
                        "id": post["id"],
                        "title": post["title"]["rendered"],
                        "status": post["status"],
                        "categories": post["categories"],
                        "content": post["content"]["rendered"][:200] + "..."  # プレビュー用
                    })
            
            logging.info(f"ページ {page}: {len(posts)} 件中 {len([p for p in posts if not p.get('tags')])} 件がタグなし")
            page += 1
            
        except Exception as e:
            logging.error(f"投稿取得エラー (page {page}): {e}")
            break
    
    logging.info(f"✅ タグなし投稿: {len(posts_without_tags)} 件発見")
    return posts_without_tags

def categorize_posts_by_content(posts: List[Dict]) -> Dict[str, List[Dict]]:
    """
    投稿内容に基づいてカテゴリ分けし、適切なタグを提案
    
    Args:
        posts: 投稿リスト
    
    Returns:
        Dict: カテゴリ別投稿リスト
    """
    categorized = {
        "javascript": [],
        "react": [],
        "wordpress": [],
        "python": [],
        "general": []
    }
    
    # キーワードベースの分類
    keywords = {
        "javascript": ["javascript", "js", "node.js", "npm", "async", "await", "promise", "typescript"],
        "react": ["react", "jsx", "component", "hooks", "usestate", "useeffect", "next.js"],
        "wordpress": ["wordpress", "wp", "php", "hook", "filter", "action", "get_posts", "wp_query"],
        "python": ["python", "django", "flask", "pandas", "numpy", "pip", "fastapi"]
    }
    
    for post in posts:
        content_lower = (post["title"] + " " + post["content"]).lower()
        category_found = False
        
        for category, words in keywords.items():
            if any(word in content_lower for word in words):
                categorized[category].append(post)
                category_found = True
                break
        
        if not category_found:
            categorized["general"].append(post)
    
    # 結果をログ出力
    for category, posts_list in categorized.items():
        if posts_list:
            logging.info(f"📁 {category.upper()}: {len(posts_list)} 件")
    
    return categorized

def get_tags_for_category(category: str) -> List[str]:
    """
    カテゴリに応じたタグリストを取得
    
    Args:
        category: カテゴリ名
    
    Returns:
        List[str]: タグ名のリスト
    """
    tag_mapping = {
        "javascript": ["JavaScript", "プログラミング", "Web開発", "フロントエンド"],
        "react": ["React", "JavaScript", "フロントエンド", "UI/UX"],
        "wordpress": ["WordPress", "PHP", "CMS", "開発"],
        "python": ["Python", "プログラミング", "データサイエンス", "バックエンド"],
        "general": ["プログラミング", "技術", "開発"]
    }
    
    return tag_mapping.get(category, tag_mapping["general"])

def update_post_tags(post_id: int, tag_ids: List[int]) -> bool:
    """
    投稿のタグを更新
    
    Args:
        post_id: 投稿ID
        tag_ids: タグIDのリスト
    
    Returns:
        bool: 成功時True
    """
    url = f"{config.wp_site_url}/wp-json/wp/v2/posts/{post_id}"
    
    update_data = {
        "tags": tag_ids
    }
    
    try:
        response = requests.post(  # またはPUTを使用
            url,
            headers=config.get_auth_header(),
            json=update_data,
            timeout=30
        )
        
        if response.status_code in (200, 201):
            return True
        else:
            logging.error(f"❌ 投稿更新失敗 (ID: {post_id}): {response.status_code}")
            logging.error(f"レスポンス: {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"❌ 投稿更新エラー (ID: {post_id}): {e}")
        return False

def bulk_update_tags(category_id: int = None, dry_run: bool = True):
    """
    既存投稿のタグを一括更新
    
    Args:
        category_id: 特定カテゴリのみ対象
        dry_run: True の場合は実際の更新を行わない（確認のみ）
    """
    logging.info("🚀 既存投稿タグ更新ツール開始")
    
    if dry_run:
        logging.warning("⚠️  DRY RUN モード: 実際の更新は行いません")
    
    # 1. タグなし投稿を取得
    posts_without_tags = fetch_posts_without_tags(category_id)
    
    if not posts_without_tags:
        logging.info("✅ タグなし投稿は見つかりませんでした")
        return
    
    # 2. 投稿をカテゴリ分け
    categorized_posts = categorize_posts_by_content(posts_without_tags)
    
    # 3. 各カテゴリの投稿にタグを追加
    total_updated = 0
    total_failed = 0
    
    for category, posts in categorized_posts.items():
        if not posts:
            continue
        
        logging.info(f"📝 {category.upper()} カテゴリの処理開始: {len(posts)} 件")
        
        # カテゴリに応じたタグを取得
        tag_names = get_tags_for_category(category)
        tag_ids = get_tag_ids(tag_names)
        
        if not tag_ids:
            logging.warning(f"⚠️  {category} のタグID取得に失敗しました")
            continue
        
        logging.info(f"🏷️  使用するタグ: {tag_names} → {tag_ids}")
        
        # 各投稿を更新
        for i, post in enumerate(posts, 1):
            logging.info(f"▶ [{i}/{len(posts)}] 更新中: {post['title']}")
            
            if dry_run:
                logging.info(f"   DRY RUN: タグ {tag_ids} を追加予定")
                total_updated += 1
            else:
                if update_post_tags(post["id"], tag_ids):
                    logging.info(f"✅ 更新成功: ID {post['id']}")
                    total_updated += 1
                else:
                    logging.error(f"❌ 更新失敗: ID {post['id']}")
                    total_failed += 1
                
                # レート制限対策
                time.sleep(1)
    
    # 4. 結果サマリー
    logging.info("=" * 50)
    logging.info(f"🎉 タグ更新処理完了!")
    logging.info(f"✅ 更新{'予定' if dry_run else '成功'}: {total_updated} 件")
    if not dry_run and total_failed > 0:
        logging.warning(f"❌ 更新失敗: {total_failed} 件")
    
    if dry_run:
        logging.info("💡 実際に更新する場合は dry_run=False で実行してください")

def interactive_mode():
    """
    対話的モードで実行
    """
    print("🏷️  WordPress 既存記事タグ更新ツール")
    print("=" * 50)
    
    # カテゴリ選択
    print("対象カテゴリを選択してください:")
    print("1. 全カテゴリ")
    print("2. WordPress記事のみ (ID: 2)")
    print("3. JavaScript記事のみ (ID: 6)")
    print("4. カスタム指定")
    
    choice = input("選択 (1-4): ").strip()
    
    category_id = None
    if choice == "2":
        category_id = 2
    elif choice == "3":
        category_id = 6
    elif choice == "4":
        category_id = int(input("カテゴリID: "))
    
    # 実行モード選択
    print("\n実行モードを選択してください:")
    print("1. 確認のみ (DRY RUN)")
    print("2. 実際に更新")
    
    mode_choice = input("選択 (1-2): ").strip()
    dry_run = mode_choice == "1"
    
    # 実行
    bulk_update_tags(category_id, dry_run)

def main():
    """メイン実行関数"""
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive":
            interactive_mode()
        elif sys.argv[1] == "--run":
            # 実際に更新実行
            bulk_update_tags(dry_run=False)
        elif sys.argv[1] == "--dry-run":
            # 確認のみ
            bulk_update_tags(dry_run=True)
        else:
            print("使用方法:")
            print("  python3 update_existing_tags.py --interactive  # 対話モード")
            print("  python3 update_existing_tags.py --dry-run     # 確認のみ")
            print("  python3 update_existing_tags.py --run         # 実際に更新")
    else:
        # デフォルトは確認のみ
        bulk_update_tags(dry_run=True)

if __name__ == "__main__":
    main()