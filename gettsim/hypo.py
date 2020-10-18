import datetime

import numpy as np
import pandas as pd


def create_other_hh_members(df, hh_typ, alter, alter_kind_1, alter_kind_2):
    new_df = df[df["hh_typ"] == hh_typ].copy()
    # Single: do nothing
    if hh_typ == "sing":
        return None
    # Single Parent one child
    if hh_typ == "sp1ch":
        new_df["kind"] = True
        new_df["alter"] = alter_kind_1
    # Single Parent two children
    if hh_typ == "sp2ch":
        new_df = new_df.append(new_df, ignore_index=True)
        new_df["kind"] = pd.Series([True, True])
        new_df["alter"] = pd.Series([alter_kind_1, alter_kind_2])
    if hh_typ == "coup1ch":
        new_df = new_df.append(new_df, ignore_index=True)
        new_df["kind"] = pd.Series([False, True])
        new_df["alter"] = pd.Series([alter, alter_kind_1])
    if hh_typ == "coup2ch":
        new_df = new_df.append([new_df] * 2, ignore_index=True)
        new_df["kind"] = pd.Series([False, True, True])
        new_df["alter"] = pd.Series([alter, alter_kind_1, alter_kind_2])

    new_df["tu_vorstand"] = False
    new_df["in_ausbildung"] = new_df["kind"]
    new_df["bruttolohn_m"] = 0
    return new_df


def gettsim_hypo_data(
    hh_typen=("sing", "sp1ch", "sp2ch", "coup", "coup1ch", "coup2ch"),
    bruttolohn=2000,
    alter=35,
    alter_kind_1=3,
    alter_kind_2=8,
    baujahr=1980,
):
    """
    Creates a dataset with hypothetical household types,
    which can be used as input for gettsim

    hh_typen: (tuple of str):
        Allowed Household Types:
    - 'sing' - Single, no kids
    - 'sp1ch' - Single Parent, one child
    - 'sp2ch' - Single Parent, two children
    - 'coup' - Couple, no kids
    - 'coup1ch' - Couple, one child
    - 'coup2ch' - Couple, two children

    bruttolohn (int):
        Gross monthly wage for the household head.

    alter, alter_kind_1, alter_kind_2 (int):
        Assumed age of adult(s) and first and second child

    baujahr (int):
        Construction year of building
    """
    # Check inputs
    for t in hh_typen:
        if t not in ["sing", "sp1ch", "sp2ch", "coup", "coup1ch", "coup2ch"]:
            raise ValueError(f"illegal household type: {t}")

    # initiate empty dataframe
    output_columns = [
        "tu_vorstand",
        "anz_erwachsene_hh",
        "anz_minderj_hh",
        "vermögen_hh",
        "alter",
        "selbstständig",
        "wohnort_ost",
        "hat_kinder",
        "bruttolohn_m",
        "eink_selbstst_m",
        "ges_rente_m",
        "prv_krankv_beit_m",
        "prv_rente_beit_m",
        "bruttolohn_vorj_m",
        "arbeitsl_lfdj_m",
        "arbeitsl_vorj_m",
        "arbeitsl_vor2j_m",
        "arbeitsstunden_w",
        "anz_kinder_tu",
        "anz_erw_tu",
        "geburtsjahr",
        "entgeltpunkte",
        "kind",
        "rentner",
        "betreuungskost_m",
        "miete_unterstellt",
        "kapital_eink_m",
        "vermiet_eink_m",
        "kaltmiete_m",
        "heizkost_m",
        "jahr_renteneintr",
        "behinderungsgrad",
        "wohnfläche",
        "gem_veranlagt",
        "in_ausbildung",
        "alleinerziehend",
        "bewohnt_eigentum",
        "immobilie_baujahr",
        "sonstig_eink_m",
    ]

    df = pd.DataFrame(
        columns=output_columns, data=np.zeros((len(hh_typen), len(output_columns)))
    )

    # Some columns require boolean type. initiate them with False
    for c in [
        "selbstständig",
        "wohnort_ost",
        "hat_kinder",
        "kind",
        "rentner",
        "gem_veranlagt",
        "in_ausbildung",
        "alleinerziehend",
        "bewohnt_eigentum",
    ]:
        df[c] = False

    # 'Custom' initializations
    df["tu_vorstand"] = True
    df["alter"] = alter
    df["immobilie_baujahr"] = baujahr
    for c in ["arbeitsl_lfdj_m", "arbeitsl_vorj_m", "arbeitsl_vor2j_m"]:
        df[c] = 12

    df["hh_typ"] = pd.Series(hh_typen)

    # Wohnfläche, Kaltmiete, Heizkosten are taken from official data
    bg_daten = {
        "wohnfläche": {
            "sing": 45,
            "sp1ch": 62,
            "sp2ch": 73,
            "coup": 63,
            "coup1ch": 70,
            "coup2ch": 76,
        },
        "kaltmiete": {
            "sing": 335,
            "sp1ch": 465,
            "sp2ch": 550,
            "coup": 449,
            "coup1ch": 553,
            "coup2ch": 629,
        },
        "heizkosten": {
            "sing": 46,
            "sp1ch": 68,
            "sp2ch": 80,
            "coup": 68,
            "coup1ch": 78,
            "coup2ch": 87,
        },
    }
    df["wohnfläche"] = df["hh_typ"].map(bg_daten["wohnfläche"])
    df["kaltmiete_m"] = df["hh_typ"].map(bg_daten["kaltmiete"])
    df["heizkost_m"] = df["hh_typ"].map(bg_daten["heizkosten"])

    df["bruttolohn_m"] = bruttolohn

    df = df.sort_values(by=["hh_typ", "bruttolohn_m"])

    df["hh_id"] = df.index
    df["tu_id"] = df.index

    # append entries for children and partner
    for hht in hh_typen:
        df = df.append(
            create_other_hh_members(df, hht, alter, alter_kind_1, alter_kind_2)
        )

    df["geburtsjahr"] = datetime.datetime.now().year - df["alter"]
    df["jahr_renteneintr"] = df["geburtsjahr"] + 67

    # Household and Tax Unit Totals
    for dim in ["hh", "tu"]:
        df[f"{dim}_size"] = df.groupby(f"{dim}_id")[f"{dim}_id"].transform("count")
        df[f"anz_minderj_{dim}"] = df.groupby(f"{dim}_id")["kind"].transform("sum")
        df[f"anz_erwachsene_{dim}"] = df[f"{dim}_size"] - df[f"anz_minderj_{dim}"]

    df["hat_kinder"] = df["anz_minderj_tu"] > 0

    df.loc[df["bruttolohn_m"] > 0, "arbeitsstunden_w"] = 38

    # All adults in couples are assumed to be married
    df.loc[(df["hh_typ"].str.contains("coup")) & (~df["kind"]), "gem_veranlagt"] = True
    df.loc[(df["hh_typ"].str.contains("sp")) & (~df["kind"]), "alleinerziehend"] = True

    df = df.sort_values(by=["hh_typ", "hh_id"])

    df = df.reset_index()
    df["p_id"] = df.index

    return df