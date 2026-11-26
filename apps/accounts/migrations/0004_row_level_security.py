from django.db import migrations

FORWARD = """
CREATE FUNCTION app_member_organisations() RETURNS SETOF uuid LANGUAGE sql STABLE AS
$$ SELECT organisation_id FROM accounts_membership
   WHERE user_id = app_current_user() AND is_active $$;

ALTER TABLE accounts_membership ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts_membership FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON accounts_membership
    USING (app_is_system() OR organisation_id = app_current_organisation())
    WITH CHECK (app_is_system() OR organisation_id = app_current_organisation());
CREATE POLICY member_read ON accounts_membership FOR SELECT
    USING (user_id = app_current_user());

CREATE POLICY member_read ON tenancy_organisation FOR SELECT
    USING (id IN (SELECT app_member_organisations()));

CREATE POLICY member_read ON tenancy_campus FOR SELECT
    USING (organisation_id IN (SELECT app_member_organisations()));
"""

BACKWARD = """
DROP POLICY member_read ON tenancy_campus;
DROP POLICY member_read ON tenancy_organisation;

DROP POLICY member_read ON accounts_membership;
DROP POLICY tenant_isolation ON accounts_membership;
ALTER TABLE accounts_membership NO FORCE ROW LEVEL SECURITY;
ALTER TABLE accounts_membership DISABLE ROW LEVEL SECURITY;

DROP FUNCTION app_member_organisations();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_tenant_managers"),
        ("tenancy", "0003_row_level_security"),
    ]

    operations = [
        migrations.RunSQL(FORWARD, BACKWARD),
    ]
