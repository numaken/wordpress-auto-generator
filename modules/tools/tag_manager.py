#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging

def get_or_create_tag_id(tag_name: str, config) -> int:
    """
    タグ名からタグIDを取得、存在しなければ作成
    
    Args:
        tag_name (str): タグ名
        config: 設定オブジェクト（wp_site_url, get_auth_header()を持つ）
    
    Returns:
        int: タグID、失敗時はNone
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
            logging.info(f"タグ作成成功: {tag_name} (ID: {new_tag['id']})")
            return new_tag["id"]
        else:
            logging.error(f"タグ作成失敗: {tag_name} - {create_response.text}")
        
    except Exception as e:
        logging.error(f"タグ処理エラー ({tag_name}): {e}")
    
    return None

def get_tag_ids(tag_names: list, config) -> list:
    """
    タグ名のリストからタグIDのリストを取得
    
    Args:
        tag_names (list): タグ名のリスト
        config: 設定オブジェクト
    
    Returns:
        list: タグIDのリスト
    """
    if not tag_names:
        return []
    
    tag_ids = []
    for tag_name in tag_names:
        tag_id = get_or_create_tag_id(tag_name, config)
        if tag_id:
            tag_ids.append(tag_id)
        else:
            logging.warning(f"タグIDの取得に失敗: {tag_name}")
    
    logging.info(f"タグID変換完了: {len(tag_names)}個中{len(tag_ids)}個成功")
    return tag_ids

def get_category_specific_tags(category_type: str) -> list:
    """
    カテゴリに応じたデフォルトタグを取得
    
    Args:
        category_type (str): カテゴリタイプ ('javascript', 'python', 'general', etc.)
    
    Returns:
        list: タグ名のリスト
    """
    tag_mapping = {
        'javascript': ["JavaScript", "プログラミング", "Web開発", "フロントエンド"],
        'python': ["Python", "Django", "FastAPI", "データサイエンス"],
        'react': ["React", "Next.js", "TypeScript", "フロントエンド"],
        'vue': ["Vue.js", "Nuxt.js", "フロントエンド", "TypeScript"],
        'wordpress': ["WordPress", "PHP", "CMS", "開発"],
        'nodejs': ["Node.js", "JavaScript", "バックエンド", "サーバーサイド"],
        'typescript': ["TypeScript", "JavaScript", "型安全", "開発効率"],
        'general': ["プログラミング", "技術", "開発"],
        'ai': ["AI", "機械学習", "人工知能", "テクノロジー"],
        'web': ["Web開発", "HTML", "CSS", "JavaScript"]
    }
    
    return tag_mapping.get(category_type, tag_mapping['general'])

def post_to_wordpress_with_tags(title: str, content: str, category_id: int, tag_category: str, config, status: str = "draft") -> bool:
    """
    WordPress REST API 経由でタグ付きの記事を投稿
    
    Args:
        title: 記事タイトル
        content: 記事内容
        category_id: カテゴリID
        tag_category: タグカテゴリ ('javascript', 'python', 'react', 'vue', 'wordpress')
        config: 設定オブジェクト
        status: 投稿ステータス
    
    Returns:
        bool: 成功時True
    """
    import json
    
    # カテゴリに応じたタグを取得
    tag_names = get_category_specific_tags(tag_category)
    tag_ids = get_tag_ids(tag_names, config)
    
    post_data = {
        "title": title,
        "content": content,
        "status": status,
        "categories": [category_id],
        "tags": tag_ids,  # 整数のIDを使用
    }
    
    try:
        post_res = requests.post(
            f"{config.wp_site_url}/wp-json/wp/v2/posts",
            headers=config.get_auth_header(),
            data=json.dumps(post_data),
            timeout=30
        )
        
        if post_res.status_code in (200, 201):
            status_text = "下書き保存" if status == "draft" else "投稿"
            logging.info(f"✅ {status_text}成功: {title}")
            return True
        else:
            logging.error(f"❌ 投稿失敗 ({post_res.status_code}):")
            logging.error(post_res.text)
            return False
            
    except Exception as e:
        logging.error(f"❌ WordPress API エラー: {e}")
        return False