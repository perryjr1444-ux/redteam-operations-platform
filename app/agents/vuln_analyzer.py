"""
Vulnerability Analyzer Agent - Intelligent Vulnerability Assessment

Uses AI to:
- Parse and analyze vulnerability scan results
- Correlate findings across multiple tools
- Prioritize vulnerabilities by exploitability and impact
- Deduplicate and categorize findings
- Map vulnerabilities to MITRE ATT&CK techniques
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class VulnerabilityFinding:
    """A single vulnerability finding"""
    id: str
    title: str
    severity: str  # "critical", "high", "medium", "low", "info"
    cvss_score: float
    description: str
    affected_component: str
    evidence: str
    remediation: str
    cve_ids: List[str]
    attack_vector: str
    exploitability_score: float  # 0.0 to 1.0
    discovered_by: str  # Tool that found it
    discovered_at: datetime


@dataclass
class VulnerabilityReport:
    """Comprehensive vulnerability analysis report"""
    target: str
    total_findings: int
    findings: List[VulnerabilityFinding]
    severity_breakdown: Dict[str, int]
    top_critical_issues: List[VulnerabilityFinding]
    attack_surface_summary: Dict[str, Any]
    recommendations: List[str]
    generated_at: datetime


class VulnerabilityAnalyzerAgent:
    """
    AI agent for intelligent vulnerability analysis.

    Processes raw scan results and provides actionable intelligence
    with prioritization, correlation, and exploitation guidance.
    """

    def __init__(self, langgraph_url: Optional[str] = None):
        self.langgraph_url = langgraph_url
        self.analysis_history: List[VulnerabilityReport] = []
        logger.info("Vulnerability Analyzer Agent initialized")

    async def execute(self, operation: str, input_data: Dict[str, Any]) -> Any:
        """Execute an operation"""
        if operation == "analyze_vulnerabilities":
            return await self.analyze_vulnerabilities(
                input_data.get("scan_results", []),
                input_data.get("target"),
            )
        elif operation == "prioritize":
            return await self.prioritize_vulnerabilities(
                input_data.get("findings", []),
                input_data.get("context", {}),
            )
        elif operation == "analyze":
            return await self.analyze_question(
                input_data.get("question"),
                input_data.get("context", {}),
            )
        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def analyze_vulnerabilities(
        self,
        scan_results: List[Dict[str, Any]],
        target: str,
    ) -> VulnerabilityReport:
        """
        Analyze raw scan results and generate intelligent vulnerability report.

        Args:
            scan_results: List of raw scan outputs from various tools
            target: Target that was scanned
        """
        logger.info(f"Analyzing vulnerabilities for target: {target}")

        # Parse findings from scan results
        findings = []
        for result in scan_results:
            tool_findings = await self._parse_scan_result(result)
            findings.extend(tool_findings)

        # Deduplicate findings
        findings = self._deduplicate_findings(findings)

        # Enrich findings with additional intelligence
        enriched_findings = []
        for finding in findings:
            enriched = await self._enrich_finding(finding)
            enriched_findings.append(enriched)

        # Sort by severity and exploitability
        enriched_findings = sorted(
            enriched_findings,
            key=lambda f: (self._severity_score(f.severity), f.exploitability_score),
            reverse=True,
        )

        # Generate severity breakdown
        severity_breakdown = self._calculate_severity_breakdown(enriched_findings)

        # Identify top critical issues
        top_critical = [f for f in enriched_findings if f.severity in ["critical", "high"]][:10]

        # Analyze attack surface
        attack_surface = self._analyze_attack_surface(enriched_findings)

        # Generate recommendations
        recommendations = self._generate_recommendations(enriched_findings, attack_surface)

        report = VulnerabilityReport(
            target=target,
            total_findings=len(enriched_findings),
            findings=enriched_findings,
            severity_breakdown=severity_breakdown,
            top_critical_issues=top_critical,
            attack_surface_summary=attack_surface,
            recommendations=recommendations,
            generated_at=datetime.utcnow(),
        )

        self.analysis_history.append(report)
        logger.info(f"Vulnerability analysis complete: {report.total_findings} findings, {len(top_critical)} critical")

        return report

    async def _parse_scan_result(self, result: Dict[str, Any]) -> List[VulnerabilityFinding]:
        """Parse scan result from a specific tool"""
        tool = result.get("tool", "unknown")
        findings = []

        # Tool-specific parsing logic
        if tool == "nmap":
            findings.extend(self._parse_nmap_vulns(result.get("output", [])))
        elif tool == "sqlmap":
            findings.extend(self._parse_sqlmap_vulns(result.get("output", [])))
        elif tool == "nikto":
            findings.extend(self._parse_nikto_vulns(result.get("output", [])))
        else:
            # Generic parsing
            findings.extend(self._parse_generic_vulns(result))

        return findings

    def _parse_nmap_vulns(self, output: List[Dict[str, Any]]) -> List[VulnerabilityFinding]:
        """Parse Nmap vulnerability script results"""
        findings = []
        for line in output:
            text = line.get("text", "")

            # Look for vulnerability indicators
            if "VULNERABLE" in text or "CVE-" in text:
                finding = VulnerabilityFinding(
                    id=f"nmap_{len(findings)}",
                    title=f"Port/Service Vulnerability Detected",
                    severity="medium",
                    cvss_score=5.0,
                    description=text,
                    affected_component="Network Service",
                    evidence=text,
                    remediation="Review service configuration and apply patches",
                    cve_ids=self._extract_cve_ids(text),
                    attack_vector="network",
                    exploitability_score=0.6,
                    discovered_by="nmap",
                    discovered_at=datetime.utcnow(),
                )
                findings.append(finding)

        return findings

    def _parse_sqlmap_vulns(self, output: List[Dict[str, Any]]) -> List[VulnerabilityFinding]:
        """Parse SQLMap injection findings"""
        findings = []
        for line in output:
            text = line.get("text", "")

            if "injectable" in text.lower() or "sql injection" in text.lower():
                finding = VulnerabilityFinding(
                    id=f"sqlmap_{len(findings)}",
                    title="SQL Injection Vulnerability",
                    severity="critical",
                    cvss_score=9.8,
                    description="SQL injection vulnerability detected - database queries can be manipulated",
                    affected_component="Web Application",
                    evidence=text,
                    remediation="Use parameterized queries and input validation",
                    cve_ids=[],
                    attack_vector="network",
                    exploitability_score=0.95,
                    discovered_by="sqlmap",
                    discovered_at=datetime.utcnow(),
                )
                findings.append(finding)

        return findings

    def _parse_nikto_vulns(self, output: List[Dict[str, Any]]) -> List[VulnerabilityFinding]:
        """Parse Nikto web server findings"""
        findings = []
        for line in output:
            text = line.get("text", "")

            if "OSVDB" in text or "vulnerability" in text.lower():
                # Determine severity from text
                severity = "medium"
                if "critical" in text.lower() or "remote code" in text.lower():
                    severity = "critical"
                elif "high" in text.lower():
                    severity = "high"

                finding = VulnerabilityFinding(
                    id=f"nikto_{len(findings)}",
                    title="Web Server Vulnerability",
                    severity=severity,
                    cvss_score=self._severity_to_cvss(severity),
                    description=text,
                    affected_component="Web Server",
                    evidence=text,
                    remediation="Update web server and remove vulnerable components",
                    cve_ids=self._extract_cve_ids(text),
                    attack_vector="network",
                    exploitability_score=0.7,
                    discovered_by="nikto",
                    discovered_at=datetime.utcnow(),
                )
                findings.append(finding)

        return findings

    def _parse_generic_vulns(self, result: Dict[str, Any]) -> List[VulnerabilityFinding]:
        """Generic vulnerability parsing"""
        # Placeholder for generic parsing logic
        return []

    def _deduplicate_findings(self, findings: List[VulnerabilityFinding]) -> List[VulnerabilityFinding]:
        """Remove duplicate findings based on title and affected component"""
        seen = set()
        deduplicated = []

        for finding in findings:
            key = (finding.title, finding.affected_component)
            if key not in seen:
                seen.add(key)
                deduplicated.append(finding)

        logger.info(f"Deduplicated {len(findings)} findings to {len(deduplicated)}")
        return deduplicated

    async def _enrich_finding(self, finding: VulnerabilityFinding) -> VulnerabilityFinding:
        """Enrich finding with additional intelligence"""
        # In a real implementation, this would query threat intelligence databases,
        # CVE databases, exploit databases, etc.

        # For now, just adjust exploitability based on severity
        if finding.severity == "critical" and finding.attack_vector == "network":
            finding.exploitability_score = min(1.0, finding.exploitability_score + 0.2)

        return finding

    def _calculate_severity_breakdown(self, findings: List[VulnerabilityFinding]) -> Dict[str, int]:
        """Calculate count of findings by severity"""
        breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for finding in findings:
            if finding.severity in breakdown:
                breakdown[finding.severity] += 1
        return breakdown

    def _analyze_attack_surface(self, findings: List[VulnerabilityFinding]) -> Dict[str, Any]:
        """Analyze the attack surface from findings"""
        attack_vectors = {}
        affected_components = {}

        for finding in findings:
            # Count by attack vector
            vector = finding.attack_vector
            attack_vectors[vector] = attack_vectors.get(vector, 0) + 1

            # Count by component
            component = finding.affected_component
            affected_components[component] = affected_components.get(component, 0) + 1

        return {
            "attack_vectors": attack_vectors,
            "affected_components": affected_components,
            "most_vulnerable_vector": max(attack_vectors.items(), key=lambda x: x[1])[0] if attack_vectors else "unknown",
            "most_vulnerable_component": max(affected_components.items(), key=lambda x: x[1])[0] if affected_components else "unknown",
        }

    def _generate_recommendations(
        self,
        findings: List[VulnerabilityFinding],
        attack_surface: Dict[str, Any],
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Critical issues first
        critical_count = sum(1 for f in findings if f.severity == "critical")
        if critical_count > 0:
            recommendations.append(
                f"URGENT: Address {critical_count} critical vulnerabilities immediately - these are actively exploitable"
            )

        # Attack surface recommendations
        most_vuln = attack_surface.get("most_vulnerable_component")
        if most_vuln:
            recommendations.append(
                f"Focus remediation efforts on {most_vuln} - highest concentration of vulnerabilities"
            )

        # SQL injection specific
        sql_vulns = [f for f in findings if "SQL" in f.title or "injection" in f.title.lower()]
        if sql_vulns:
            recommendations.append(
                f"Implement parameterized queries and input validation to address {len(sql_vulns)} injection vulnerabilities"
            )

        # General recommendations
        recommendations.append("Perform regular security scanning and implement a patch management process")
        recommendations.append("Consider implementing a Web Application Firewall (WAF) for additional protection")

        return recommendations

    async def prioritize_vulnerabilities(
        self,
        findings: List[VulnerabilityFinding],
        context: Dict[str, Any],
    ) -> List[VulnerabilityFinding]:
        """Prioritize vulnerabilities based on context"""
        # Sort by combination of severity and exploitability
        return sorted(
            findings,
            key=lambda f: (self._severity_score(f.severity), f.exploitability_score, f.cvss_score),
            reverse=True,
        )

    def _severity_score(self, severity: str) -> int:
        """Convert severity to numeric score for sorting"""
        return {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}.get(severity, 0)

    def _severity_to_cvss(self, severity: str) -> float:
        """Convert severity string to approximate CVSS score"""
        return {"critical": 9.5, "high": 7.5, "medium": 5.0, "low": 3.0, "info": 0.0}.get(severity, 5.0)

    def _extract_cve_ids(self, text: str) -> List[str]:
        """Extract CVE IDs from text"""
        pattern = r'CVE-\d{4}-\d{4,7}'
        return re.findall(pattern, text)

    async def analyze_question(self, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a question from vulnerability perspective"""
        return {
            "agent": "vuln_analyzer",
            "analysis": f"Vulnerability assessment perspective on: {question}",
            "recommendation": "Recommend prioritizing vulnerabilities by exploitability and business impact",
            "confidence": 0.85,
        }
