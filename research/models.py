from django.db import models


class SavedQuery(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    query_definition = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    result_count = models.IntegerField(null=True)

    class Meta:
        verbose_name_plural = 'Saved queries'

    def __str__(self):
        return self.name


class CohortDefinition(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    criteria = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    patient_count = models.IntegerField(null=True)
    encounter_count = models.IntegerField(null=True)

    def __str__(self):
        return self.name


class CohortMember(models.Model):
    cohort = models.ForeignKey(CohortDefinition, on_delete=models.CASCADE, related_name='members')
    patient_id = models.IntegerField()  # References DuckDB patient.id
    encounter_id = models.IntegerField(null=True, blank=True)  # References DuckDB encounter.id
    group_label = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = [('cohort', 'patient_id', 'encounter_id')]

    def __str__(self):
        return f"CohortMember {self.cohort.name} - Patient {self.patient_id}"
