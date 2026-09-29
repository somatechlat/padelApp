from rest_framework import serializers

from apps.courts.models import Court, PromoBanner, Venue


class ClubInfoSerializer(serializers.ModelSerializer):
    """Public club payload: contact, maps, bank, logo and resolved i18n titles."""

    home_section_title = serializers.SerializerMethodField()
    home_greeting_tagline = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Venue
        fields = [
            "id",
            "name",
            "address",
            "maps_query",
            "maps_url",
            "phone",
            "email",
            "whatsapp_number",
            "whatsapp_message",
            "instagram_url",
            "logo_url",
            "home_section_title",
            "home_greeting_tagline",
            "home_section_title_i18n",
            "home_greeting_tagline_i18n",
            "bank_name",
            "bank_account_number",
            "bank_account_holder",
            "bank_account_code",
            "bank_extra",
            "timezone",
            "currency",
        ]
        read_only_fields = fields

    def _lang(self):
        return self.context.get("lang")

    def get_home_section_title(self, obj):
        return obj.home_section_title_for(self._lang())

    def get_home_greeting_tagline(self, obj):
        return obj.home_greeting_tagline_for(self._lang())

    def get_logo_url(self, obj):
        return obj.logo_url(self.context.get("request"))


class PromoBannerSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    subtitle = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PromoBanner
        fields = [
            "id",
            "title",
            "subtitle",
            "title_i18n",
            "subtitle_i18n",
            "image",
            "image_url",
            "link_url",
            "link_type",
            "sort_order",
            "starts_at",
            "ends_at",
        ]
        read_only_fields = fields

    def _lang(self):
        return self.context.get("lang")

    def get_title(self, obj):
        return obj.title_for(self._lang())

    def get_subtitle(self, obj):
        return obj.subtitle_for(self._lang())

    def get_image_url(self, obj):
        return obj.image_url(self.context.get("request"))


class CourtSerializer(serializers.ModelSerializer):
    venue = serializers.PrimaryKeyRelatedField(queryset=Venue.objects.all())

    class Meta:
        model = Court
        fields = [
            "id",
            "venue",
            "name",
            "description",
            "court_type",
            "has_lighting",
            "price_base",
            "image",
            "status",
        ]
        read_only_fields = ["id"]


class TimeSlotSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    start = serializers.TimeField()
    end = serializers.TimeField()
    status = serializers.CharField()
