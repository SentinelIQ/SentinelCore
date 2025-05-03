from rest_framework import serializers
from notifications.models import NotificationChannel
from companies.serializers import CompanySerializer

class NotificationChannelSerializer(serializers.ModelSerializer):
    """
    Base serializer for NotificationChannel model.
    """
    company_data = CompanySerializer(source='company', read_only=True)
    
    class Meta:
        model = NotificationChannel
        fields = [
            'id', 'name', 'channel_type', 'is_enabled', 
            'config', 'company', 'company_data',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        """
        Dispatch to the appropriate validator based on channel type.
        """
        channel_type = data.get('channel_type')
        config = data.get('config', {})
        
        if channel_type == 'email':
            self._validate_email_config(config)
        elif channel_type == 'slack':
            self._validate_slack_config(config)
        elif channel_type == 'mattermost':
            self._validate_mattermost_config(config)
        elif channel_type == 'webhook':
            self._validate_webhook_config(config)
        elif channel_type == 'sms':
            self._validate_sms_config(config)
            
        return data
    
    def _validate_email_config(self, config):
        """
        Validate email (SMTP) channel configuration.
        """
        required_fields = ['smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 'from_email']
        
        for field in required_fields:
            if field not in config:
                raise serializers.ValidationError(
                    {"config": f"Email configuration requires '{field}' field"}
                )
                
        # Validate port is numeric
        try:
            port = int(config['smtp_port'])
            if port < 1 or port > 65535:
                raise serializers.ValidationError(
                    {"config": "SMTP port must be between 1 and 65535"}
                )
        except (ValueError, TypeError):
            raise serializers.ValidationError(
                {"config": "SMTP port must be a valid number"}
            )
            
        # Validate email format
        if '@' not in config['from_email']:
            raise serializers.ValidationError(
                {"config": "From email must be a valid email address"}
            )
            
    def _validate_slack_config(self, config):
        """
        Validate Slack channel configuration.
        """
        if 'webhook_url' not in config:
            raise serializers.ValidationError(
                {"config": "Slack configuration requires 'webhook_url' field"}
            )
            
        # Validate webhook URL format
        webhook_url = config['webhook_url']
        if not webhook_url.startswith('https://hooks.slack.com/'):
            raise serializers.ValidationError(
                {"config": "Slack webhook URL must be a valid Slack webhook URL"}
            )
            
    def _validate_mattermost_config(self, config):
        """
        Validate Mattermost channel configuration.
        """
        if 'webhook_url' not in config:
            raise serializers.ValidationError(
                {"config": "Mattermost configuration requires 'webhook_url' field"}
            )
            
        # Validate webhook URL format
        webhook_url = config['webhook_url']
        if not webhook_url.startswith('http'):
            raise serializers.ValidationError(
                {"config": "Mattermost webhook URL must be a valid HTTP/HTTPS URL"}
            )
            
        # Other optional fields
        if 'channel' in config and not isinstance(config['channel'], str):
            raise serializers.ValidationError(
                {"config": "Mattermost channel must be a string"}
            )
            
    def _validate_webhook_config(self, config):
        """
        Validate generic webhook channel configuration.
        """
        if 'url' not in config:
            raise serializers.ValidationError(
                {"config": "Webhook configuration requires 'url' field"}
            )
            
        # Validate URL format
        url = config['url']
        if not url.startswith('http'):
            raise serializers.ValidationError(
                {"config": "Webhook URL must be a valid HTTP/HTTPS URL"}
            )
            
        # Validate headers format if provided
        if 'headers' in config and not isinstance(config['headers'], dict):
            raise serializers.ValidationError(
                {"config": "Webhook headers must be a dictionary"}
            )
            
    def _validate_sms_config(self, config):
        """
        Validate SMS channel configuration.
        """
        required_fields = ['provider', 'api_key']
        
        for field in required_fields:
            if field not in config:
                raise serializers.ValidationError(
                    {"config": f"SMS configuration requires '{field}' field"}
                )
                
        # Validate provider is supported
        supported_providers = ['twilio', 'nexmo', 'aws_sns']
        if config['provider'] not in supported_providers:
            raise serializers.ValidationError(
                {"config": f"SMS provider must be one of: {', '.join(supported_providers)}"}
            )
            
        # Validate Twilio specific fields
        if config['provider'] == 'twilio':
            if 'account_sid' not in config:
                raise serializers.ValidationError(
                    {"config": "Twilio configuration requires 'account_sid' field"}
                )
            if 'from_number' not in config:
                raise serializers.ValidationError(
                    {"config": "Twilio configuration requires 'from_number' field"}
                )


class EmailChannelSerializer(NotificationChannelSerializer):
    """
    Specialized serializer for Email notification channels.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['channel_type'].initial = 'email'
        self.fields['channel_type'].read_only = True
        
    def to_representation(self, instance):
        """Customize the representation to include email-specific info"""
        data = super().to_representation(instance)
        if 'config' in data and data['config']:
            config = data['config']
            data['smtp_details'] = {
                'host': config.get('smtp_host', ''),
                'port': config.get('smtp_port', ''),
                'username': config.get('smtp_username', ''),
                'from_email': config.get('from_email', '')
            }
        return data


class SlackChannelSerializer(NotificationChannelSerializer):
    """
    Specialized serializer for Slack notification channels.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['channel_type'].initial = 'slack'
        self.fields['channel_type'].read_only = True
        
    def to_representation(self, instance):
        """Customize the representation to include Slack-specific info"""
        data = super().to_representation(instance)
        if 'config' in data and data['config']:
            config = data['config']
            data['slack_details'] = {
                'webhook_url': config.get('webhook_url', ''),
                'username': config.get('username', ''),
                'icon_emoji': config.get('icon_emoji', '')
            }
        return data


class MattermostChannelSerializer(NotificationChannelSerializer):
    """
    Specialized serializer for Mattermost notification channels.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['channel_type'].initial = 'mattermost'
        self.fields['channel_type'].read_only = True
        
    def to_representation(self, instance):
        """Customize the representation to include Mattermost-specific info"""
        data = super().to_representation(instance)
        if 'config' in data and data['config']:
            config = data['config']
            data['mattermost_details'] = {
                'webhook_url': config.get('webhook_url', ''),
                'username': config.get('username', ''),
                'channel': config.get('channel', ''),
                'icon_url': config.get('icon_url', '')
            }
        return data


class WebhookChannelSerializer(NotificationChannelSerializer):
    """
    Specialized serializer for webhook notification channels.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['channel_type'].initial = 'webhook'
        self.fields['channel_type'].read_only = True
        
    def to_representation(self, instance):
        """Customize the representation to include webhook-specific info"""
        data = super().to_representation(instance)
        if 'config' in data and data['config']:
            config = data['config']
            data['webhook_details'] = {
                'url': config.get('url', ''),
                'include_company': config.get('include_company', False)
            }
            if 'headers' in config:
                data['webhook_details']['headers'] = config.get('headers', {})
        return data


class SMSChannelSerializer(NotificationChannelSerializer):
    """
    Specialized serializer for SMS notification channels.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['channel_type'].initial = 'sms'
        self.fields['channel_type'].read_only = True
        
    def to_representation(self, instance):
        """Customize the representation to include SMS-specific info"""
        data = super().to_representation(instance)
        if 'config' in data and data['config']:
            config = data['config']
            data['sms_details'] = {
                'provider': config.get('provider', ''),
                'from_number': config.get('from_number', '')
            }
        return data

class NotificationChannelLiteSerializer(serializers.ModelSerializer):
    """Lite serializer for notification channels, used in listings and references"""
    
    class Meta:
        model = NotificationChannel
        fields = [
            'id', 'name', 'channel_type', 'is_enabled'
        ]
        read_only_fields = ['id'] 