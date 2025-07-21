# item/serializers.py
from rest_framework import serializers
from .models import CollectibleItem
from .schemas import VALID_ITEM_TYPES  # Теперь этот импорт должен работать


class CollectibleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectibleItem
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Преобразуем строки в числа для координат
        representation['latitude'] = float(instance.latitude) if instance.latitude else None
        representation['longitude'] = float(instance.longitude) if instance.longitude else None
        return representation