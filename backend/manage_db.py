#!/usr/bin/env python3
"""
Database management CLI script
"""
import argparse
import logging
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.db.seeder import DatabaseSeeder, init_db_command, seed_db_command, db_stats_command

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_command(args):
    """Handle database initialization"""
    try:
        init_db_command(drop_existing=args.drop)
        logger.info("Database initialized successfully")
        return 0
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return 1


def seed_command(args):
    """Handle database seeding"""
    try:
        if args.sample:
            stats = seed_db_command(sample_data=True)
            logger.info("Sample data seeded successfully")
        elif args.csv_file:
            csv_file = Path(args.csv_file)
            if not csv_file.exists():
                logger.error(f"CSV file not found: {csv_file}")
                return 1
            
            stats = seed_db_command(csv_file=csv_file)
            logger.info("CSV data seeded successfully")
        else:
            logger.error("Either --sample or --csv-file must be specified")
            return 1
        
        # Print statistics
        print("\n=== Seeding Statistics ===")
        print(f"Total processed: {stats['total_processed']}")
        print(f"Total inserted: {stats['total_inserted']}")
        print(f"Total skipped: {stats['total_skipped']}")
        print(f"Total errors: {stats['total_errors']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        return 1


def stats_command(args):
    """Handle database statistics"""
    try:
        stats = db_stats_command()
        
        print("\n=== Database Statistics ===")
        print(f"Total movies: {stats['total_movies']}")
        
        if stats['year_range']['earliest']:
            print(f"Year range: {stats['year_range']['earliest']} - {stats['year_range']['latest']}")
        
        if stats['rating_stats']['avg']:
            print(f"Rating stats - Min: {stats['rating_stats']['min']:.1f}, "
                  f"Max: {stats['rating_stats']['max']:.1f}, "
                  f"Avg: {stats['rating_stats']['avg']:.1f}")
        
        if stats['top_genres']:
            print("\nTop genres:")
            for genre_stat in stats['top_genres']:
                print(f"  {genre_stat['genre']}: {genre_stat['count']} movies")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error getting database statistics: {e}")
        return 1


def reset_command(args):
    """Handle database reset (drop and recreate)"""
    try:
        logger.info("Resetting database...")
        init_db_command(drop_existing=True)
        
        if args.seed_sample:
            seed_db_command(sample_data=True)
            logger.info("Database reset and seeded with sample data")
        else:
            logger.info("Database reset (empty)")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        return 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Database Management CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize database tables')
    init_parser.add_argument('--drop', action='store_true', help='Drop existing tables first')
    
    # Seed command
    seed_parser = subparsers.add_parser('seed', help='Seed database with data')
    seed_group = seed_parser.add_mutually_exclusive_group(required=True)
    seed_group.add_argument('--sample', action='store_true', help='Seed with sample data')
    seed_group.add_argument('--csv-file', help='Seed from CSV file')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    
    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Reset database (drop and recreate)')
    reset_parser.add_argument('--seed-sample', action='store_true', help='Seed with sample data after reset')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate command handler
    if args.command == 'init':
        return init_command(args)
    elif args.command == 'seed':
        return seed_command(args)
    elif args.command == 'stats':
        return stats_command(args)
    elif args.command == 'reset':
        return reset_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())