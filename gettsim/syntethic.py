import datetime

import numpy as np
import pandas as pd

from gettsim.policy_environment import _load_parameter_group_from_yaml


def create_other_hh_members(df, hh_typ, age_adults, age_children, double_earner):
    """
    duplicates information from the one person already created
    as often as needed.
    """
    new_df = df[df["hh_typ"] == hh_typ].copy()
    # Single: no additional person needed
    if hh_typ == "sing":
        return None
    # Single Parent one child
    if hh_typ == "sp1ch":
        new_df["kind"] = True
        new_df["alter"] = age_children[0]
    # Single Parent two children
    if hh_typ == "sp2ch":
        new_df = new_df.append(new_df, ignore_index=True)
        new_df["kind"] = pd.Series([True, True])
        new_df["alter"] = pd.Series(age_children)
    if hh_typ == "coup":
        new_df["alter"] = age_adults[1]
    if hh_typ == "coup1ch":
        new_df = new_df.append(new_df, ignore_index=True)
        new_df["kind"] = pd.Series([False, True])
        new_df["alter"] = pd.Series([age_adults[1], age_children[0]])
    if hh_typ == "coup2ch":
        new_df = new_df.append([new_df] * 2, ignore_index=True)
        new_df["kind"] = pd.Series([False, True, True])
        new_df["alter"] = pd.Series([age_adults[1], age_children[0], age_children[1]])

    # Make sure new household members are not heads
    new_df["tu_vorstand"] = False
    # Children are in education
    new_df["in_ausbildung"] = new_df["kind"]
    # children do not have earnings
    new_df.loc[new_df["kind"], "bruttolohn_m"] = 0
    # If single earner household, the partner is assigned zero wage as well
    if not double_earner:
        new_df.loc[~new_df["kind"], "bruttolohn_m"] = 0
    return new_df


def gettsim_hypo_data(
    hh_typen=("sing", "sp1ch", "sp2ch", "coup", "coup1ch", "coup2ch"),
    age_adults=(35, 35),
    age_children=(3, 8),
    baujahr=1980,
    double_earner=False,
    policy_year=datetime.datetime.now().year,
    heterogeneous_vars=(),
    **kwargs,
):
    """
    Creates a dataset with hypothetical household types,
    which can be used as input for gettsim

    hh_typen (tuple of str):
        Allowed Household Types:
        - 'sing' - Single, no kids
        - 'sp1ch' - Single Parent, one child
        - 'sp2ch' - Single Parent, two children
        - 'coup' - Couple, no kids
        - 'coup1ch' - Couple, one child
        - 'coup2ch' - Couple, two children

    age_adults (list of int):
        Assumed age of adult(s)

    age_children (list of int):
        Assumed age of children

    baujahr (int):
        Construction year of building

    double_earner (bool):
        whether or not both adults should be assigned the same value for 'bruttolohn_m'

    heterogenous_vars (dict):
        if specified, contains the variable name as key and a list of values

    policy_year (int):
        the year from which the reference data on housing are drawn.

    kwargs

    bruttolohn_m, kapital_eink_m, eink_selbst_m, vermögen_hh (int):
        values for income and wealth, respectively.
        only valid if heterogenous vars is empty
    """
    # Check inputs
    for t in hh_typen:
        if t not in ["sing", "sp1ch", "sp2ch", "coup", "coup1ch", "coup2ch"]:
            raise ValueError(f"illegal household type: {t}")

    for a in age_adults + age_children:
        if (a <= 0) or (type(a) != int):
            raise ValueError(f"illegal value for age: {a}")

    if len(heterogeneous_vars) == 0:
        # If no heterogeneity specified,
        # just create the household types with default incomes.
        return create_single_household(
            hh_typen,
            age_adults,
            age_children,
            baujahr,
            double_earner,
            policy_year,
            bruttolohn_m=kwargs.get("bruttolohn_m", 2000),
        )
    else:
        synth = pd.DataFrame()
        # loop over variables to vary
        for hetvar in heterogeneous_vars.keys():
            # allow only certain variables to vary
            if hetvar not in [
                "bruttolohn_m",
                "kapital_eink_m",
                "eink_selbst_m",
                "vermögen_hh",
            ]:
                raise ValueError(
                    f"Illegal value for variable to vary across households: {hetvar}"
                )
            for value in heterogeneous_vars[hetvar]:
                synth = synth.append(
                    create_single_household(
                        hh_typen,
                        age_adults,
                        age_children,
                        baujahr,
                        double_earner,
                        policy_year,
                        **{hetvar: value},
                    )
                )
    # TODO: RE-CREATE unique household and personal id.
    synth = synth.reset_index()
    synth["p_id"] = synth.index

    return synth


def create_single_household(
    hh_typen, age_adults, age_children, baujahr, double_earner, policy_year, **kwargs
):
    """ creates a single set of households
    """
    # initiate empty dataframe
    output_columns = [
        "tu_vorstand",
        "vermögen_hh",
        "alter",
        "selbstständig",
        "wohnort_ost",
        "hat_kinder",
        "bruttolohn_m",
        "eink_selbst_m",
        "ges_rente_m",
        "prv_krankenv",
        "prv_krankv_beit_m",
        "prv_rente_beit_m",
        "bruttolohn_vorj_m",
        "arbeitsl_lfdj_m",
        "arbeitsl_vorj_m",
        "arbeitsl_vor2j_m",
        "arbeitsstunden_w",
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
        "prv_krankenv",
    ]:
        df[c] = False

    # 'Custom' initializations
    df["tu_vorstand"] = True
    df["alter"] = age_adults[0]
    df["immobilie_baujahr"] = baujahr
    for c in ["arbeitsl_lfdj_m", "arbeitsl_vorj_m", "arbeitsl_vor2j_m"]:
        df[c] = 12

    df["hh_typ"] = pd.Series(hh_typen)

    # Wohnfläche, Kaltmiete, Heizkosten are taken from official data
    bg_daten = _load_parameter_group_from_yaml(
        datetime.date(policy_year, 1, 1), "bedarfsgemeinschaften"
    )
    df["wohnfläche"] = df["hh_typ"].map(bg_daten["wohnfläche"])
    df["kaltmiete_m"] = df["hh_typ"].map(bg_daten["kaltmiete"])
    df["heizkost_m"] = df["hh_typ"].map(bg_daten["heizkosten"])
    # Income and wealth
    df["bruttolohn_m"] = kwargs.get("bruttolohn_m", 0)
    df["kapital_eink_m"] = kwargs.get("bruttolohn_m", 0)
    df["eink_selbst_m"] = kwargs.get("eink_selbst_m", 0)
    df["vermögen_hh"] = kwargs.get("vermögen_hh", 0)

    df["hh_id"] = df.index
    df["tu_id"] = df.index

    # append entries for children and partner
    for hht in hh_typen:
        df = df.append(
            create_other_hh_members(df, hht, age_adults, age_children, double_earner)
        )
    df["geburtsjahr"] = policy_year - df["alter"]
    df["jahr_renteneintr"] = df["geburtsjahr"] + 67

    df["hat_kinder"] = df["hh_typ"].str.contains("ch")

    df.loc[df["bruttolohn_m"] > 0, "arbeitsstunden_w"] = 38

    # All adults in couples are assumed to be married
    df.loc[(df["hh_typ"].str.contains("coup")) & (~df["kind"]), "gem_veranlagt"] = True
    df.loc[(df["hh_typ"].str.contains("sp")) & (~df["kind"]), "alleinerziehend"] = True

    df = df.sort_values(by=["hh_typ", "hh_id"])

    df = df.reset_index()
    df["p_id"] = df.index

    return df[["hh_id", "tu_id", "p_id", "hh_typ"] + output_columns]
