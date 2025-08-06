#!/usr/bin/env python
"""
커스텀 디자인 테이블의 user_id를 숫자 ID에서 username으로 변경하는 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from db.database import engine, SessionLocal
from db import models

def fix_custom_design_user_ids():
    """user_id가 숫자로 저장된 커스텀 디자인을 username으로 변경합니다."""
    db = SessionLocal()
    
    try:
        # user_id가 숫자로만 이루어진 커스텀 디자인 찾기
        custom_designs_with_numeric_user_id = db.query(models.CustomDesign).filter(
            models.CustomDesign.user_id.op('~')('^[0-9]+$')  # 숫자만으로 이루어진 user_id
        ).all()
        
        if not custom_designs_with_numeric_user_id:
            print("숫자 user_id를 가진 커스텀 디자인이 없습니다.")
            return
        
        print(f"숫자 user_id를 가진 커스텀 디자인 수: {len(custom_designs_with_numeric_user_id)}")
        
        fixed_count = 0
        for design in custom_designs_with_numeric_user_id:
            try:
                # 숫자 ID로 AdminUser 찾기
                user_numeric_id = int(design.user_id)
                user = db.query(models.AdminUser).filter(
                    models.AdminUser.id == user_numeric_id
                ).first()
                
                if user:
                    old_user_id = design.user_id
                    design.user_id = user.username
                    print(f"커스텀 디자인 ID {design.id}: user_id를 '{old_user_id}' → '{user.username}'으로 변경")
                    fixed_count += 1
                else:
                    print(f"경고: 커스텀 디자인 ID {design.id}의 user_id '{design.user_id}'에 해당하는 사용자를 찾을 수 없습니다.")
            except ValueError:
                print(f"경고: 커스텀 디자인 ID {design.id}의 user_id '{design.user_id}'를 숫자로 변환할 수 없습니다.")
        
        # 변경사항 커밋
        db.commit()
        print(f"\n총 {fixed_count}개의 커스텀 디자인 user_id가 업데이트되었습니다.")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix_custom_design_user_ids()