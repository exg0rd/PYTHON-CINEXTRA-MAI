#!/usr/bin/env python3
"""
Recreate admin user with password admin123
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.db.models import User
from app.core.auth import get_password_hash

def recreate_admin():
    """Recreate admin user with password admin123"""
    
    print("Recreating admin user...")
    print("=" * 40)
    
    db = SessionLocal()
    try:
        # Delete existing admin users
        print("Removing existing admin users...")
        existing_admins = db.query(User).filter(
            (User.email == "admin@cinema.com") | 
            (User.username == "admin") |
            (User.is_admin == True)
        ).all()
        
        for admin in existing_admins:
            print(f"   Removing: {admin.username} ({admin.email})")
            db.delete(admin)
        
        db.commit()
        
        # Create new admin user
        print("Creating new admin user...")
        password = "admin123"
        hashed_password = get_password_hash(password)
        
        admin_user = User(
            email="admin@cinema.com",
            username="admin",
            password_hash=hashed_password,
            is_admin=True
        )
        
        db.add(admin_user)
        db.commit()
        
        print("Admin user created successfully!")
        print(f"   Username: admin")
        print(f"   Email: admin@cinema.com")
        print(f"   Password: admin123")
        print(f"   Admin privileges: Yes")
        
        return True
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    success = recreate_admin()
    sys.exit(0 if success else 1)