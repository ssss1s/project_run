from rest_framework import serializers
from subscribe.models import Subscribe

class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribe
        fields = ['coach', 'athlete']