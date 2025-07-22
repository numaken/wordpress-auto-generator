#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下書き記事一括公開スクリプト (bulk_publish_drafts.py)
下書き状態の記事を一括で公開状態に変更
"""

import requests
import time
import logging
from datetime import datetime, timedelta

# 設定を外部ファイルから読み込み
try:
    from core.config import config
except ImportError:
    logging.error("❌ config.py が見つかりません")
    exit(1)

def get_draft_posts(category_id=None, hours_ago=24):
    """
    下書き状態の記事を取得
    
    Args:
        category_id: 特定カテゴリのみ（Noneで全カテゴリ）
        hours_ago: 何時間前以降の記事を対象にするか
    
    Returns:
        list: 下書き記事のリスト
    """
    draft_posts = []
    page = 1
    
    # 指定時間前の日時を計算
    since_time = datetime.now() - timedelta(hours=hours_ago)
    since_iso = since_time.strftime("%Y-%m-%dT%H:%M:%S")
    
    logging.info(f"🔍 下書き記事を検索中... ({since_iso} 以降)")
    
    while True:
        url = f"{config.wp_site_url}/wp-json/wp/v2/posts"
        params = {
            "status": "draft",
            "per_page": 100,
            "page": page,
            "after": since_iso,  # 指定時間以降の記事のみ
            "orderby": "date",
            "order": "desc"
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
                logging.error(f"記事取得エラー: HTTP {response.status_code}")
                break
            
            posts = response.json()
            if not posts:
                break
            
            for post in posts:
                draft_posts.append({
                    "id": post["id"],
                    "title": post["title"]["rendered"],
                    "date": post["date"],
                    "categories": post["categories"],
                    "tags": post["tags"]
                })
            
            logging.info(f"ページ {page}: {len(posts)} 件の下書きを発見")
            page += 1
            
        except Exception as e:
            logging.error(f"記事取得エラー (page {page}): {e}")
            break
    
    logging.info(f"✅ 合計 {len(draft_posts)} 件の下書き記事を発見")
    return draft_posts

def publish_post(post_id, title):
    """
    指定された記事を公開状態に変更
    
    Args:
        post_id: 記事ID
        title: 記事タイトル（ログ用）
    
    Returns:
        bool: 成功時True
    """
    url = f"{config.wp_site_url}/wp-json/wp/v2/posts/{post_id}"
    
    update_data = {
        "status": "publish"
    }
    
    try:
        response = requests.post(
            url,
            headers=config.get_auth_header(),
            json=update_data,
            timeout=30
        )
        
        if response.status_code in (200, 201):
            logging.info(f"✅ 公開成功: {title}")
            return True
        else:
            logging.error(f"❌ 公開失敗 (ID: {post_id}): HTTP {response.status_code}")
            logging.error(f"レスポンス: {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"❌ 公開エラー (ID: {post_id}): {e}")
        return False

def bulk_publish_drafts(category_id=None, hours_ago=24, dry_run=True):
    """
    下書き記事を一括公開
    
    Args:
        category_id: 対象カテゴリID（Noneで全カテゴリ）
        hours_ago: 何時間前以降の記事を対象にするか
        dry_run: Trueの場合は実際の更新を行わない
    """
    logging.info("🚀 下書き記事一括公開ツール開始")
    logging.info("=" * 50)
    
    if dry_run:
        logging.warning("⚠️  DRY RUN モード: 実際の公開は行いません")
    
    # 下書き記事を取得
    draft_posts = get_draft_posts(category_id, hours_ago)
    
    if not draft_posts:
        logging.info("下書き記事が見つかりませんでした")
        return {"published": 0, "failed": 0}
    
    # 確認表示
    logging.info(f"📝 公開対象記事:")
    for i, post in enumerate(draft_posts[:10], 1):  # 最初の10件を表示
        logging.info(f"   {i}. {post['title']} (ID: {post['id']})")
    
    if len(draft_posts) > 10:
        logging.info(f"   ... 他 {len(draft_posts) - 10} 件")
    
    # 実行確認
    if not dry_run:
        logging.warning(f"⚠️  {len(draft_posts)} 件の記事を公開します")
        try:
            response = input("続行しますか？ (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                logging.info("処理をキャンセルしました")
                return {"published": 0, "failed": 0}
        except KeyboardInterrupt:
            logging.info("\n処理をキャンセルしました")
            return {"published": 0, "failed": 0}
    
    # 一括公開実行
    published_count = 0
    failed_count = 0
    
    logging.info("▶ 一括公開処理開始...")
    
    for i, post in enumerate(draft_posts, 1):
        logging.info(f"[{i}/{len(draft_posts)}] 処理中: {post['title']}")
        
        if dry_run:
            logging.info(f"   DRY RUN: 公開予定")
            published_count += 1
        else:
            if publish_post(post["id"], post["title"]):
                published_count += 1
            else:
                failed_count += 1
            
            # レート制限対策
            time.sleep(1)
    
    # 結果サマリー
    logging.info("=" * 50)
    logging.info(f"🎉 一括公開処理完了!")
    logging.info(f"✅ 公開{'予定' if dry_run else '成功'}: {published_count} 件")
    
    if not dry_run and failed_count > 0:
        logging.warning(f"❌ 公開失敗: {failed_count} 件")
    
    if dry_run:
        logging.info("💡 実際に公開する場合は --run オプションで実行してください")
    else:
        logging.info("🌐 サイトで記事が公開されていることを確認してください")
    
    return {"published": published_count, "failed": failed_count}

def main():
    """メイン実行"""
    import sys
    
    # デフォルト設定
    category_id = None
    hours_ago = 24
    dry_run = True
    
    # 引数解析
    if len(sys.argv) > 1:
        if "--run" in sys.argv:
            dry_run = False
        if "--all-time" in sys.argv:
            hours_ago = 24 * 365  # 1年前まで
        if "--category" in sys.argv:
            try:
                idx = sys.argv.index("--category")
                category_id = int(sys.argv[idx + 1])
            except (ValueError, IndexError):
                logging.error("--category の後に数値を指定してください")
                sys.exit(1)
        if "--hours" in sys.argv:
            try:
                idx = sys.argv.index("--hours")
                hours_ago = int(sys.argv[idx + 1])
            except (ValueError, IndexError):
                logging.error("--hours の後に数値を指定してください")
                sys.exit(1)
    
    # ヘルプ表示
    if "--help" in sys.argv:
        print("📝 下書き記事一括公開ツール")
        print("=" * 40)
        print("使用方法:")
        print("  python3 bulk_publish_drafts.py                    # 確認のみ（過去24時間）")
        print("  python3 bulk_publish_drafts.py --run              # 実際に公開実行")
        print("  python3 bulk_publish_drafts.py --category 2       # カテゴリ2のみ")
        print("  python3 bulk_publish_drafts.py --hours 6          # 過去6時間の記事のみ")
        print("  python3 bulk_publish_drafts.py --all-time         # 全期間")
        print("  python3 bulk_publish_drafts.py --run --all-time   # 全期間を実際に公開")
        print("\nオプション:")
        print("  --run        実際に公開実行（指定なしは確認のみ）")
        print("  --category N 特定カテゴリのみ対象")
        print("  --hours N    過去N時間の記事のみ対象")
        print("  --all-time   全期間の下書きを対象")
        print("  --help       このヘルプを表示")
        sys.exit(0)
    
    # 設定表示
    logging.info(f"🎯 実行設定:")
    logging.info(f"   対象カテゴリ: {category_id if category_id else '全カテゴリ'}")
    logging.info(f"   対象期間: 過去{hours_ago}時間")
    logging.info(f"   実行モード: {'本番実行' if not dry_run else '確認のみ'}")
    
    # 実行
    result = bulk_publish_drafts(category_id, hours_ago, dry_run)
    
    # 終了コード
    sys.exit(0 if result["failed"] == 0 else 1)

if __name__ == "__main__":
    main()