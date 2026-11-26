from django.db import migrations

FORWARD = """
CREATE FUNCTION app_current_organisation() RETURNS uuid LANGUAGE sql STABLE AS
$$ SELECT NULLIF(current_setting('app.organisation_id', true), '')::uuid $$;

CREATE FUNCTION app_current_user() RETURNS uuid LANGUAGE sql STABLE AS
$$ SELECT NULLIF(current_setting('app.user_id', true), '')::uuid $$;

CREATE FUNCTION app_is_system() RETURNS boolean LANGUAGE sql STABLE AS
$$ SELECT COALESCE(current_setting('app.is_system', true), '') = 'on' $$;

ALTER TABLE tenancy_organisation ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenancy_organisation FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON tenancy_organisation
    USING (app_is_system() OR id = app_current_organisation())
    WITH CHECK (app_is_system() OR id = app_current_organisation());

ALTER TABLE tenancy_campus ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenancy_campus FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON tenancy_campus
    USING (app_is_system() OR organisation_id = app_current_organisation())
    WITH CHECK (app_is_system() OR organisation_id = app_current_organisation());
"""

BACKWARD = """
DROP POLICY tenant_isolation ON tenancy_campus;
ALTER TABLE tenancy_campus NO FORCE ROW LEVEL SECURITY;
ALTER TABLE tenancy_campus DISABLE ROW LEVEL SECURITY;

DROP POLICY tenant_isolation ON tenancy_organisation;
ALTER TABLE tenancy_organisation NO FORCE ROW LEVEL SECURITY;
ALTER TABLE tenancy_organisation DISABLE ROW LEVEL SECURITY;

DROP FUNCTION app_is_system();
DROP FUNCTION app_current_user();
DROP FUNCTION app_current_organisation();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("tenancy", "0002_tenant_managers"),
    ]

    operations = [
        migrations.RunSQL(FORWARD, BACKWARD),
    ]
