from rest_framework import serializers


class DateRangeFilterSerializer(serializers.Serializer):
    """
    Serializer for filtering dashboard metrics by date range.
    """
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    days = serializers.IntegerField(required=False, default=30, min_value=1, max_value=365)
    
    def validate(self, data):
        """
        Validate that if both start_date and end_date are provided, the range is valid.
        """
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("End date must be after start date")
            
        return data 