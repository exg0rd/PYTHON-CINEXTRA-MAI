#!/usr/bin/env python3
"""
Simple script to create an admin user
"""
import sys
from app.core.cli import main

if __name__ == '__main__':
    # Override sys.argv to create admin user
    if len(sys.argv) < 3:
        print("Usage: python create_admin.py <username> <email>")
        print("Example: python create_admin.py admin admin@example.com")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    
    # Set up arguments for CLI
    sys.argv = ['cli.py', 'create-admin', username, email]
    
    # Run the CLI
    sys.exit(main())