<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

## Application architecture
- Keep the supplied Python engine as reference and port its Decimal simulation into a pure TypeScript module using decimal.js, because the deployed runtime cannot execute Python or pandas.
- Use a shared financial-state provider for every page, with isolated browser-only fictional sample mode and owner-scoped Cloud workspace persistence for personal records, because all calculations and histories must remain consistent.
- Use explicit confirmation for plan versions and reconcile manual payments against the confirmed monthly schedule, because financial history must be auditable.
- Keep named content views in separate TanStack leaf routes and reusable view components outside routes, because navigation and metadata must remain independently addressable.
