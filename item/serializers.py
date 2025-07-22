
from rest_framework import serializers
from .models import CollectibleItem



class CollectibleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectibleItem
        fields =['id', 'uid', 'value', 'latitude', 'longitude', 'picture', 'value']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Преобразуем строки в числа для координат
        representation['latitude'] = float(instance.latitude) if instance.latitude else None
        representation['longitude'] = float(instance.longitude) if instance.longitude else None
        return representation
