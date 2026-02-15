"""
Enterprise Data Validation Framework - Main Execution Script
Author: T Samuel Paul
Description: Orchestrates data validation across multiple sources
"""

import argparse
import sys
from datetime import datetime
import logging
from typing import Dict, List
import pandas as pd

from src.validators.completeness_validator import CompletenessValidator
from src.validators.accuracy_validator import AccuracyValidator
from src.validators.consistency_validator import ConsistencyValidator
from src.validators.anomaly_detector import AnomalyDetector
from src.connectors.sql_connector import SQLConnector
from src.reporting.dashboard_generator import DashboardGenerator
from src.reporting.alert_system import AlertSystem
from src.utils.config_manager import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/validation_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ValidationOrchestrator:
    """Main orchestrator for data validation framework."""
    
    def __init__(self, config_path: str = 'config.py'):
        """Initialize validation orchestrator."""
        self.config = ConfigManager(config_path)
        self.db_connector = SQLConnector(self.config.get_db_config())
        self.results = {
            'completeness': [],
            'accuracy': [],
            'consistency': [],
            'anomaly': []
        }
        
    def run_completeness_validation(self, source: str = None) -> List[Dict]:
        """
        Run completeness validation checks.
        
        Args:
            source: Specific data source to validate (None for all)
            
        Returns:
            List of validation results
        """
        logger.info("="*60)
        logger.info("RUNNING COMPLETENESS VALIDATION")
        logger.info("="*60)
        
        validator = CompletenessValidator(self.db_connector)
        sources = [source] if source else self.config.get_data_sources()
        
        for src in sources:
            logger.info(f"Validating source: {src}")
            results = validator.validate(src)
            self.results['completeness'].extend(results)
            
            # Log results
            for result in results:
                if result['status'] == 'FAILED':
                    logger.warning(
                        f"❌ {src} - {result['rule']}: "
                        f"{result['errors_found']} errors found"
                    )
                else:
                    logger.info(f"✓ {src} - {result['rule']}: Passed")
        
        return self.results['completeness']
    
    def run_accuracy_validation(self, source: str = None) -> List[Dict]:
        """
        Run accuracy validation checks.
        
        Args:
            source: Specific data source to validate (None for all)
            
        Returns:
            List of validation results
        """
        logger.info("="*60)
        logger.info("RUNNING ACCURACY VALIDATION")
        logger.info("="*60)
        
        validator = AccuracyValidator(self.db_connector)
        sources = [source] if source else self.config.get_data_sources()
        
        for src in sources:
            logger.info(f"Validating source: {src}")
            results = validator.validate(src)
            self.results['accuracy'].extend(results)
            
            for result in results:
                if result['status'] == 'FAILED':
                    logger.warning(
                        f"❌ {src} - {result['rule']}: "
                        f"{result['errors_found']} errors found"
                    )
                else:
                    logger.info(f"✓ {src} - {result['rule']}: Passed")
        
        return self.results['accuracy']
    
    def run_consistency_validation(self, source: str = None) -> List[Dict]:
        """
        Run consistency validation checks.
        
        Args:
            source: Specific data source to validate (None for all)
            
        Returns:
            List of validation results
        """
        logger.info("="*60)
        logger.info("RUNNING CONSISTENCY VALIDATION")
        logger.info("="*60)
        
        validator = ConsistencyValidator(self.db_connector)
        results = validator.validate_all()
        self.results['consistency'].extend(results)
        
        for result in results:
            if result['status'] == 'FAILED':
                logger.warning(
                    f"❌ {result['rule']}: "
                    f"{result['errors_found']} inconsistencies found"
                )
            else:
                logger.info(f"✓ {result['rule']}: Passed")
        
        return self.results['consistency']
    
    def run_anomaly_detection(self, source: str = None) -> List[Dict]:
        """
        Run anomaly detection.
        
        Args:
            source: Specific data source to analyze (None for all)
            
        Returns:
            List of detected anomalies
        """
        logger.info("="*60)
        logger.info("RUNNING ANOMALY DETECTION")
        logger.info("="*60)
        
        detector = AnomalyDetector(self.db_connector)
        sources = [source] if source else self.config.get_data_sources()
        
        for src in sources:
            logger.info(f"Analyzing source: {src}")
            results = detector.detect(src)
            self.results['anomaly'].extend(results)
            
            for result in results:
                logger.warning(
                    f"⚠️  {src} - {result['column']}: "
                    f"{result['anomaly_count']} anomalies detected "
                    f"(Method: {result['method']})"
                )
        
        return self.results['anomaly']
    
    def generate_summary(self) -> Dict:
        """
        Generate validation summary statistics.
        
        Returns:
            Summary dictionary
        """
        total_checks = sum(len(v) for v in self.results.values())
        failed_checks = sum(
            1 for category in self.results.values()
            for result in category
            if result.get('status') == 'FAILED'
        )
        
        summary = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_checks': total_checks,
            'passed_checks': total_checks - failed_checks,
            'failed_checks': failed_checks,
            'accuracy': (total_checks - failed_checks) / total_checks if total_checks > 0 else 0,
            'by_category': {
                'completeness': {
                    'total': len(self.results['completeness']),
                    'failed': sum(1 for r in self.results['completeness'] if r.get('status') == 'FAILED')
                },
                'accuracy': {
                    'total': len(self.results['accuracy']),
                    'failed': sum(1 for r in self.results['accuracy'] if r.get('status') == 'FAILED')
                },
                'consistency': {
                    'total': len(self.results['consistency']),
                    'failed': sum(1 for r in self.results['consistency'] if r.get('status') == 'FAILED')
                },
                'anomaly': {
                    'total': len(self.results['anomaly']),
                    'detected': len(self.results['anomaly'])
                }
            }
        }
        
        return summary
    
    def print_summary(self, summary: Dict) -> None:
        """Print validation summary to console."""
        print("\n" + "="*70)
        print("DATA VALIDATION SUMMARY")
        print("="*70)
        print(f"Timestamp:        {summary['timestamp']}")
        print(f"Total Checks:     {summary['total_checks']}")
        print(f"Passed:           {summary['passed_checks']} ({summary['accuracy']*100:.2f}%)")
        print(f"Failed:           {summary['failed_checks']}")
        print("\nBy Category:")
        print("-" * 70)
        
        for category, stats in summary['by_category'].items():
            if category == 'anomaly':
                print(f"{category.upper():15} - Anomalies Detected: {stats['detected']}")
            else:
                failed = stats['failed']
                total = stats['total']
                print(f"{category.upper():15} - Failed: {failed}/{total}")
        
        print("="*70)
        
        # Print status
        if summary['failed_checks'] == 0:
            print("✅ ALL VALIDATIONS PASSED")
        else:
            print(f"⚠️  {summary['failed_checks']} VALIDATION(S) FAILED - REVIEW REQUIRED")
        print("="*70 + "\n")
    
    def send_alerts(self, summary: Dict) -> None:
        """Send alerts for critical failures."""
        alert_system = AlertSystem(self.config.get_alert_config())
        
        # Send alert if accuracy below threshold
        if summary['accuracy'] < 0.95:  # 95% threshold
            alert_system.send_critical_alert(
                subject="Critical: Data Validation Accuracy Below Threshold",
                message=f"Overall validation accuracy: {summary['accuracy']*100:.2f}%\n"
                       f"Failed checks: {summary['failed_checks']}\n"
                       f"Review required immediately."
            )
        
        # Send alerts for specific failures
        for category, results in self.results.items():
            for result in results:
                if result.get('severity') == 'critical' and result.get('status') == 'FAILED':
                    alert_system.send_critical_alert(
                        subject=f"Critical Validation Failure: {result['rule']}",
                        message=f"Source: {result.get('source', 'N/A')}\n"
                               f"Errors: {result['errors_found']}\n"
                               f"Details: {result.get('details', 'N/A')}"
                    )


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Enterprise Data Validation Framework')
    parser.add_argument('--mode', 
                       choices=['all', 'completeness', 'accuracy', 'consistency', 'anomaly'],
                       default='all',
                       help='Validation mode to run')
    parser.add_argument('--source',
                       type=str,
                       default=None,
                       help='Specific data source to validate')
    parser.add_argument('--report',
                       action='store_true',
                       help='Generate HTML report')
    parser.add_argument('--alerts',
                       action='store_true',
                       help='Send email alerts for failures')
    
    args = parser.parse_args()
    
    try:
        # Initialize orchestrator
        orchestrator = ValidationOrchestrator()
        
        # Run validation based on mode
        if args.mode in ['all', 'completeness']:
            orchestrator.run_completeness_validation(args.source)
        
        if args.mode in ['all', 'accuracy']:
            orchestrator.run_accuracy_validation(args.source)
        
        if args.mode in ['all', 'consistency']:
            orchestrator.run_consistency_validation(args.source)
        
        if args.mode in ['all', 'anomaly']:
            orchestrator.run_anomaly_detection(args.source)
        
        # Generate and print summary
        summary = orchestrator.generate_summary()
        orchestrator.print_summary(summary)
        
        # Generate report if requested
        if args.report:
            dashboard = DashboardGenerator()
            report_path = dashboard.generate_report(orchestrator.results, summary)
            logger.info(f"Validation report generated: {report_path}")
        
        # Send alerts if requested
        if args.alerts:
            orchestrator.send_alerts(summary)
            logger.info("Alerts sent for critical failures")
        
        # Exit with appropriate code
        sys.exit(0 if summary['failed_checks'] == 0 else 1)
        
    except Exception as e:
        logger.error(f"Validation framework error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
