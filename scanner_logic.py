import socket
import requests

import ssl

def audit_ssl(target):
    host = clean_input(target)
    try:
        # We try to create a secure connection to the site
        context = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=3) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                # If we get here, the SSL certificate is VALID
                return "Valid SSL/TLS Certificate Found", 0
    except:
        # If the connection fails, the site is INSECURE
        return "CRITICAL: No SSL/TLS Certificate or Invalid Cert", 50
# 1. Configuration for the Scoring Algorithm
WEIGHTS = {
    "port_open": 15,       # Each open port adds 15 points
    "header_missing": 10,   # Each missing header adds 10 points
    "critical_port": 25     # Critical ports (21, 3306) add extra weight
}


REMEDIATION_TIPS = {
    21: "CRITICAL: Disable FTP. Use SFTP (Port 22).",
    22: "ADVICE: Secure SSH with Key-based auth.",
    80: "WARNING: Unencrypted HTTP. Install SSL.",
    443: "INFO: Service is encrypted.",
    3306: "DANGER: Database exposed. Block external access.",
    8080: "WARNING: Proxy/Dev port open.",
    "X-Frame-Options": "Missing: Vulnerable to Clickjacking.",
    "Content-Security-Policy": "Missing: Risk of XSS/Injection.",
    "Strict-Transport-Security": "Missing: HSTS not enforced.",
    "X-Content-Type-Options": "Missing: MIME-Sniffing risk.",
    "Referrer-Policy": "Missing: Information Leakage risk.",
    "X-XSS-Protection": "Missing: Legacy XSS filter off."
}

def clean_input(target):
    return target.strip().replace("http://", "").replace("https://", "").split('/')[0]

def calculate_grade(score):
    """Logic to convert numerical score to Letter Grade"""
    if score <= 10: return "A (Secure)"
    elif score <= 30: return "B (Good)"
    elif score <= 60: return "C (Vulnerable)"
    elif score <= 65: return "D (High Risk)"
    elif score <= 85: return "E (Critical)"
    else: return "F (Critical Danger)"

def scan_ports(target):
    host = clean_input(target)
    all_results = []
    total_risk_score = 0
    common_ports = [21, 22, 80, 443, 3306, 8080]
    
    for port in common_ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        try:
            result = sock.connect_ex((host, port))
            state = "open" if result == 0 else "closed"
            
            # Apply Scoring Logic
            if state == "open":
                total_risk_score += WEIGHTS["port_open"]
                if port in [21, 3306]: # Critical port penalty
                    total_risk_score += WEIGHTS["critical_port"]

            all_results.append({
                "port": port,
                "state": state,
                "risk": "High" if state == "open" and port in [21, 80, 3306] else "Low",
                "fix": REMEDIATION_TIPS.get(port, "Audit service.") if state == "open" else "No action needed."
            })
        except:
            continue
        finally:
            sock.close()
    return all_results, total_risk_score

def analyze_headers(target):
    host = clean_input(target)
    url = f"http://{host}"
    findings = []
    header_score = 0
    security_checks = ["X-Frame-Options", "Content-Security-Policy", "Strict-Transport-Security", 
                       "X-Content-Type-Options", "Referrer-Policy", "X-XSS-Protection"]
    
    try:
        response = requests.get(url, timeout=5, verify=False)
        for header in security_checks:
            if header not in response.headers:
                findings.append(REMEDIATION_TIPS.get(header))
                header_score += WEIGHTS["header_missing"]
    except:
        return ["Web Analysis Failed"], 50 # Default penalty for failed connection
    
    return findings, header_score

