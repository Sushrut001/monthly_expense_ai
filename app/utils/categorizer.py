"""
app/utils/categorizer.py
Rule-based + keyword-driven transaction categoriser.
"""
from __future__ import annotations

import re
import pandas as pd

# ── Keyword → Category mapping ──────────────────────────────────────────────
_RULES: dict[str, list[str]] = {
    "Income": [
        r"\bsalary\b", r"\bpayroll\b", r"\bincome\b", r"\bwages?\b",
        r"\bbonus\b", r"\bdividend\b", r"\brefund\b", r"\bfreelance\b",
        r"\bcredit\s+received\b", r"\binterest\s+credit\b", r"\bneft\s+cr\b",
        r"\bimps\s+cr\b", r"\brtgs\s+cr\b",
    ],
    "Food": [
        r"\bswiggy\b", r"\bzomato\b", r"\bubereats\b", r"\brestaurant\b",
        r"\bcafe\b", r"\bcoffee\b", r"\bpizza\b", r"\bburger\b", r"\bdominos\b",
        r"\bmcdonalds?\b", r"\bkfc\b", r"\bsubway\b", r"\bgrocery\b",
        r"\bbigbasket\b", r"\bgrofers\b", r"\bblinkit\b", r"\bzepto\b",
        r"\binstamrt\b", r"\bdunzo\b", r"\bfood\b", r"\bmeal\b",
        r"\bdinning\b", r"\bdining\b", r"\bcanteen\b", r"\bsupermarket\b",
        r"\breliance\s+fresh\b", r"\bmore\s+retail\b", r"\bdmart\b",
    ],
    "Transport": [
        r"\buber\b", r"\bola\b", r"\blyft\b", r"\brapido\b", r"\bauto\b",
        r"\btaxi\b", r"\bcab\b", r"\bpetrol\b", r"\bfuel\b", r"\bgas\b",
        r"\bmetro\b", r"\bbus\b", r"\btrain\b", r"\birctc\b", r"\bindigoair\b",
        r"\bairlines?\b", r"\bflight\b", r"\bairport\b", r"\bmakemytrip\b",
        r"\bgoibibo\b", r"\byrail\b", r"\bparkplus\b", r"\bparking\b",
        r"\btoll\b", r"\bfasttag\b",
    ],
    "Shopping": [
        r"\bamazon\b", r"\bflipcart\b", r"\bflipcart\b", r"\bflipart\b",
        r"\bflipcart\b", r"\bflipkart\b", r"\bmeesho\b", r"\bmyntra\b",
        r"\bajio\b", r"\bnykaa\b", r"\bzara\b", r"\bh&m\b", r"\bshopify\b",
        r"\bshopping\b", r"\bstore\b", r"\bmall\b", r"\bmarket\b",
        r"\bonline\s+purchase\b", r"\becommerce\b",
    ],
    "Bills": [
        r"\bbill\b", r"\belectricity\b", r"\bpower\b", r"\bmseb\b",
        r"\btata\s+power\b", r"\bbescom\b", r"\bwater\b", r"\bgas\s+bill\b",
        r"\bmobile\b", r"\bairtel\b", r"\bjio\b", r"\bbsnl\b", r"\bvi\b",
        r"\brecharge\b", r"\bbroadband\b", r"\binternet\b", r"\bdth\b",
        r"\btata\s+sky\b", r"\bdish\s+tv\b", r"\brent\b", r"\bemi\b",
        r"\bloan\b", r"\bmortgage\b", r"\binsurance\b", r"\bpremium\b",
        r"\butility\b", r"\btelecom\b",
    ],
    "Entertainment": [
        r"\bnetflix\b", r"\bspotify\b", r"\bprime\b", r"\bhulu\b",
        r"\bdisney\+?\b", r"\bhotstar\b", r"\bsonyliv\b", r"\bzee5\b",
        r"\byoutube\b", r"\bgaming\b", r"\bsteam\b", r"\bcinema\b",
        r"\bmovie\b", r"\btheatre\b", r"\bpvr\b", r"\binox\b",
        r"\bconcert\b", r"\bevent\b", r"\bticket\b", r"\bbook\s*my\s*show\b",
        r"\bclub\b", r"\bbar\b", r"\bpub\b",
    ],
    "Healthcare": [
        r"\bhospital\b", r"\bclinic\b", r"\bdoctor\b", r"\bpharmacy\b",
        r"\bmedical\b", r"\bmedicine\b", r"\bdrug\b", r"\bapollo\b",
        r"\bfortis\b", r"\bhealthcare\b", r"\bhealth\b", r"\blab\b",
        r"\bdiagnostic\b", r"\bpathology\b", r"\bdentist\b", r"\beye\s+care\b",
        r"\bnetmeds\b", r"\bpharmaeasy\b", r"\b1mg\b",
    ],
}

_COMPILED: dict[str, list[re.Pattern]] = {
    cat: [re.compile(p, re.IGNORECASE) for p in patterns]
    for cat, patterns in _RULES.items()
}


def _categorise_single(description: str, transaction_type: str) -> str:
    if transaction_type == "credit":
        # Quick win: credits are almost always income unless matched otherwise
        for pattern in _COMPILED["Income"]:
            if pattern.search(description):
                return "Income"
        # Still could be a refund/cashback falling under Income
        return "Income"

    desc_lower = description.lower()
    for category, patterns in _COMPILED.items():
        if category == "Income":
            continue
        for pattern in patterns:
            if pattern.search(desc_lower):
                return category
    return "Other"


def categorise_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a `category` column to the DataFrame.
    Input must have `description` and `transaction_type` columns.
    """
    df = df.copy()
    df["category"] = df.apply(
        lambda row: _categorise_single(row["description"], row["transaction_type"]),
        axis=1,
    )
    return df
