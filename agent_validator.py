#!/usr/bin/env python3
"""
Agent Behavior Validation
Tests and validates agent responses and behaviors
"""

import json
import re
from datetime import datetime
from pathlib import Path

class AgentValidator:
    def __init__(self):
        self.test_results = []
        self.validation_log = Path("/root/.openclaw/workspace/memory/validation_log.json")
    
    def validate_response(self, response, criteria):
        """
        Validate a response against criteria
        criteria: dict with keys like 'max_length', 'required_keywords', 'forbidden_patterns'
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'passed': True,
            'checks': []
        }
        
        # Check max length
        if 'max_length' in criteria:
            length_ok = len(response) <= criteria['max_length']
            results['checks'].append({
                'check': 'max_length',
                'passed': length_ok,
                'details': f"Length: {len(response)} / {criteria['max_length']}"
            })
            results['passed'] &= length_ok
        
        # Check required keywords
        if 'required_keywords' in criteria:
            missing = []
            for keyword in criteria['required_keywords']:
                if keyword.lower() not in response.lower():
                    missing.append(keyword)
            
            keywords_ok = len(missing) == 0
            results['checks'].append({
                'check': 'required_keywords',
                'passed': keywords_ok,
                'details': f"Missing: {missing}" if missing else "All present"
            })
            results['passed'] &= keywords_ok
        
        # Check forbidden patterns
        if 'forbidden_patterns' in criteria:
            found = []
            for pattern in criteria['forbidden_patterns']:
                if re.search(pattern, response, re.IGNORECASE):
                    found.append(pattern)
            
            patterns_ok = len(found) == 0
            results['checks'].append({
                'check': 'forbidden_patterns',
                'passed': patterns_ok,
                'details': f"Found: {found}" if found else "None found"
            })
            results['passed'] &= patterns_ok
        
        self.test_results.append(results)
        return results
    
    def check_conversation_logged(self, date_str=None):
        """Verify conversation was logged for a given date"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        conv_dir = Path("/root/.openclaw/workspace/memory/conversations")
        pattern = f"{date_str}*.md"
        
        matching_files = list(conv_dir.glob(pattern))
        
        return {
            'date': date_str,
            'logged': len(matching_files) > 0,
            'files': [f.name for f in matching_files]
        }
    
    def check_memory_updated(self, hours=1):
        """Check if MEMORY.md was updated recently"""
        if not Path("/root/.openclaw/workspace/MEMORY.md").exists():
            return {'exists': False, 'recently_updated': False}
        
        mtime = Path("/root/.openclaw/workspace/MEMORY.md").stat().st_mtime
        age_hours = (datetime.now().timestamp() - mtime) / 3600
        
        return {
            'exists': True,
            'recently_updated': age_hours <= hours,
            'hours_since_update': age_hours
        }
    
    def validate_trading_bot(self):
        """Check if trading bot is running properly"""
        import subprocess
        
        result = subprocess.run(
            ["ps", "aux"], 
            capture_output=True, 
            text=True
        )
        
        alpaca_running = 'alpaca_vwap_trader' in result.stdout
        
        return {
            'alpaca_trader_running': alpaca_running,
            'status': 'healthy' if alpaca_running else 'stopped'
        }
    
    def run_daily_checks(self):
        """Run all daily validation checks"""
        checks = {
            'timestamp': datetime.now().isoformat(),
            'conversation_logged': self.check_conversation_logged(),
            'memory_updated': self.check_memory_updated(hours=24),
            'trading_bot': self.validate_trading_bot(),
            'overall_status': 'PASS'
        }
        
        # Determine overall status
        if not checks['conversation_logged']['logged']:
            checks['overall_status'] = 'FAIL'
        elif not checks['memory_updated']['recently_updated']:
            checks['overall_status'] = 'WARN'
        
        # Save to log
        self._save_check(checks)
        
        return checks
    
    def _save_check(self, check_result):
        """Save check result to log file"""
        logs = []
        if self.validation_log.exists():
            with open(self.validation_log, 'r') as f:
                try:
                    logs = json.load(f)
                except:
                    logs = []
        
        logs.append(check_result)
        
        # Keep only last 30 days
        logs = logs[-30:]
        
        with open(self.validation_log, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def generate_report(self):
        """Generate validation report"""
        if not self.validation_log.exists():
            return "No validation history found."
        
        with open(self.validation_log, 'r') as f:
            logs = json.load(f)
        
        report = "# Agent Validation Report\n\n"
        report += f"Last 7 days of checks:\n\n"
        
        for log in logs[-7:]:
            date = log['timestamp'][:10]
            status = log['overall_status']
            emoji = '✅' if status == 'PASS' else '⚠️' if status == 'WARN' else '❌'
            report += f"{emoji} {date}: {status}\n"
            report += f"   - Conversations: {'✓' if log['conversation_logged']['logged'] else '✗'}\n"
            report += f"   - Memory: {'✓' if log['memory_updated']['recently_updated'] else '✗'}\n"
            report += f"   - Trading Bot: {'✓' if log['trading_bot']['alpaca_trader_running'] else '✗'}\n\n"
        
        return report

if __name__ == "__main__":
    validator = AgentValidator()
    
    print("Running daily validation checks...")
    results = validator.run_daily_checks()
    
    print(f"\nOverall Status: {results['overall_status']}")
    print(f"Conversation Logged: {results['conversation_logged']['logged']}")
    print(f"Memory Updated (24h): {results['memory_updated']['recently_updated']}")
    print(f"Trading Bot Running: {results['trading_bot']['alpaca_trader_running']}")
