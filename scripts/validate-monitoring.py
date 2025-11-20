#!/usr/bin/env python3
"""
Validate Crypto Viz Monitoring Configuration
"""

import os
import sys
from pathlib import Path

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def check_files():
    """Check if all configuration files exist"""
    print(f"{BLUE}=== Checking Configuration Files ==={NC}")

    files = [
        "monitoring/docker-compose.monitoring.yml",
        "monitoring/prometheus/prometheus.yml",
        "monitoring/prometheus/alerts.yml",
        "monitoring/prometheus/alertmanager.yml",
        "monitoring/loki/loki-config.yml",
        "monitoring/loki/promtail-config.yml",
        "monitoring/grafana/provisioning/datasources/datasources.yml",
        "monitoring/grafana/provisioning/dashboards/dashboards.yml",
        "monitoring/grafana/dashboards/crypto-viz-overview.json",
    ]

    all_exist = True
    for file in files:
        if Path(file).exists():
            print(f"{GREEN}✓{NC} {file}")
        else:
            print(f"{RED}✗{NC} {file} - Missing!")
            all_exist = False

    return all_exist

def check_scripts():
    """Check if all scripts exist and are executable"""
    print(f"\n{BLUE}=== Checking Scripts ==={NC}")

    scripts = [
        "scripts/health-check.sh",
        "scripts/monitoring-dashboard.sh",
        "scripts/start-monitoring.sh",
        "scripts/validate-monitoring.sh",
    ]

    all_ok = True
    for script in scripts:
        path = Path(script)
        if path.exists():
            if os.access(path, os.X_OK):
                print(f"{GREEN}✓{NC} {script} (executable)")
            else:
                print(f"{YELLOW}⚠{NC} {script} (not executable)")
                try:
                    path.chmod(0o755)
                    print(f"{GREEN}✓{NC} {script} (fixed)")
                except:
                    pass
        else:
            print(f"{RED}✗{NC} {script} - Missing!")
            all_ok = False

    return all_ok

def check_directories():
    """Check if all required directories exist"""
    print(f"\n{BLUE}=== Checking Required Directories ==={NC}")

    dirs = [
        "monitoring/prometheus",
        "monitoring/grafana/provisioning/datasources",
        "monitoring/grafana/provisioning/dashboards",
        "monitoring/grafana/dashboards",
        "monitoring/loki",
    ]

    all_exist = True
    for dir_path in dirs:
        if Path(dir_path).is_dir():
            print(f"{GREEN}✓{NC} {dir_path}")
        else:
            print(f"{RED}✗{NC} {dir_path} - Missing!")
            all_exist = False

    return all_exist

def check_documentation():
    """Check if documentation exists"""
    print(f"\n{BLUE}=== Checking Documentation ==={NC}")

    docs = [
        "monitoring/README.md",
        "monitoring/QUICK_START.md",
        "MONITORING_SETUP.md",
    ]

    all_exist = True
    for doc in docs:
        if Path(doc).exists():
            print(f"{GREEN}✓{NC} {doc}")
        else:
            print(f"{YELLOW}⚠{NC} {doc} - Missing (optional)")

    return True

def main():
    print(f"{BLUE}")
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║     Validating Monitoring Configuration                       ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print(f"{NC}\n")

    # Run all checks
    checks = [
        check_files(),
        check_scripts(),
        check_directories(),
        check_documentation(),
    ]

    # Summary
    print("\n╔════════════════════════════════════════════════════════════════╗")
    if all(checks):
        print(f"║ {GREEN}✓ Validation PASSED{NC}                                           ║")
        print("║                                                                ║")
        print("║ All monitoring configuration files are in place!               ║")
        print("║                                                                ║")
        print("║ Next steps:                                                    ║")
        print("║ 1. Start monitoring: ./scripts/start-monitoring.sh            ║")
        print("║ 2. Access Grafana:   http://localhost:3001 (admin/admin)      ║")
        print("║ 3. CLI Dashboard:    ./scripts/monitoring-dashboard.sh        ║")
        print("╚════════════════════════════════════════════════════════════════╝")
        return 0
    else:
        print(f"║ {RED}✗ Validation FAILED{NC}                                           ║")
        print("║                                                                ║")
        print("║ Some configuration files are missing or invalid.               ║")
        print("║ Please check the errors above.                                 ║")
        print("╚════════════════════════════════════════════════════════════════╝")
        return 1

if __name__ == "__main__":
    sys.exit(main())
