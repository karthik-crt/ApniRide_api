from django.conf import settings

def getApiKey():
    from api.models import IntegrationSettings
    settings_obj = IntegrationSettings.objects.first()
    if settings_obj:
        return {
            "maps_api_key": settings_obj.maps_api_key,
            "sms_api_key": settings_obj.sms_api_key,
            "payment_api_key": settings_obj.payment_api_key
        }
    return {
        "maps_api_key": None,
        "sms_api_key": None,
        "payment_api_key": None
    }