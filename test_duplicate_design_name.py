#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
디자인명 중복 문제 테스트
서로 다른 ID지만 동일한 디자인명을 가진 경우 테스트
"""
import requests
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import models
from core.config import settings

BASE_URL = "http://localhost:8000"

def setup_test_data():
    """동일한 디자인명을 가진 제품 2개 생성"""
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # 기존 TEST_DUPLICATE 제품들 삭제
        db.query(models.Releasedproduct).filter(
            models.Releasedproduct.design_name == "TEST_DUPLICATE"
        ).delete()
        db.commit()
        
        # 동일한 디자인명으로 2개 제품 생성
        product1 = models.Releasedproduct(
            user_id=33,  # tester1 user_id
            design_name="TEST_DUPLICATE",
            color_name="Color1",
            brand_id=1,
            main_image_url="http://example.com/image1.jpg",
            thumbnail_url="http://example.com/thumb1.jpg",
            views=0
        )
        
        product2 = models.Releasedproduct(
            user_id=33,  # tester1 user_id
            design_name="TEST_DUPLICATE",  # 동일한 디자인명!
            color_name="Color2", 
            brand_id=1,
            main_image_url="http://example.com/image2.jpg",
            thumbnail_url="http://example.com/thumb2.jpg",
            views=0
        )
        
        db.add(product1)
        db.add(product2)
        db.commit()
        
        db.refresh(product1)
        db.refresh(product2)
        
        print("="*70)
        print("테스트 데이터 생성 완료")
        print("-"*70)
        print(f"Product 1 - ID: {product1.id}, Name: {product1.design_name}, Color: {product1.color_name}")
        print(f"Product 2 - ID: {product2.id}, Name: {product2.design_name}, Color: {product2.color_name}")
        print("="*70)
        
        return product1.id, product2.id
        
    finally:
        db.close()

def login():
    """로그인하여 토큰 획득"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": "tester1", "password": "1234567"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_duplicate_design_name(product1_id, product2_id):
    """디자인명 중복 문제 테스트"""
    token = login()
    if not token:
        print("로그인 실패")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n" + "="*70)
    print("디자인명 중복 문제 테스트")
    print("="*70)
    
    # 1. 첫 번째 제품 입장
    print(f"\n1. Product 1 (ID={product1_id}) 입장")
    response = requests.post(
        f"{BASE_URL}/unity/released_product/enter/by-id/{product1_id}",
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   디자인명: {data.get('item_name')}")
        print(f"   실시간 유저수: {data.get('realtime_users')}")
    
    # 2. 두 번째 제품 입장 (동일한 디자인명, 다른 ID)
    print(f"\n2. Product 2 (ID={product2_id}) 입장 - 동일한 디자인명, 다른 ID")
    response = requests.post(
        f"{BASE_URL}/unity/released_product/enter/by-id/{product2_id}",
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   디자인명: {data.get('item_name')}")
        print(f"   실시간 유저수: {data.get('realtime_users')}")
        
        if data.get('realtime_users') == 1:
            print("\n   ❌ 문제 발견!")
            print("   서로 다른 ID인데 디자인명이 같아서 중복 처리됨")
            print("   ID별로 구분되어야 하는데 디자인명으로만 구분됨")
        else:
            print("\n   ✅ 정상: ID별로 구분됨")
    
    # 3. 각 제품의 실시간 유저수 개별 확인
    print(f"\n3. 각 제품의 실시간 유저수 확인")
    
    print(f"\n   Product 1 (ID={product1_id}) 유저수:")
    response = requests.get(
        f"{BASE_URL}/unity/released_product/realtime-users/by-id/{product1_id}",
        headers=headers
    )
    if response.status_code == 200:
        print(f"   → {response.json().get('realtime_users')}명")
    
    print(f"\n   Product 2 (ID={product2_id}) 유저수:")
    response = requests.get(
        f"{BASE_URL}/unity/released_product/realtime-users/by-id/{product2_id}",
        headers=headers
    )
    if response.status_code == 200:
        print(f"   → {response.json().get('realtime_users')}명")
    
    # 4. DB 직접 확인
    print("\n4. DB 직접 확인")
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    realtime_records = db.query(models.RealtimeUser).filter(
        models.RealtimeUser.content_type == 'released_product',
        models.RealtimeUser.content_name == 'TEST_DUPLICATE'
    ).all()
    
    print(f"   RealtimeUser 테이블 레코드 수: {len(realtime_records)}")
    for record in realtime_records:
        print(f"   - user_id: {record.user_id}, content_name: {record.content_name}")
    
    db.close()
    
    # 5. 정리
    print("\n5. 테스트 정리 (퇴장)")
    requests.post(f"{BASE_URL}/unity/released_product/leave/by-id/{product1_id}", headers=headers)
    requests.post(f"{BASE_URL}/unity/released_product/leave/by-id/{product2_id}", headers=headers)
    
    print("\n" + "="*70)
    print("문제 요약:")
    print("-"*70)
    print("현재 시스템은 content_name(디자인명)으로만 중복을 체크합니다.")
    print("따라서 서로 다른 ID의 제품이라도 디자인명이 같으면")
    print("동일한 제품으로 인식되어 카운트가 증가하지 않습니다.")
    print("\n해결 방법:")
    print("RealtimeUser 테이블에 content_id 필드를 추가하고")
    print("UniqueConstraint를 (user_id, content_type, content_id)로 변경해야 합니다.")
    print("="*70)

if __name__ == "__main__":
    # 테스트 데이터 생성
    product1_id, product2_id = setup_test_data()
    
    # 테스트 실행
    test_duplicate_design_name(product1_id, product2_id)