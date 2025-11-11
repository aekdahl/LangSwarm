"""
Escalation Router for Human-in-the-Loop

Routes escalations to appropriate channels based on severity (S1-S4).
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from .models import EscalationPayload, Severity

logger = logging.getLogger(__name__)


class EscalationRouter:
    """
    Routes escalations to humans based on severity.
    
    Severity levels:
    - S1: Critical - halt execution, page on-call immediately
    - S2: High - alert immediately, can attempt replan once
    - S3: Medium - notify async, continue with replan
    - S4: Low - log for daily digest
    
    Integrates with:
    - Slack (via webhooks)
    - PagerDuty (via API)
    - Email
    - Logging system
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize escalation router with configuration.
        
        Args:
            config: Configuration dict with:
                - slack_webhook: Slack webhook URL
                - pagerduty_key: PagerDuty integration key
                - email_recipients: List of email addresses
                - oncall_team: Team name for paging
        """
        self.config = config
        self.notifiers = self._setup_notifiers()
        self.escalation_history = []
        self.halted_plans = set()
    
    async def escalate(self, payload: EscalationPayload) -> str:
        """
        Route escalation to appropriate channels based on severity.
        
        Args:
            payload: Complete escalation context
            
        Returns:
            Status string indicating what happened
        """
        logger.info(
            f"Escalating {payload.severity.value} for plan {payload.plan_id}: {payload.trigger}"
        )
        
        # Record escalation
        self.escalation_history.append({
            "plan_id": payload.plan_id,
            "severity": payload.severity.value,
            "trigger": payload.trigger,
            "timestamp": payload.created_at
        })
        
        if payload.severity == Severity.S1:
            # Critical: halt execution, page on-call
            await self._halt_execution(payload.plan_id)
            await self._page_oncall(payload)
            return "halted_awaiting_human"
        
        elif payload.severity == Severity.S2:
            # High: attempt replan once, alert immediately
            await self._alert_immediate(payload)
            return "alerted_can_replan_once"
        
        elif payload.severity == Severity.S3:
            # Medium: notify async, continue with replan
            await self._notify_async(payload)
            return "notified_continuing"
        
        elif payload.severity == Severity.S4:
            # Low: log for daily digest
            await self._log_digest(payload)
            return "logged"
        
        return "unknown_severity"
    
    def is_halted(self, plan_id: str) -> bool:
        """Check if plan execution is halted"""
        return plan_id in self.halted_plans
    
    def resume(self, plan_id: str) -> None:
        """Resume halted plan execution"""
        if plan_id in self.halted_plans:
            self.halted_plans.remove(plan_id)
            logger.info(f"Resumed plan {plan_id}")
    
    def _setup_notifiers(self) -> Dict[str, Any]:
        """Setup notification channels"""
        notifiers = {}
        
        # Slack notifier
        if "slack_webhook" in self.config:
            notifiers["slack"] = {
                "type": "slack",
                "webhook": self.config["slack_webhook"]
            }
        
        # PagerDuty notifier
        if "pagerduty_key" in self.config:
            notifiers["pagerduty"] = {
                "type": "pagerduty",
                "integration_key": self.config["pagerduty_key"]
            }
        
        # Email notifier
        if "email_recipients" in self.config:
            notifiers["email"] = {
                "type": "email",
                "recipients": self.config["email_recipients"]
            }
        
        return notifiers
    
    async def _halt_execution(self, plan_id: str) -> None:
        """
        Halt plan execution immediately.
        
        Marks plan as halted so coordinator will stop.
        """
        self.halted_plans.add(plan_id)
        logger.critical(f"HALTED plan execution: {plan_id}")
    
    async def _page_oncall(self, payload: EscalationPayload) -> None:
        """
        Page on-call team via PagerDuty.
        
        For S1 critical escalations.
        """
        if "pagerduty" in self.notifiers:
            logger.critical(
                f"🚨 PAGING ON-CALL for {payload.plan_id}: {payload.trigger}"
            )
            
            # In production, this would call PagerDuty API
            # For now, log the page
            page_data = {
                "severity": "critical",
                "plan_id": payload.plan_id,
                "trigger": payload.trigger,
                "step": payload.step,
                "proposed_fix": payload.proposed_fix,
                "links": payload.links
            }
            
            logger.critical(f"PagerDuty payload: {page_data}")
        else:
            logger.warning("PagerDuty not configured, cannot page on-call")
    
    async def _alert_immediate(self, payload: EscalationPayload) -> None:
        """
        Send immediate alert via Slack/Email.
        
        For S2 high priority escalations.
        """
        message = self._format_alert_message(payload)
        
        # Slack
        if "slack" in self.notifiers:
            logger.warning(f"📢 SLACK ALERT: {message}")
            # In production: POST to slack_webhook
        
        # Email
        if "email" in self.notifiers:
            logger.warning(f"📧 EMAIL ALERT to {self.notifiers['email']['recipients']}")
            # In production: Send email
    
    async def _notify_async(self, payload: EscalationPayload) -> None:
        """
        Send async notification via Slack.
        
        For S3 medium priority escalations.
        """
        message = self._format_notification_message(payload)
        
        if "slack" in self.notifiers:
            logger.info(f"💬 SLACK NOTIFICATION: {message}")
            # In production: POST to slack_webhook
        else:
            logger.info(f"Notification: {message}")
    
    async def _log_digest(self, payload: EscalationPayload) -> None:
        """
        Log for daily digest.
        
        For S4 low priority escalations.
        """
        logger.info(
            f"📝 DIGEST: Plan {payload.plan_id} - {payload.trigger} at step {payload.step}"
        )
    
    def _format_alert_message(self, payload: EscalationPayload) -> str:
        """Format immediate alert message"""
        return f"""
🚨 *{payload.severity.value} Escalation* - Plan {payload.plan_id}

*Trigger:* {payload.trigger}
*Step:* {payload.step}
*Observation:* {payload.observation.get('status', 'unknown')}

*Last Actions:*
{self._format_actions(payload.last_actions)}

*Proposed Fix:* {payload.proposed_fix or 'None'}

*Next Safe Actions:* {', '.join(payload.next_safe_actions)}

*Links:*
- Trace: {payload.links.get('trace', 'N/A')}
- Diff: {payload.links.get('diff', 'N/A')}
- Artifact: {payload.links.get('artifact_preview', 'N/A')}
"""
    
    def _format_notification_message(self, payload: EscalationPayload) -> str:
        """Format async notification message"""
        return f"""
ℹ️ Plan {payload.plan_id} - {payload.trigger}
Step: {payload.step}
Proposed: {payload.proposed_fix or 'Replanning'}
"""
    
    def _format_actions(self, actions: list) -> str:
        """Format action history"""
        if not actions:
            return "None"
        
        formatted = []
        for action in actions[-3:]:  # Last 3 actions
            formatted.append(
                f"  • {action.get('action', 'unknown')}: {action.get('result', 'unknown')}"
            )
        
        return "\n".join(formatted)




