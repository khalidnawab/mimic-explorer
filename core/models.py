from django.db import models
from django.utils import timezone


class SystemConfig(models.Model):
    """Singleton settings model for app state. Named SystemConfig to avoid collision with Django's AppConfig."""
    mimic_data_path = models.CharField(max_length=500, blank=True)
    import_status = models.CharField(max_length=20, choices=[
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='not_started')
    import_progress = models.JSONField(default=dict)
    imported_modules = models.JSONField(default=list)
    total_patients = models.IntegerField(default=0)
    total_encounters = models.IntegerField(default=0)
    import_started_at = models.DateTimeField(null=True, blank=True)
    import_completed_at = models.DateTimeField(null=True, blank=True)
    mimic_version = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = 'System Configuration'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"SystemConfig (import: {self.import_status})"
