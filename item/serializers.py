from rest_framework import serializers
from decimal import Decimal
from item.models import CollectibleItem


class CollectibleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectibleItem
        fields = '__all__'
        extra_kwargs = {'uid': {'validators': []}}

