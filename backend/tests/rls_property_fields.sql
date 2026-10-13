-- Integration test for the real PostgreSQL RLS policies and composite FK.
-- Run ONLY against a disposable Supabase-compatible test database after
-- migrations 001-006 have been applied:
--   psql "$SUPABASE_TEST_DATABASE_URL" -v ON_ERROR_STOP=1 \
--     -f backend/tests/rls_property_fields.sql
-- All fixture data and temporary grants are rolled back at the end.

BEGIN;

GRANT SELECT, INSERT, UPDATE, DELETE
  ON TABLE public.property_fields
  TO anon, authenticated;

INSERT INTO auth.users (id, aud, role, email, raw_app_meta_data, raw_user_meta_data)
VALUES
  ('10000000-0000-4000-8000-000000000001', 'authenticated', 'authenticated', 'rls-a@example.invalid', '{"provider":"email","providers":["email"]}', '{}'),
  ('10000000-0000-4000-8000-000000000002', 'authenticated', 'authenticated', 'rls-b@example.invalid', '{"provider":"email","providers":["email"]}', '{}')
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.users (id, email)
VALUES
  ('10000000-0000-4000-8000-000000000001', 'rls-a@example.invalid'),
  ('10000000-0000-4000-8000-000000000002', 'rls-b@example.invalid')
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.organizations (id, name, tier)
VALUES
  ('20000000-0000-4000-8000-000000000001', 'RLS test organization A', 'starter'),
  ('20000000-0000-4000-8000-000000000002', 'RLS test organization B', 'starter')
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.organization_memberships (organization_id, user_id, role)
VALUES
  ('20000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000001', 'admin'),
  ('20000000-0000-4000-8000-000000000002', '10000000-0000-4000-8000-000000000002', 'admin')
ON CONFLICT (organization_id, user_id) DO NOTHING;

INSERT INTO public.properties (id, organization_id, address)
VALUES
  ('30000000-0000-4000-8000-000000000001', '20000000-0000-4000-8000-000000000001', 'RLS test property A'),
  ('30000000-0000-4000-8000-000000000002', '20000000-0000-4000-8000-000000000002', 'RLS test property B')
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.property_fields (id, organization_id, property_id, field_name, value, classification)
VALUES
  ('40000000-0000-4000-8000-000000000002', '20000000-0000-4000-8000-000000000002', '30000000-0000-4000-8000-000000000002', 'rls-fixture', '"unchanged"', 'SOURCE_DATA')
ON CONFLICT (id) DO NOTHING;

DO $$
DECLARE
  field_policy_count INTEGER;
BEGIN
  SELECT count(*) INTO field_policy_count
  FROM pg_policies
  WHERE schemaname = 'public'
    AND tablename = 'property_fields';
  IF field_policy_count <> 4 THEN
    RAISE EXCEPTION 'Expected exactly four reconciled property_fields policies; found %', field_policy_count;
  END IF;
  IF EXISTS (
    SELECT 1
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'property_fields'
      AND (permissive <> 'PERMISSIVE' OR roles::text <> '{authenticated}')
  ) THEN
    RAISE EXCEPTION 'property_fields policies must be permissive only for authenticated members';
  END IF;
END
$$;

SET LOCAL ROLE authenticated;
SET LOCAL request.jwt.claim.sub = '10000000-0000-4000-8000-000000000001';
SET LOCAL request.jwt.claim.role = 'authenticated';
SET LOCAL request.jwt.claims = '{"sub":"10000000-0000-4000-8000-000000000001","role":"authenticated","aud":"authenticated"}';

DO $$
DECLARE
  visible_count BIGINT;
  changed_count BIGINT;
  rejection_observed BOOLEAN;
BEGIN
  SELECT count(*) INTO visible_count
  FROM public.property_fields
  WHERE id = '40000000-0000-4000-8000-000000000002';
  IF visible_count <> 0 THEN
    RAISE EXCEPTION 'Organization A could read organization B property fields';
  END IF;

  UPDATE public.property_fields
    SET value = '"tampered"'
    WHERE id = '40000000-0000-4000-8000-000000000002';
  GET DIAGNOSTICS changed_count = ROW_COUNT;
  IF changed_count <> 0 THEN
    RAISE EXCEPTION 'Organization A modified organization B property fields';
  END IF;

  DELETE FROM public.property_fields
    WHERE id = '40000000-0000-4000-8000-000000000002';
  GET DIAGNOSTICS changed_count = ROW_COUNT;
  IF changed_count <> 0 THEN
    RAISE EXCEPTION 'Organization A deleted organization B property fields';
  END IF;

  -- A is a member of organization A, but the property belongs to B. The
  -- composite FK must reject the otherwise member-scoped insert.
  rejection_observed := FALSE;
  BEGIN
    INSERT INTO public.property_fields (organization_id, property_id, field_name, value, classification)
    VALUES ('20000000-0000-4000-8000-000000000001', '30000000-0000-4000-8000-000000000002', 'cross-org-property', '"bad"', 'USER_INPUT');
  EXCEPTION WHEN foreign_key_violation THEN
    rejection_observed := TRUE;
  END;
  IF NOT rejection_observed THEN
    RAISE EXCEPTION 'Organization A inserted a field for organization B property';
  END IF;

  -- A has no membership in B; a mismatched organization_id must also fail
  -- the authenticated insert policy, independently of the composite FK.
  rejection_observed := FALSE;
  BEGIN
    INSERT INTO public.property_fields (organization_id, property_id, field_name, value, classification)
    VALUES ('20000000-0000-4000-8000-000000000002', '30000000-0000-4000-8000-000000000001', 'mismatched-org-id', '"bad"', 'USER_INPUT');
  EXCEPTION WHEN insufficient_privilege THEN
    rejection_observed := TRUE;
  END;
  IF NOT rejection_observed THEN
    RAISE EXCEPTION 'A mismatched organization_id was not rejected by RLS';
  END IF;

  INSERT INTO public.property_fields (organization_id, property_id, field_name, value, classification)
  VALUES ('20000000-0000-4000-8000-000000000001', '30000000-0000-4000-8000-000000000001', 'same-org-lifecycle', '"inserted"', 'USER_INPUT');

  SELECT count(*) INTO visible_count
  FROM public.property_fields
  WHERE organization_id = '20000000-0000-4000-8000-000000000001'
    AND property_id = '30000000-0000-4000-8000-000000000001'
    AND field_name = 'same-org-lifecycle';
  IF visible_count <> 1 THEN
    RAISE EXCEPTION 'Same-organization insert/read failed';
  END IF;

  UPDATE public.property_fields
    SET value = '"updated"'
    WHERE organization_id = '20000000-0000-4000-8000-000000000001'
      AND property_id = '30000000-0000-4000-8000-000000000001'
      AND field_name = 'same-org-lifecycle';
  GET DIAGNOSTICS changed_count = ROW_COUNT;
  IF changed_count <> 1 THEN
    RAISE EXCEPTION 'Same-organization update failed';
  END IF;

  DELETE FROM public.property_fields
    WHERE organization_id = '20000000-0000-4000-8000-000000000001'
      AND property_id = '30000000-0000-4000-8000-000000000001'
      AND field_name = 'same-org-lifecycle';
  GET DIAGNOSTICS changed_count = ROW_COUNT;
  IF changed_count <> 1 THEN
    RAISE EXCEPTION 'Same-organization delete failed';
  END IF;
END
$$;

RESET ROLE;
SET LOCAL ROLE anon;
SET LOCAL request.jwt.claim.sub = '';
SET LOCAL request.jwt.claim.role = 'anon';
SET LOCAL request.jwt.claims = '{"role":"anon","aud":"anon"}';

DO $$
DECLARE
  visible_count BIGINT;
  rejection_observed BOOLEAN := FALSE;
BEGIN
  SELECT count(*) INTO visible_count FROM public.property_fields;
  IF visible_count <> 0 THEN
    RAISE EXCEPTION 'Anonymous role could read property fields';
  END IF;

  BEGIN
    INSERT INTO public.property_fields (organization_id, property_id, field_name, value, classification)
    VALUES ('20000000-0000-4000-8000-000000000001', '30000000-0000-4000-8000-000000000001', 'anonymous-write', '"bad"', 'USER_INPUT');
  EXCEPTION WHEN insufficient_privilege THEN
    rejection_observed := TRUE;
  END;
  IF NOT rejection_observed THEN
    RAISE EXCEPTION 'Anonymous role could insert property fields';
  END IF;
END
$$;

RESET ROLE;
DO $$
DECLARE
  stored_value JSONB;
BEGIN
  SELECT value INTO stored_value
  FROM public.property_fields
  WHERE id = '40000000-0000-4000-8000-000000000002';
  IF stored_value IS DISTINCT FROM '"unchanged"'::jsonb THEN
    RAISE EXCEPTION 'Organization B fixture was changed by the organization A test';
  END IF;
END
$$;

ROLLBACK;
