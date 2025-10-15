#!/usr/bin/env python3
"""
MongoDB Index Auto-Deployment Script

This script executes MongoDB shell (mongosh) JavaScript files to deploy indexes.
Connection credentials are read from environment variables for security.
All operations are logged with proper error handling.
"""

import os
import sys
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Tuple


# Create deployment_logs directory if it doesn't exist
log_dir = Path('deployment_logs')
log_dir.mkdir(exist_ok=True)

# Configure logging
log_file = log_dir / f'index_deployment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


class MongoIndexDeployer:
    """Handles MongoDB index deployment operations using mongosh."""

    def __init__(self, connection_string: str):
        """
        Initialize the MongoDB Index Deployer.

        Args:
            connection_string: MongoDB connection string with credentials
        """
        self.connection_string = connection_string

    def check_mongosh_installed(self) -> bool:
        """
        Check if mongosh is installed and available.

        Returns:
            bool: True if mongosh is installed, False otherwise
        """
        try:
            result = subprocess.run(
                ['mongosh', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"MongoDB Shell (mongosh) found: {version}")
                return True
            else:
                logger.error("mongosh is installed but returned an error")
                return False
        except FileNotFoundError:
            logger.error("mongosh is not installed or not in PATH")
            logger.error("Please install MongoDB Shell: https://www.mongodb.com/docs/mongodb-shell/install/")
            return False
        except Exception as e:
            logger.error(f"Error checking mongosh installation: {e}")
            return False

    def test_connection(self) -> bool:
        """
        Test connection to MongoDB cluster.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            logger.info("Testing connection to MongoDB cluster...")
            result = subprocess.run(
                ['mongosh', self.connection_string, '--quiet', '--eval', 'db.adminCommand("ping")'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info("Successfully connected to MongoDB cluster")
                return True
            else:
                logger.error(f"Failed to connect to MongoDB: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.error("Connection attempt timed out after 30 seconds")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection test: {e}")
            return False

    def find_js_files(self, directory: str) -> List[Path]:
        """
        Find all JavaScript files in the specified directory.

        Args:
            directory: Directory path to search for .js files

        Returns:
            List of Path objects for found .js files
        """
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                logger.error(f"Directory not found: {directory}")
                return []

            if not dir_path.is_dir():
                logger.error(f"Path is not a directory: {directory}")
                return []

            js_files = sorted(dir_path.glob('*.js'))

            if not js_files:
                logger.warning(f"No .js files found in {directory}")
                return []

            logger.info(f"Found {len(js_files)} JavaScript file(s) in {directory}")
            for js_file in js_files:
                logger.info(f"  - {js_file.name}")

            return js_files
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
            return []

    def execute_js_file(self, js_file: Path) -> Tuple[bool, str]:
        """
        Execute a JavaScript file using mongosh.

        Args:
            js_file: Path to the JavaScript file

        Returns:
            Tuple of (success: bool, output: str)
        """
        try:
            logger.info("=" * 80)
            logger.info(f"Executing: {js_file.name}")
            logger.info("=" * 80)

            # Execute the JavaScript file using mongosh
            command = [
                'mongosh',
                self.connection_string,
                '--quiet',
                '--file', str(js_file)
            ]

            logger.debug(f"Executing command: mongosh <connection_string> --quiet --file {js_file}")

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            output = result.stdout
            error_output = result.stderr

            # Log the output
            if output:
                logger.info("Script output:")
                for line in output.strip().split('\n'):
                    if line.strip():
                        logger.info(f"  {line}")

            if error_output:
                logger.warning("Script errors/warnings:")
                for line in error_output.strip().split('\n'):
                    if line.strip():
                        logger.warning(f"  {line}")

            if result.returncode == 0:
                logger.info(f"✓ Successfully executed {js_file.name}")
                return True, output
            else:
                logger.error(f"✗ Failed to execute {js_file.name} (exit code: {result.returncode})")
                return False, error_output

        except subprocess.TimeoutExpired:
            logger.error(f"Execution of {js_file.name} timed out after 5 minutes")
            return False, "Timeout"
        except FileNotFoundError:
            logger.error(f"File not found: {js_file}")
            return False, "File not found"
        except Exception as e:
            logger.error(f"Unexpected error executing {js_file.name}: {e}", exc_info=True)
            return False, str(e)

    def deploy_indexes(self, scripts_directory: str) -> bool:
        """
        Deploy all indexes by executing JavaScript files in the specified directory.

        Args:
            scripts_directory: Directory containing .js files to execute

        Returns:
            bool: True if all operations successful, False otherwise
        """
        all_successful = True

        # Find all JavaScript files
        js_files = self.find_js_files(scripts_directory)

        if not js_files:
            logger.error("No JavaScript files found to execute")
            return False

        # Execute each file in alphabetical order
        successful_count = 0
        failed_count = 0

        for js_file in js_files:
            success, output = self.execute_js_file(js_file)

            if success:
                successful_count += 1
            else:
                failed_count += 1
                all_successful = False

        # Summary
        logger.info("=" * 80)
        logger.info("Deployment Summary:")
        logger.info(f"  Total scripts: {len(js_files)}")
        logger.info(f"  Successful: {successful_count}")
        logger.info(f"  Failed: {failed_count}")
        logger.info("=" * 80)

        return all_successful


def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("MongoDB Index Auto-Deployment Script Started")
    logger.info("=" * 80)

    # Get MongoDB connection string from environment variable
    connection_string = os.environ.get('MONGODB_CONNECTION_STRING')
    if not connection_string:
        logger.error("MONGODB_CONNECTION_STRING environment variable is not set")
        logger.error("Please set the connection string as a secret in your GitHub repository")
        sys.exit(1)

    # Get scripts directory path
    scripts_directory = os.environ.get('INDEXES_DIRECTORY', 'indexes_to_deploy')

    # Initialize deployer
    deployer = MongoIndexDeployer(connection_string)

    try:
        # Check if mongosh is installed
        if not deployer.check_mongosh_installed():
            logger.error("MongoDB Shell (mongosh) is required but not found")
            sys.exit(1)

        # Test MongoDB connection
        if not deployer.test_connection():
            logger.error("Failed to establish MongoDB connection")
            sys.exit(1)

        # Deploy indexes
        logger.info(f"Starting index deployment from directory: {scripts_directory}")
        success = deployer.deploy_indexes(scripts_directory)

        if success:
            logger.info("=" * 80)
            logger.info("Index deployment completed successfully")
            logger.info("=" * 80)
            sys.exit(0)
        else:
            logger.error("=" * 80)
            logger.error("Index deployment completed with errors")
            logger.error("=" * 80)
            sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("Deployment interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error during deployment: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
