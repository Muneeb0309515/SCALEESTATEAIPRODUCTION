-- Forward-only hardening for property_fields tenant isolation.
-- Apply after 005_property_persistence.sql, only after reviewing the active
-- schema and migration ledger. This migration intentionally does not rewrite
-- property data: it aborts if existing field/property organization links do not
-- agree, so those records can be investigated rather than silently reassigned.

BEGIN;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM public.property_fields AS fields
    LEFT JOIN public.properties AS properties
      ON properties.id = fields.property_id
    WHERE properties.id IS NULL
       OR fields.organization_id IS NULL
       OR fields.organization_id IS DISTINCT FROM properties.organization_id
  ) THEN
    RAISE EXCEPTION
      'Cannot apply property_fields tenant-isolation migration: existing field/property organization links are inconsistent. Review and reconcile those rows separately before retrying.';
  END IF;
END
$$;

-- A composite FK needs a unique referenced key even though properties.id is
-- already the primary key.
ALTER TABLE public.properties
  ADD CONSTRAINT properties_id_organization_id_key
  UNIQUE (id, organization_id);

-- Replace the former property_id-only FK with a tenant-aware relationship.
ALTER TABLE public.property_fields
  DROP CONSTRAINT IF EXISTS property_fields_property_id_fkey;

ALTER TABLE public.property_fields
  ADD CONSTRAINT property_fields_property_org_fkey
  FOREIGN KEY (property_id, organization_id)
  REFERENCES public.properties (id, organization_id)
  ON DELETE CASCADE
  NOT VALID;

ALTER TABLE public.property_fields
  VALIDATE CONSTRAINT property_fields_property_org_fkey;

-- Membership rows have their own RLS. Use a narrowly-scoped SECURITY DEFINER
-- predicate to avoid recursive membership-policy evaluation on both fresh and
-- already-provisioned Supabase databases. The function reveals only whether
-- auth.uid() is a member of the requested organization.
CREATE OR REPLACE FUNCTION public.property_fields_user_is_member(
  target_organization_id uuid
)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $function$
  SELECT EXISTS (
    SELECT 1
    FROM public.organization_memberships AS memberships
    WHERE memberships.organization_id = target_organization_id
      AND memberships.user_id = auth.uid()
  );
$function$;

REVOKE ALL ON FUNCTION public.property_fields_user_is_member(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.property_fields_user_is_member(uuid) TO authenticated;

-- PostgreSQL combines permissive policies with OR. Remove every existing
-- property_fields policy (including policies unknown to the old migration
-- file) before installing the complete, known tenant policy set below.
DO $$
DECLARE
  existing_policy RECORD;
BEGIN
  FOR existing_policy IN
    SELECT policyname
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'property_fields'
  LOOP
    EXECUTE format(
      'DROP POLICY %I ON public.property_fields',
      existing_policy.policyname
    );
  END LOOP;
END
$$;

ALTER TABLE public.property_fields ENABLE ROW LEVEL SECURITY;

CREATE POLICY property_fields_select_same_organization
  ON public.property_fields
  FOR SELECT
  TO authenticated
  USING (public.property_fields_user_is_member(organization_id));

CREATE POLICY property_fields_insert_same_organization
  ON public.property_fields
  FOR INSERT
  TO authenticated
  WITH CHECK (public.property_fields_user_is_member(organization_id));

CREATE POLICY property_fields_update_same_organization
  ON public.property_fields
  FOR UPDATE
  TO authenticated
  USING (public.property_fields_user_is_member(organization_id))
  WITH CHECK (public.property_fields_user_is_member(organization_id));

CREATE POLICY property_fields_delete_same_organization
  ON public.property_fields
  FOR DELETE
  TO authenticated
  USING (public.property_fields_user_is_member(organization_id));

COMMIT;
