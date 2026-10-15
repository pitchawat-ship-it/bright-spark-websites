CREATE TABLE public.financial_workspaces (user_id uuid PRIMARY KEY, state jsonb NOT NULL DEFAULT '{}'::jsonb, updated_at timestamptz NOT NULL DEFAULT now());
GRANT SELECT, INSERT, UPDATE, DELETE ON public.financial_workspaces TO authenticated;
GRANT ALL ON public.financial_workspaces TO service_role;
ALTER TABLE public.financial_workspaces ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Owners manage financial workspace" ON public.financial_workspaces FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);