#!/usr/bin/env python3
"""
重複チェック共通モジュール
すべてのスクリプトで既存記事との重複を防ぐ
"""

import requests
import logging
from typing import Set, List
from core.config import config

def fetch_existing_titles() -> Set[str]:
    """
    WordPress REST API で既存投稿のタイトルを全件取得
    公開記事・下書きの両方を対象とする（改善版）
    
    Returns:
        Set[str]: 既存記事タイトルのセット
    """
    titles = set()
    page = 1

    logging.info("既存記事タイトルを取得中...")
    
    while True:
        url = f"{config.wp_site_url}/wp-json/wp/v2/posts"
        params = {
            "categories": config.category_id,
            "per_page": 100,
            "page": page,
            "status": "publish,draft",  # 公開・下書き両方を含める
        }
        
        try:
            response = requests.get(
                url, 
                headers=config.get_auth_header(), 
                params=params, 
                timeout=10
            )
            
            # 400エラーは通常「ページが存在しない」ことを意味する
            if response.status_code == 400:
                logging.debug(f"ページ {page}: データなし（正常終了）")
                break
            elif response.status_code != 200:
                logging.error(f"既存記事取得エラー (page {page}): HTTP {response.status_code}")
                logging.error(f"レスポンス: {response.text}")
                break
                
            response.raise_for_status()
            
        except requests.exceptions.Timeout:
            logging.error(f"既存記事取得タイムアウト (page {page})")
            break
        except requests.exceptions.RequestException as e:
            logging.error(f"既存記事取得エラー (page {page}): {e}")
            break
        except Exception as e:
            logging.error(f"既存記事取得予期しないエラー (page {page}): {e}")
            break

        data = response.json()
        if not data:
            logging.debug(f"ページ {page}: データなし（正常終了）")
            break

        for post in data:
            title = post.get("title", {}).get("rendered", "").strip()
            if title:
                titles.add(title)

        logging.info(f"ページ {page}: {len(data)} 件取得")
        page += 1
        
        # 安全装置：100ページを超えたら停止
        if page > 100:
            logging.warning("100ページを超えたため取得を停止しました")
            break

    logging.info(f"✅ 合計 {len(titles)} 件の既存タイトルを取得完了")
    return titles

def is_duplicate_title(new_title: str, existing_titles: Set[str]) -> bool:
    """
    新しいタイトルが既存タイトルと重複するかチェック
    
    Args:
        new_title: チェック対象の新しいタイトル
        existing_titles: 既存タイトルのセット
        
    Returns:
        bool: 重複している場合True
    """
    new_clean = new_title.lower().strip()
    
    for existing in existing_titles:
        existing_clean = existing.lower().strip()
        
        # 完全一致チェック
        if new_clean == existing_clean:
            return True
            
        # 包含関係チェック（類似性の高い重複を検出）
        if len(new_clean) > 10 and len(existing_clean) > 10:
            if new_clean in existing_clean or existing_clean in new_clean:
                return True
    
    return False

def filter_duplicate_topics(topics: List[str], existing_titles: Set[str] = None) -> List[str]:
    """
    トピックリストから重複するものを除外
    
    Args:
        topics: チェック対象のトピックリスト
        existing_titles: 既存タイトルセット（Noneの場合は自動取得）
        
    Returns:
        List[str]: 重複を除外したトピックリスト
    """
    if existing_titles is None:
        existing_titles = fetch_existing_titles()
    
    unique_topics = []
    skipped_count = 0
    
    logging.info(f"重複チェック開始: {len(topics)} 件のトピックを検証")
    
    for topic in topics:
        if is_duplicate_title(topic, existing_titles):
            logging.warning(f"⚠️  重複スキップ: {topic}")
            skipped_count += 1
        else:
            unique_topics.append(topic)
            # 処理中のトピックも既存リストに追加（同一実行内での重複防止）
            existing_titles.add(topic)
    
    logging.info(f"✅ 重複チェック完了:")
    logging.info(f"   - 有効なトピック: {len(unique_topics)} 件")
    logging.info(f"   - 重複でスキップ: {skipped_count} 件")
    
    return unique_topics

def check_single_topic(topic: str) -> bool:
    """
    単一トピックの重複チェック
    
    Args:
        topic: チェック対象のトピック
        
    Returns:
        bool: 重複していない場合True（生成可能）
    """
    existing_titles = fetch_existing_titles()
    
    if is_duplicate_title(topic, existing_titles):
        logging.warning(f"⚠️  重複検出: '{topic}' は既存記事と重複しています")
        return False
    
    logging.info(f"✅ 重複なし: '{topic}' は生成可能です")
    return True

def get_stats() -> dict:
    """
    既存記事の統計情報を取得
    
    Returns:
        dict: 統計情報
    """
    existing_titles = fetch_existing_titles()
    
    return {
        "total_articles": len(existing_titles),
        "category_id": config.category_id,
        "site_url": config.wp_site_url
    }

if __name__ == "__main__":
    # テスト実行
    print("🔍 重複チェッカーのテスト実行")
    
    # 統計情報表示
    stats = get_stats()
    print(f"📊 既存記事数: {stats['total_articles']} 件")
    
    # サンプルトピックでテスト
    test_topics = [
        "get_posts() でカスタム投稿を取得する方法",  # 既存の可能性が高い
        "テスト用の新しいトピック例",                    # 新規の可能性が高い
    ]
    
    for topic in test_topics:
        result = check_single_topic(topic)
        print(f"{'✅' if result else '❌'} {topic}")