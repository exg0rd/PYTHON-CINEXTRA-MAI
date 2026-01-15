#!/usr/bin/env python3
"""
CLI script for CSV parsing and database operations
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import List
import getpass

from .csv_parser import MovieCSVParser, CSVParsingError, create_sample_csv_data
from .credits_parser import import_credits_from_csv
from ..models.movie import MovieData
from ..db.database import SessionLocal
from ..db.models import User
from ..api.auth import get_password_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_admin_command(args):
    """Handle admin user creation command"""
    try:
        db = SessionLocal()
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(
                (User.email == args.email) | (User.username == args.username)
            ).first()
            
            if existing_user:
                if existing_user.email == args.email:
                    logger.error(f"User with email {args.email} already exists")
                else:
                    logger.error(f"User with username {args.username} already exists")
                return 1
            
            # Get password
            if args.password:
                password = args.password
            else:
                password = getpass.getpass("Enter password for admin user: ")
                confirm_password = getpass.getpass("Confirm password: ")
                
                if password != confirm_password:
                    logger.error("Passwords do not match")
                    return 1
            
            if len(password) < 6:
                logger.error("Password must be at least 6 characters long")
                return 1
            
            # Create admin user
            hashed_password = get_password_hash(password)
            admin_user = User(
                email=args.email,
                username=args.username,
                password_hash=hashed_password,
                is_admin=True
            )
            
            db.add(admin_user)
            db.commit()
            
            logger.info(f"Admin user created successfully!")
            logger.info(f"Username: {args.username}")
            logger.info(f"Email: {args.email}")
            logger.info(f"Admin privileges: Yes")
            
            return 0
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        return 1


def make_admin_command(args):
    """Handle making existing user admin command"""
    try:
        db = SessionLocal()
        try:
            # Find user by email or username
            user = db.query(User).filter(
                (User.email == args.identifier) | (User.username == args.identifier)
            ).first()
            
            if not user:
                logger.error(f"User not found: {args.identifier}")
                return 1
            
            if user.is_admin:
                logger.info(f"User {user.username} is already an admin")
                return 0
            
            # Make user admin
            user.is_admin = True
            db.commit()
            
            logger.info(f"User {user.username} is now an admin!")
            
            return 0
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Error making user admin: {e}")
        return 1


def list_users_command(args):
    """Handle list users command"""
    try:
        db = SessionLocal()
        try:
            users = db.query(User).all()
            
            if not users:
                logger.info("No users found")
                return 0
            
            print("\n=== Users ===")
            print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Admin':<8} {'Created':<20}")
            print("-" * 85)
            
            for user in users:
                created_date = user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else "N/A"
                admin_status = "Yes" if user.is_admin else "No"
                
                print(f"{user.id:<5} {user.username:<20} {user.email:<30} {admin_status:<8} {created_date:<20}")
            
            print(f"\nTotal users: {len(users)}")
            admin_count = sum(1 for user in users if user.is_admin)
            print(f"Admin users: {admin_count}")
            
            return 0
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return 1
    """Handle credits import command"""
    try:
        csv_file = Path(args.csv_file)
        
        if not csv_file.exists():
            logger.error(f"Credits CSV file not found: {csv_file}")
            return 1
        
        db = SessionLocal()
        try:
            logger.info(f"Starting credits import from: {csv_file}")
            stats = import_credits_from_csv(db, str(csv_file))
            
            logger.info("Credits import completed!")
            logger.info(f"Movies processed: {stats['movies_processed']}")
            logger.info(f"Cast members imported: {stats['cast_imported']}")
            logger.info(f"Crew members imported: {stats['crew_imported']}")
            logger.info(f"Errors: {stats['errors']}")
            
            return 0
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Error importing credits: {e}")
        return 1


def import_credits_command(args):
    """Handle credits import command"""
    try:
        csv_file = Path(args.csv_file)
        
        if not csv_file.exists():
            logger.error(f"Credits CSV file not found: {csv_file}")
            return 1
        
        db = SessionLocal()
        try:
            logger.info(f"Starting credits import from: {csv_file}")
            stats = import_credits_from_csv(db, str(csv_file))
            
            logger.info("Credits import completed!")
            logger.info(f"Movies processed: {stats['movies_processed']}")
            logger.info(f"Cast members imported: {stats['cast_imported']}")
            logger.info(f"Crew members imported: {stats['crew_imported']}")
            logger.info(f"Errors: {stats['errors']}")
            
            return 0
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Error importing credits: {e}")
        return 1


def parse_csv_command(args):
    """Handle CSV parsing command"""
    try:
        csv_file = Path(args.csv_file)
        
        if not csv_file.exists():
            logger.error(f"CSV file not found: {csv_file}")
            return 1
        
        parser = MovieCSVParser(batch_size=args.batch_size)
        
        if args.stats_only:
            # Just show statistics
            stats = parser.get_csv_stats(csv_file)
            print("\n=== CSV File Statistics ===")
            print(f"Total rows: {stats['total_rows']}")
            print(f"Columns: {len(stats['columns'])}")
            print(f"Missing titles: {stats['missing_titles']}")
            
            if stats['date_range']['earliest']:
                print(f"Date range: {stats['date_range']['earliest']} to {stats['date_range']['latest']}")
            
            if stats['rating_stats']['mean']:
                print(f"Rating stats - Min: {stats['rating_stats']['min']:.1f}, "
                      f"Max: {stats['rating_stats']['max']:.1f}, "
                      f"Mean: {stats['rating_stats']['mean']:.1f}")
            
            return 0
        
        # Parse CSV file
        logger.info(f"Starting CSV parsing: {csv_file}")
        
        if args.batch_mode:
            # Process in batches
            total_movies = 0
            for batch_num, batch in enumerate(parser.parse_csv_batch(csv_file)):
                total_movies += len(batch)
                logger.info(f"Batch {batch_num + 1}: {len(batch)} movies parsed")
                
                # In a real implementation, this is where you'd save to database
                if args.output:
                    output_file = Path(args.output) / f"batch_{batch_num + 1}.json"
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    import json
                    with open(output_file, 'w') as f:
                        json.dump([movie.dict() for movie in batch], f, indent=2, default=str)
                    
                    logger.info(f"Batch saved to: {output_file}")
            
            logger.info(f"Total movies parsed: {total_movies}")
        else:
            # Parse entire file
            movies = parser.parse_csv_file(csv_file)
            logger.info(f"Parsed {len(movies)} movies from CSV")
            
            if args.output:
                output_file = Path(args.output)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                import json
                with open(output_file, 'w') as f:
                    json.dump([movie.dict() for movie in movies], f, indent=2, default=str)
                
                logger.info(f"Results saved to: {output_file}")
        
        return 0
        
    except CSVParsingError as e:
        logger.error(f"CSV parsing error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


def create_sample_command(args):
    """Handle sample data creation command"""
    try:
        output_path = Path(args.output)
        create_sample_csv_data(output_path)
        logger.info(f"Sample CSV data created at: {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        return 1


def validate_csv_command(args):
    """Handle CSV validation command"""
    try:
        csv_file = Path(args.csv_file)
        
        if not csv_file.exists():
            logger.error(f"CSV file not found: {csv_file}")
            return 1
        
        parser = MovieCSVParser()
        
        if parser.validate_csv_format(csv_file):
            logger.info("CSV file format is valid")
            
            # Show basic info
            stats = parser.get_csv_stats(csv_file)
            print(f"✓ CSV file is valid")
            print(f"✓ Total rows: {stats['total_rows']}")
            print(f"✓ Columns found: {len(stats['columns'])}")
            
            return 0
        
    except CSVParsingError as e:
        logger.error(f"CSV validation failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Movie CSV Parser CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Parse command
    parse_parser = subparsers.add_parser('parse', help='Parse CSV file')
    parse_parser.add_argument('csv_file', help='Path to CSV file')
    parse_parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for processing')
    parse_parser.add_argument('--batch-mode', action='store_true', help='Process in batches')
    parse_parser.add_argument('--output', help='Output file/directory for results')
    parse_parser.add_argument('--stats-only', action='store_true', help='Show only statistics')
    
    # Import credits command
    credits_parser = subparsers.add_parser('import-credits', help='Import cast and crew credits from CSV file')
    credits_parser.add_argument('csv_file', help='Path to credits CSV file')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate CSV file format')
    validate_parser.add_argument('csv_file', help='Path to CSV file')
    
    # Create sample command
    sample_parser = subparsers.add_parser('create-sample', help='Create sample CSV data')
    sample_parser.add_argument('output', help='Output path for sample CSV file')
    
    # Admin user management commands
    admin_parser = subparsers.add_parser('create-admin', help='Create admin user')
    admin_parser.add_argument('username', help='Username for admin user')
    admin_parser.add_argument('email', help='Email for admin user')
    admin_parser.add_argument('--password', help='Password for admin user (will prompt if not provided)')
    
    make_admin_parser = subparsers.add_parser('make-admin', help='Make existing user admin')
    make_admin_parser.add_argument('identifier', help='Username or email of user to make admin')
    
    list_users_parser = subparsers.add_parser('list-users', help='List all users')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate command handler
    if args.command == 'parse':
        return parse_csv_command(args)
    elif args.command == 'import-credits':
        return import_credits_command(args)
    elif args.command == 'validate':
        return validate_csv_command(args)
    elif args.command == 'create-sample':
        return create_sample_command(args)
    elif args.command == 'create-admin':
        return create_admin_command(args)
    elif args.command == 'make-admin':
        return make_admin_command(args)
    elif args.command == 'list-users':
        return list_users_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())