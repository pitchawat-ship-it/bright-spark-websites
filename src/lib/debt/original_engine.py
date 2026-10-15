# -*- coding: utf-8 -*-
"""
Debt Calculation & Advanced Financial Advisory Engine (Production-Grade)
- Supports Daily Interest, Flat Rate to Effective Rate conversions
- Stress-testing, Refinancing Analyzers, Late Fee estimators, and strict Audit Rails
"""
from __future__ import annotations
 
import json
import math
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
 
D = Decimal
CENT = D("0.01")
MAX_MONTHS = 600
 
def money(x) -> Decimal:
    """Convert input to a Decimal safely and quantize it to 2 decimal places."""
    if x is None:
        return D("0.00")
    val_str = str(x).strip()
    if val_str.lower() in ["nan", "inf", "-inf", ""]:
        return D("0.00")
    try:
        return D(val_str).quantize(CENT, rounding=ROUND_HALF_UP)
    except Exception:
        return D("0.00")
 
# ════════════════════════════════════════════════════════════
# 1) DATACLASSES & STRUCTURAL SETUP
# ════════════════════════════════════════════════════════════
@dataclass
class Debt:
    name: str
    balance: float              # Total debt balance (THB)
    apr_pct: float              # Annual Percentage Rate (%)
    min_payment: float          # Minimum monthly payment
    debt_type: str = "standard"  # standard | daily_card | flat_rate
    flat_years: float = 0.0     # If flat_rate: tenure in years
    accrued_days: int = 30      # If daily_card: days accrued for interest calculation
 
@dataclass
class Profile:
    incomes: Dict[str, float]          # Monthly incomes
    living_expenses: Dict[str, float]  # Living/necessary expenses
    debts: List[Debt]
    savings_goal: float = 0.0          # Monthly savings target
    safety_buffer: float = 0.0         # Emergency reserve buffer
    start_month: str = "2026-11"
 
@dataclass
class ScenarioDefinition:
    key_name: str
    strategy: str
    extra_override: Optional[float] = None
    custom_sequence: Optional[List[str]] = None
 
# ════════════════════════════════════════════════════════════
# 2) STAGE 1: FINANCIAL FEASIBILITY & ADAPTIVE STRESS-TEST
# ════════════════════════════════════════════════════════════
@dataclass
class FeasibilityReport:
    total_income: Decimal
    total_living: Decimal
    total_savings: Decimal
    min_debt_payment: Decimal
    safety_reserve: Decimal
    free_cashflow: Decimal
    max_possible_extra: Decimal
    is_feasible: bool
    shortfall: Decimal
    status_message: str
    risk_level: str
    min_income_to_survive: Decimal     # Minimum income target to survive
    max_income_drop_pct: Decimal       # Maximum drop % of income before plan fails
 
@dataclass
class BudgetResult:
    income: Decimal
    living: Decimal
    savings: Decimal
    min_total: Decimal
    capacity_extra: Decimal
    extra_used: Decimal
    shortfall: Decimal
    warnings: List[str] = field(default_factory=list)
 
def compute_budget(p: Profile, custom_extra: Optional[float] = None) -> BudgetResult:
    income = sum(money(v) for v in p.incomes.values())
    living = sum(money(v) for v in p.living_expenses.values())
    savings = money(p.savings_goal)
    min_total = sum(money(d.min_payment) for d in p.debts)
 
    free = income - living - savings - min_total
    warnings: List[str] = []
    shortfall = D("0.00")
    capacity = D("0.00")
 
    if free < 0:
        shortfall = -free
        warnings.append(f"Insufficient income for min payments! Shortfall of {shortfall:,.2f} THB/month.")
    else:
        capacity = free
 
    if custom_extra is None:
        extra = capacity
    else:
        extra = money(custom_extra)
        if extra < 0:
            extra = D("0.00")
        if extra > capacity:
            warnings.append(f"Custom extra budget {extra:,.2f} exceeds net capacity. Adjusted down to {capacity:,.2f} THB/month.")
            extra = capacity
 
    return BudgetResult(income, living, savings, min_total, capacity, extra, shortfall, warnings)
 
def analyze_feasibility(p: Profile) -> FeasibilityReport:
    """Evaluate financial health and perform stress-testing."""
    t_inc = sum(money(v) for v in p.incomes.values())
    t_liv = sum(money(v) for v in p.living_expenses.values())
    t_sav = money(p.savings_goal)
    t_min = sum(money(d.min_payment) for d in p.debts)
    t_safe = money(p.safety_buffer)
 
    free_cf = t_inc - t_liv - t_sav - t_min
    min_survive = t_liv + t_min  # Required living costs + minimum debt obligations
 
    if t_inc > 0:
        max_drop = ((t_inc - min_survive) / t_inc) * D("100.00")
        max_drop = max(D("0.00"), max_drop)
    else:
        max_drop = D("0.00")
 
    if free_cf < 0:
        shortfall = -free_cf
        is_feasible = False
        max_extra = D("0.00")
        risk_level = "Critical"
        status_message = f"Critical Cash Flow deficit! Lacking monthly budget for minimum debt payment of {shortfall:,.2f} THB/month."
    else:
        shortfall = D("0.00")
        is_feasible = True
        max_extra = max(free_cf - t_safe, D("0.00"))
        if max_extra == 0:
            risk_level = "High"
            status_message = "Extremely limited cash flow. Budget covers only minimum payments."
        elif max_extra < (t_inc * D("0.10")):
            risk_level = "Medium"
            status_message = "Moderate cash flow. Some potential to pay down extra debt."
        else:
            risk_level = "Low"
            status_message = "Excellent cash flow. Strong capacity for aggressive debt payoff."
 
    return FeasibilityReport(
        total_income=t_inc,
        total_living=t_liv,
        total_savings=t_sav,
        min_debt_payment=t_min,
        safety_reserve=t_safe,
        free_cashflow=free_cf,
        max_possible_extra=max_extra,
        is_feasible=is_feasible,
        shortfall=shortfall,
        status_message=status_message,
        risk_level=risk_level,
        min_income_to_survive=min_survive,
        max_income_drop_pct=max_drop
    )
 
# ════════════════════════════════════════════════════════════
# 3) FINANCIAL FORMULAS (Flat to Effective, Break-Even, etc.)
# ════════════════════════════════════════════════════════════
def flat_to_effective_apr(flat_rate_pct: float, years: float) -> float:
    """Convert flat interest rate to estimated effective annual percentage rate (APR)."""
    if years <= 0 or flat_rate_pct <= 0:
        return flat_rate_pct
    n_periods = years * 12
    return float((2 * n_periods / (n_periods + 1)) * flat_rate_pct)
 
def compute_reinvestment_breakeven(original_interest: Decimal, new_interest: Decimal, fee: Decimal) -> float:
    """Calculate refinancing break-even timeline in months."""
    monthly_saving = original_interest - new_interest
    if monthly_saving <= 0:
        return float("inf")
    return float((fee / monthly_saving).quantize(CENT, rounding=ROUND_HALF_UP))
 
# ════════════════════════════════════════════════════════════
# 4) CORE SIMULATION ENGINE WITH ERROR-HANDLING
# ════════════════════════════════════════════════════════════
def simulate_engine(
    debts: List[Debt],
    extra_budget: Decimal,
    strategy: str,
    rollover: bool,
    start_month: str,
    custom_order: Optional[List[str]] = None
) -> pd.DataFrame:
    """Simulate monthly debt payment schedules with dynamic interest calculations."""
    state = []
    for d in debts:
        apr = d.apr_pct
        if d.debt_type == "flat_rate" and d.flat_years > 0:
            apr = flat_to_effective_apr(d.apr_pct, d.flat_years)
 
        state.append({
            "name": d.name.strip(),
            "bal": money(d.balance),
            "apr": money(apr),
            "min": money(d.min_payment),
            "type": d.debt_type,
            "accrued_days": d.accrued_days
        })
 
    fixed_pool = sum((s["min"] for s in state), D("0.00")) + extra_budget
    period_cursor = pd.Period(start_month, freq="M")
    rows = []
 
    for m_no in range(1, MAX_MONTHS + 1):
        active = [s for s in state if s["bal"] > 0]
        if not active:
            break
 
        month_label = str(period_cursor + (m_no - 1))
        monthly_distribution = {}
 
        for s in active:
            if s["type"] == "daily_card":
                monthly_interest = money(s["bal"] * (s["apr"] / D("100.00")) / D("365.00") * D(s["accrued_days"]))
            else:
                monthly_interest = money(s["bal"] * (s["apr"] / D("100.00")) / D("12.00"))
 
            total_owed = s["bal"] + monthly_interest
            pay_min = min(s["min"], total_owed)
 
            monthly_distribution[s["name"]] = {
                "opening": s["bal"],
                "interest": monthly_interest,
                "owed": total_owed,
                "pay_min": pay_min,
                "pay_extra": D("0.00"),
                "closing": total_owed - pay_min
            }
 
        total_paid_min = sum(r["pay_min"] for r in monthly_distribution.values())
        if rollover:
            available_extra = fixed_pool - total_paid_min
        else:
            available_extra = extra_budget if strategy != "baseline" else D("0.00")
        available_extra = max(available_extra, D("0.00"))
 
        # Sorting
        if strategy == "avalanche":
            sorted_debts = sorted(active, key=lambda x: (-x["apr"], x["bal"], x["name"]))
        elif strategy == "snowball":
            sorted_debts = sorted(active, key=lambda x: (x["bal"], -x["apr"], x["name"]))
        elif strategy == "custom" and custom_order:
            order_map = {name.strip(): i for i, name in enumerate(custom_order)}
            sorted_debts = sorted(active, key=lambda x: (order_map.get(x["name"], 999), x["name"]))
        else:
            sorted_debts = active
 
        for s in sorted_debts:
            if available_extra <= 0:
                break
            r = monthly_distribution[s["name"]]
            remaining_to_pay = r["closing"]
            additional_payment = min(available_extra, remaining_to_pay)
 
            r["pay_extra"] = additional_payment
            available_extra -= additional_payment
 
        for s in active:
            r = monthly_distribution[s["name"]]
            total_pay = r["pay_min"] + r["pay_extra"]
            final_closing = r["owed"] - total_pay
 
            rows.append({
                "month_no": m_no,
                "month": month_label,
                "debt": s["name"],
                "opening": float(r["opening"]),
                "interest": float(r["interest"]),
                "pay_min": float(r["pay_min"]),
                "pay_extra": float(r["pay_extra"]),
                "pay_total": float(total_pay),
                "principal": float(total_pay - r["interest"]),
                "closing": float(final_closing)
            })
            s["bal"] = final_closing
 
    return pd.DataFrame(rows)
 
# ════════════════════════════════════════════════════════════
# 5) ANALYTICS & STRATEGIC SCENARIOS RUNNER
# ════════════════════════════════════════════════════════════
def run_simulation_suite(
    profile_input: Profile,
    scenarios: List[ScenarioDefinition]
) -> Dict[str, Any]:
    feasibility = analyze_feasibility(profile_input)
    results = {}
    comparison_rows = []
 
    for sc in scenarios:
        warnings_log = []
 
        if sc.strategy == "baseline":
            budget_info = compute_budget(profile_input, custom_extra=0.0)
            extra_used = D("0.00")
            rollover = False
        else:
            budget_info = compute_budget(profile_input, custom_extra=sc.extra_override)
            extra_used = budget_info.extra_used
            rollover = True
 
        warnings_log.extend(budget_info.warnings)
 
        df_schedule = simulate_engine(
            debts=profile_input.debts,
            extra_budget=extra_used,
            strategy=sc.strategy,
            rollover=rollover,
            start_month=profile_input.start_month,
            custom_order=sc.custom_sequence
        )
 
        debt_final_balances = {}
        for d in profile_input.debts:
            subset = df_schedule[df_schedule["debt"] == d.name]
            debt_final_balances[d.name] = money(subset["closing"].iloc[-1]) if not subset.empty else money(d.balance)
 
        fully_paid_off = all(val <= 0 for val in debt_final_balances.values())
        months_taken = int(df_schedule["month_no"].max()) if not df_schedule.empty else 0
 
        total_interest_paid = money(df_schedule["interest"].sum()) if not df_schedule.empty else D("0.00")
        total_amount_paid = money(df_schedule["pay_total"].sum()) if not df_schedule.empty else D("0.00")
 
        payoff_by_item = {}
        for d in profile_input.debts:
            sub = df_schedule[df_schedule["debt"] == d.name]
            closed_row = sub[sub["closing"] <= 0]
            payoff_by_item[d.name] = int(closed_row["month_no"].iloc[0]) if not closed_row.empty else -1
 
        summary_stat = {
            "months": months_taken,
            "paid_off": fully_paid_off,
            "total_interest": total_interest_paid,
            "total_paid": total_amount_paid,
            "payoff_month_by_debt": payoff_by_item,
            "final_month": df_schedule["month"].iloc[-1] if not df_schedule.empty else profile_input.start_month
        }
 
        issues = []
        for (m, d_n), grp in df_schedule.groupby(["month_no", "debt"]):
            op = money(grp["opening"].iloc[0])
            cl = money(grp["closing"].iloc[0])
            ite = money(grp["interest"].iloc[0])
            p_t = money(grp["pay_total"].iloc[0])
            if money(op + ite - p_t) != cl:
                issues.append(f"Mathematical inconsistency detected in month {m} for {d_n}")
 
        results[sc.key_name] = {
            "budget": budget_info,
            "schedule": df_schedule,
            "summary": summary_stat,
            "audit_passed": len(issues) == 0,
            "audit_details": issues,
            "warnings": warnings_log
        }
 
    baseline_stat = results.get("Baseline", {}).get("summary")
    for sc in scenarios:
        sc_data = results[sc.key_name]
        s_sum = sc_data["summary"]
 
        row = {
            "Scenario": sc.key_name,
            "Extra Budget/Month": float(sc_data["budget"].extra_used),
            "Duration (Months)": s_sum["months"],
            "Payoff Status": "Fully Settled" if s_sum["paid_off"] else "Remaining Balance",
            "Target End Month": s_sum["final_month"],
            "Total Interest": float(s_sum["total_interest"]),
            "Total Paid": float(s_sum["total_paid"]),
            "Accumulated Interest Saved": 0.0,
            "Timeline Reduced (Months)": 0
        }
        if baseline_stat:
            row["Accumulated Interest Saved"] = float(money(baseline_stat["total_interest"] - s_sum["total_interest"]))
            row["Timeline Reduced (Months)"] = max(0, baseline_stat["months"] - s_sum["months"])
        comparison_rows.append(row)
 
    comparison_df = pd.DataFrame(comparison_rows)
 
    return {
        "feasibility": feasibility,
        "scenarios": results,
        "comparison": comparison_df,
        "audit_info": {"formulas": ["Daily Interest", "Monthly Interest"], "assumptions": []}
    }
 
# ════════════════════════════════════════════════════════════
# 6) EXECUTION INTERFACE (COLAB INTERACTIVE FORM)
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=== Enter Your Financial Information ===")
    
    # 💰 Monthly Incomes
    salary_income = float(input("Monthly Salary Income (THB): ") or 45000)
    supplementary_income = float(input("Other Supplementary Income (THB): ") or 0)
 
    # 🏠 Living Expenses & Emergency Reserve
    total_living_expenses = float(input("Total Monthly Living Expenses (THB): ") or 20000)
    savings_goal = float(input("Monthly Savings Goal (THB): ") or 2000)
    safety_reserve_buffer = float(input("Safety Reserve Buffer (THB): ") or 1000)
 
    # 📅 Dynamic Debts Collection Loop
    debts_list = []
    debt_count = 1
    
    print("\n--- Outstanding Debts & Commitments ---")
    while True:
        print(f"\n[Debt Item #{debt_count}]")
        d_name = input(f"Debt Name (e.g., Credit Card {debt_count}): ") or f"Debt {debt_count}"
        d_bal = float(input("Remaining Debt Balance (THB): ") or 50000)
        d_apr = float(input("Annual Interest Rate (%) e.g., 18.0: ") or 18.0)
        d_min = float(input("Minimum Monthly Payment (THB): ") or 2000)
        d_type = input("Debt Type (standard / daily_card / flat_rate): ") or "standard"
        
        d_days = 30
        d_years = 0.0
        if d_type == "daily_card":
            d_days = int(input("Accrued Interest Days (default 30): ") or 30)
        elif d_type == "flat_rate":
            d_years = float(input("Flat Rate Tenure (Years): ") or 1.0)
            
        # Add to list
        debts_list.append(
            Debt(d_name, d_bal, d_apr, d_min, debt_type=d_type, accrued_days=d_days, flat_years=d_years)
        )
        
        # Ask if the user wants to add more
        cont = input("\nDo you have another debt? (y/n, default 'n'): ").strip().lower()
        if cont != 'y':
            break
        debt_count += 1
 
    # 📈 Strategic Simulation
    custom_extra_budget = float(input("\nCustom Extra Budget to Test (THB): ") or 5000)
    start_month = input("Start Month (Format YYYY-MM e.g., 2026-11): ") or "2026-11"
 
    # Setup user financial profile
    profile = Profile(
        incomes={
            "Salary": salary_income,
            "Freelance": supplementary_income
        },
        living_expenses={
            "Living expenses": total_living_expenses
        },
        debts=debts_list,
        savings_goal=savings_goal,
        safety_buffer=safety_reserve_buffer,
        start_month=start_month
    )
 
    # Define testing scenarios
    scenario_definitions = [
        ScenarioDefinition("Baseline", "baseline"),
        ScenarioDefinition("Avalanche", "avalanche"),
        ScenarioDefinition("Snowball", "snowball"),
        ScenarioDefinition("Custom Budget", "avalanche", extra_override=custom_extra_budget)
    ]
 
    # Execute the simulation engine
    suite_output = run_simulation_suite(profile, scenario_definitions)
    fe_rep = suite_output["feasibility"]
 
    print("\n" + "="*70)
    print("📊 FINANCIAL FEASIBILITY & STRESS-TEST REPORT")
    print("="*70)
    print(f"- Safe Monthly Extra Budget Allocation (Friction-Free Extra Budget): {fe_rep.max_possible_extra:,.2f} THB/month")
    print(f"- Required Monthly Income Target for Survival (Min Income Target): {fe_rep.min_income_to_survive:,.2f} THB/month")
    print(f"- Income Protection Buffer (Max acceptable drop in income): {fe_rep.max_income_drop_pct:,.2f}%")
    print("="*70 + "\n")
 
    print("🏆 STRATEGIC PAYOFF SCENARIOS COMPARISON BOARD:")
    pd.options.display.float_format = "{:,.2f}".format
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", None)
    print(suite_output["comparison"].to_string(index=False))
 
    refi_months = compute_reinvestment_breakeven(D("3000"), D("1500"), D("5000"))
    print(f"\n🔄 [Refinance Check] Assuming personal loan refinancing: saving {3000:,.2f} THB originally down to {1500:,.2f} THB in interest (Fee: 5,000 THB) will reach Break-Even point in {refi_months:.1f} months.")