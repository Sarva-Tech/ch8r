import pytest
from unittest.mock import Mock, patch
from core.services.template_loader import TemplateLoader


class TestIntentClassificationUpdates:
    """Test the updated intent classification and response templates"""

    def test_feature_support_classified_as_feature_request(self):
        """Test that feature support questions are classified as feature_request"""
        # Mock context for feature support question
        context = {
            'role': 'Customer Support Agent',
            'product_name': 'ch8r',
            'behavior': 'Helpful and informative',
            'tone': 'Professional',
            'conversation_history': [],
            'kb_context': 'ch8r currently supports Google Gemini as the AI provider.',
            'tools': [{'function': {'name': 'list_tickets'}, 'function': {'name': 'list_pull_requests'}}],
            'integration_context': ''
        }
        
        # Render the intent classification template
        template_content = TemplateLoader.render_template('prompts/intent_classification.j2', context)
        
        # Verify the template includes feature_request definition for support questions
        assert 'feature_request' in template_content
        assert 'is X supported?' in template_content
        assert 'do you support Y?' in template_content
        assert 'Feature Support Inquiries' in template_content
        assert 'ALWAYS call tools' in template_content

    def test_final_response_includes_scenario_logic(self):
        """Test that final response template includes scenario-based response logic"""
        context = {
            'role': 'Customer Support Agent',
            'product_name': 'ch8r',
            'behavior': 'Helpful and informative',
            'tone': 'Professional',
            'response_style': 'balanced',
            'intent': 'feature_request',
            'reasoning': 'User is asking about Grok support',
            'kb_context': 'ch8r currently supports Google Gemini as the AI provider.',
            'tool_results': []
        }
        
        # Render the final response template
        template_content = TemplateLoader.render_template('prompts/final_response.j2', context)
        
        # Verify the template includes scenario-based response logic
        assert 'SCENARIO-BASED RESPONSE LOGIC' in template_content
        assert 'Feature Support Response Pattern' in template_content
        
        # For feature_request intent, only feature support patterns should be visible
        # Bug report patterns should be inside conditional blocks that aren't rendered
        assert 'Bug Report Response Pattern' not in template_content  # Should not be rendered for feature_request
        assert 'Feedback Response Pattern' not in template_content  # Should not be rendered for feature_request
        
        # Verify feature support scenarios
        assert 'Supported' in template_content
        assert 'Not Supported, No Ticket' in template_content
        assert 'Not Supported, Has Ticket' in template_content
        assert 'Not Supported, Has Pull Request' in template_content

    def test_feature_support_response_patterns(self):
        """Test specific response patterns for feature support scenarios"""
        context = {
            'role': 'Customer Support Agent',
            'product_name': 'ch8r',
            'behavior': 'Helpful and informative',
            'tone': 'Professional',
            'response_style': 'balanced',
            'intent': 'feature_request',
            'reasoning': 'User is asking about Grok support',
            'kb_context': 'ch8r currently supports Google Gemini as the AI provider.',
            'tool_results': []
        }
        
        template_content = TemplateLoader.render_template('prompts/final_response.j2', context)
        
        # Verify specific response patterns (the template variables should be rendered as empty strings since they're not provided)
        assert 'Hello,  is supported as a .' in template_content
        assert 'Hello,  is not yet supported as a .' in template_content
        assert 'Would you like to submit a feature request for  support' in template_content
        assert 'there is an existing ticket created for .' in template_content
        assert 'the  support is in progress' in template_content

    def test_bug_report_response_patterns(self):
        """Test specific response patterns for bug report scenarios"""
        context = {
            'role': 'Customer Support Agent',
            'product_name': 'ch8r',
            'behavior': 'Helpful and informative',
            'tone': 'Professional',
            'response_style': 'balanced',
            'intent': 'bug_report',
            'reasoning': 'User is reporting a bug',
            'kb_context': '',
            'tool_results': []
        }
        
        template_content = TemplateLoader.render_template('prompts/final_response.j2', context)
        
        # Verify the template includes scenario-based response logic
        assert 'SCENARIO-BASED RESPONSE LOGIC' in template_content
        assert 'Bug Report Response Pattern' in template_content
        
        # For bug_report intent, only bug report patterns should be visible
        assert 'Feature Support Response Pattern' not in template_content  # Should not be rendered for bug_report
        assert 'Feedback Response Pattern' not in template_content  # Should not be rendered for bug_report
        
        # Verify bug report response patterns
        assert 'we apologize for the inconvenience caused' in template_content
        assert 'this seems to be a new bug' in template_content
        assert 'Would you like to report it' in template_content
        assert 'there seems to be a ticket for this bug' in template_content
        assert 'the fix is being worked on' in template_content
