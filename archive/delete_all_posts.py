#!/usr/bin/env python3
import requests
import time
import logging

# 設定を外部ファイルから読み込み
try:
    from config import config
except ImportError:
    logging.error("❌ config.py が見つかりません")
    logging.error("   config.py ファイルを作成してください")
    exit(1)

#――――――――――――――――――――――
# 削除設定
#――――――――――――――――――――――
PER_PAGE = 100        # 1 ページあたり取得件数（最大100）
SLEEP_SEC = 0.5       # 削除ごとのインターバル（過負荷防止）
TIMEOUT = 10          # HTTP リクエストタイムアウト

def fetch_post_ids(page: int):
    """
    per_page 件ずつ、投稿ID一覧を取得
    :param page: ページ番号（1 から）
    :return: ID のリスト
    """
    url = f"{config.wp_site_url}/wp-json/wp/v2/posts"
    params = {
        "per_page": PER_PAGE,
        "page":     page,
        "status":   "publish,draft",   # 公開・下書き両方を対象
    }
    
    try:
        r = requests.get(url, headers=config.get_auth_header(), params=params, timeout=TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            logging.info(f"ページ {page}: {len(data)} 件取得")
            return [post["id"] for post in data]
        elif r.status_code == 400:
            # ページ数オーバーなどで「空配列」返ってくる場合あり
            logging.info(f"ページ {page}: データなし")
            return []
        else:
            logging.error(f"投稿取得エラー page={page} → HTTP {r.status_code}")
            logging.error(f"レスポンス: {r.text}")
            return []
    except Exception as e:
        logging.error(f"投稿取得例外 page={page}: {e}")
        return []

def delete_post(post_id: int):
    """
    force=true で投稿を完全削除
    """
    url = f"{config.wp_site_url}/wp-json/wp/v2/posts/{post_id}"
    params = {"force": "true"}
    
    try:
        r = requests.delete(url, headers=config.get_auth_header(), params=params, timeout=TIMEOUT)
        if r.status_code in (200, 204):
            logging.info(f"✅ 削除成功 ID={post_id}")
            return True
        else:
            logging.error(f"❌ 削除失敗 ID={post_id} → HTTP {r.status_code}")
            logging.error(f"レスポンス: {r.text}")
            return False
    except Exception as e:
        logging.error(f"❌ 削除例外 ID={post_id}: {e}")
        return False

def confirm_deletion():
    """
    削除実行前の確認
    """
    logging.warning("⚠️  この操作により、すべての投稿が完全に削除されます！")
    logging.warning("   バックアップを取っていることを確認してください。")
    
    try:
        response = input("\n本当に削除を実行しますか？ (yes/no): ").strip().lower()
        return response in ['yes', 'y']
    except KeyboardInterrupt:
        logging.info("\n操作がキャンセルされました")
        return False

def main():
    logging.info("🗑️  WordPress投稿一括削除スクリプト")
    logging.info(f"🌐 対象サイト: {config.wp_site_url}")
    logging.info(f"👤 実行ユーザー: {config.wp_user}")
    
    # 削除前の確認
    if not confirm_deletion():
        logging.info("削除処理をキャンセルしました")
        return
    
    page = 1
    total_deleted = 0
    total_failed = 0

    logging.info("削除処理を開始します...")
    
    while True:
        logging.info(f"--- ページ {page} 処理中 ---")
        ids = fetch_post_ids(page)
        
        if not ids:
            logging.info("取得できる投稿がありません。処理完了。")
            break

        for pid in ids:
            if delete_post(pid):
                total_deleted += 1
            else:
                total_failed += 1
            time.sleep(SLEEP_SEC)

        page += 1

    logging.info("=" * 50)
    logging.info(f"🎉 削除処理完了")
    logging.info(f"✅ 削除成功: {total_deleted} 件")
    
    if total_failed > 0:
        logging.warning(f"❌ 削除失敗: {total_failed} 件")
    
    logging.info("WordPress管理画面で結果を確認してください。")

if __name__ == "__main__":
    main()