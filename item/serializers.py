from rest_framework import serializers
from item.models import CollectibleItem


class CollectibleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectibleItem
        fields = ['name','uid', 'latitude', 'longitude', 'picture', 'value']




