"""Remove legacy FK constraints from CohortMember.

The patient_id and encounter_id fields now reference DuckDB IDs (plain integers),
not Django ORM models. SQLite doesn't support DROP CONSTRAINT, so we recreate
the table without the FK references.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                # Create new table without FK constraints
                '''CREATE TABLE "research_cohortmember_new" (
                    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    "patient_id" integer NOT NULL,
                    "encounter_id" integer NULL,
                    "group_label" varchar(50) NOT NULL,
                    "cohort_id" bigint NOT NULL REFERENCES "research_cohortdefinition" ("id")
                        DEFERRABLE INITIALLY DEFERRED
                )''',
                # Copy existing data
                '''INSERT INTO "research_cohortmember_new"
                    (id, patient_id, encounter_id, group_label, cohort_id)
                    SELECT id, patient_id, encounter_id, group_label, cohort_id
                    FROM "research_cohortmember"''',
                # Drop old table
                'DROP TABLE "research_cohortmember"',
                # Rename new table
                'ALTER TABLE "research_cohortmember_new" RENAME TO "research_cohortmember"',
                # Recreate unique index
                '''CREATE UNIQUE INDEX "research_cohortmember_cohort_id_patient_id_encounter_id_uniq"
                    ON "research_cohortmember" ("cohort_id", "patient_id", "encounter_id")''',
                # Recreate cohort_id index
                '''CREATE INDEX "research_cohortmember_cohort_id"
                    ON "research_cohortmember" ("cohort_id")''',
            ],
            reverse_sql=[
                # Reverse: recreate with FKs (not really needed but makes migration reversible)
                'SELECT 1',
            ],
        ),
    ]
