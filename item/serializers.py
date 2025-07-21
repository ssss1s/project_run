from rest_framework import serializers
from item.models import CollectibleItem


class CollectibleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectibleItem
        fields = '__all__'


