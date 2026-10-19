from datetime import date

from pulse.collectors.cbe import parse_bop, parse_cpi_page, parse_cpi_release, parse_mpc, parse_nir_title, parse_remittances
from pulse.collectors.gold_eg import parse_banklive
from pulse.collectors.pmi import parse_pmi_text


def test_nir_title():
    assert parse_nir_title("Net International Reserves reached US$ 57,348.2 mn at the end of September 2026 (Provisional)") == (date(2026, 9, 1), 57348.2)
    assert parse_nir_title("Something else") is None


def test_cpi_page():
    t = ("Last Updated: 11 Oct 2026 Inflation for Last Month: Sep 2026 Headline (m/m) Core (m/m) Headline (y/y) Core (y/y) "
         "Regulated Items (m/m) Fruits and Vegetables (m/m) Regulated Items (y/y) Fruits and Vegetables (y/y) "
         "1.300% 0.800% 13.900% 14.100% 0.100% 11.300% 12.000% 18.900% View Historical Data")
    month, rel, vals = parse_cpi_page(t)
    assert month == date(2026, 9, 1) and rel == date(2026, 10, 11)
    assert vals["cpi_urban_yoy"] == 13.9 and vals["cpi_core_yoy"] == 14.1 and vals["cpi_fv_yoy"] == 18.9


def test_cpi_release():
    t = ("Monthly urban headline CPI inflation, released yesterday by CAPMAS, recorded 1.3 percent in September 2026 compared with "
         "1.8 percent in September 2025 and 0.1 percent in August 2026. On an annual basis, urban headline CPI inflation recorded "
         "13.9 percent in September 2026 compared with 14.5 percent in August 2026.")
    out = parse_cpi_release(t)
    assert ("cpi_urban_yoy", date(2026, 8, 1), 14.5) in out and ("cpi_urban_mom", date(2025, 9, 1), 1.8) in out


def test_remittances():
    t = ("During the first eight months of 2026 (January/August 2026), remittances from Egyptians working abroad witnessed an increase "
         "of 27.2%, registering record inflows of about USD 33.9 billion (compared to around USD 26.6 billion during the same period of "
         "the previous year). Remittances also rose by 21.7% in August 2026, recording about USD 4.2 billion (against around USD 3.5 "
         "billion in August 2025).")
    out = parse_remittances(t)
    assert ("remittances", date(2026, 8, 1), 4.2, None) in out
    assert ("remittances_yoy", date(2026, 8, 1), 21.7, None) in out
    assert any(o[0] == "remittances_ytd" and o[2] == 33.9 for o in out)


def test_mpc():
    t = ("the Monetary Policy Committee (MPC) of the Central Bank of Egypt (CBE) has decided to keep its key policy rates unchanged. "
         "The overnight deposit rate, overnight lending rate, and the rate of the main operation remain at 19.00 percent, 20.00 percent, "
         "and 19.50 percent, respectively. The discount rate was also maintained at 19.50 percent. Domestically, real economic activity "
         "continued to moderate, with growth recording 4.7 percent in Q2 2026, down from 5.0 percent in Q1 2026. Accordingly, real GDP "
         "growth averaged 5.1 percent in FY 2025/26 and is expected to remain broadly stable.")
    p = parse_mpc(t)
    assert p["decision"] == 0 and (p["cbe_odr"], p["cbe_olr"], p["cbe_mainop"], p["cbe_discount"]) == (19.0, 20.0, 19.5, 19.5)
    assert p["gdp_q"][0] == (date(2026, 4, 1), 4.7) and p["gdp_fy"] == (date(2025, 7, 1), 5.1)


def test_bop_sentence_scoping():
    t = ("During FY 2025/2026, the BoP recorded an overall surplus of US$ 2.8 billion (against an overall deficit of US$ 2.1 billion). "
         "FDI in Egypt witnessed a net inflow of US$ 18.0 billion. The current account recorded a deficit of US$ 22.5 billion "
         "during the year under review (against US$ 15.4 billion). • Suez Canal transit receipts increased by 21.6 percent to register "
         "US$ 4.4 billion (against US$ 3.6 billion), due to traffic. • FDI in Egypt recorded a net inflow of US$ 18.0 billion "
         "(against US$ 12.2 billion), as follows")
    fy, vals = parse_bop(t)
    d = {(s, o): v for s, o, v in vals}
    assert fy == 2025
    assert d[("bop_overall_fy", date(2024, 7, 1))] == -2.1
    assert d[("bop_ca_fy", date(2025, 7, 1))] == -22.5
    assert d[("suez_receipts_fy", date(2025, 7, 1))] == 4.4 and d[("fdi_net_fy", date(2024, 7, 1))] == 12.2


def test_pmi_pairs():
    t = "Following a seven-month high of 49.6 in August, the Egypt PMI dropped to 47.2 in September and fell below its long-run average of 48.2."
    assert parse_pmi_text(t, date(2026, 10, 5)) == [(date(2026, 8, 1), 49.6), (date(2026, 9, 1), 47.2)]
    assert parse_pmi_text("PMI rose to 50.1 in December", date(2027, 1, 5)) == [(date(2026, 12, 1), 50.1)]


def test_banklive():
    t = ("Last Updated | 2026-10-18 15:00:02 Unit Buying Price Selling Price XAUUSD XAU/USD $4,165.42 0.003% $4,166.42 0.003% "
         "XAUEGP Gold 24 Karat 7,166 -0.07% 7,143 -0.07% XAUEGP Gold 21 Karat 6,270 -0.08% 6,250 -0.08% XAUEGP Gold Pound 50,160 -0.08%")
    p = parse_banklive(t)
    assert p["gold_eg_21k"] == 6270 and p["gold_eg_24k"] == 7166 and p["xauusd_spot"] == 4165.42 and p["gold_eg_pound"] == 50160


def test_cpi_release_negative_in_words():
    t = ("Monthly urban headline CPI inflation, released today by CAPMAS, recorded 0.0 percent in July 2026 compared with "
         "negative 0.5 percent in July 2025 and negative 0.4 percent in June 2026. On an annual basis, urban headline CPI "
         "inflation recorded 14.9 percent in July 2026 compared with 14.3 percent in June 2026.")
    out = parse_cpi_release(t)
    assert ("cpi_urban_mom", date(2025, 7, 1), -0.5) in out and ("cpi_urban_mom", date(2026, 6, 1), -0.4) in out
    assert ("cpi_urban_mom", date(2026, 7, 1), 0.0) in out


def test_foreign_flows_parser():
    from datetime import date
    from pulse.collectors.flows import parse_flows
    a = ("Egypt's stocks start week in dark red. The EGX30 fell on Sunday. Non-Arab foreign investors recorded net sales of "
         "5.562 billion Egyptian pounds, while Egyptian investors were net buyers of 5.121 billion pounds and Arab investors "
         "purchased a net 440.522 million pounds.")
    r = parse_flows(a, date(2026, 10, 18))
    assert len(r) == 1 and r[0]["series"] == "egx_foreign_net" and r[0]["value"] == -5562.0 and r[0]["date"] == date(2026, 10, 18)
    b = ("EGX rebounds on Thursday, Oct. 1. Egyptian investors recorded EGP318.5mn of net buying. Foreign investors sold "
         "EGP 225.7mn, including EGP 220.7mn of net selling by foreign institutions.")
    r = parse_flows(b, date(2026, 10, 2))
    assert r[0]["value"] == -225.7 and r[0]["date"] == date(2026, 10, 1)
    c = "Reported foreign net selling reached EGP5.56bn, intensifying concerns."
    assert parse_flows(c, date(2026, 10, 19))[0]["value"] == -5560.0
    d = "Foreign investors sold a net EGP 5.8bn of Egyptian treasury bills on Wednesday, traders said."
    r = parse_flows(d, date(2026, 10, 15))
    assert r[0]["series"] == "tbill_foreign_net" and r[0]["value"] == -5800.0 and r[0]["date"] == date(2026, 10, 14)
    e = "Foreign investors were net buyers of EGP 1.2bn on the EGX on Monday."
    assert parse_flows(e, date(2026, 10, 12))[0]["value"] == 1200.0


def test_foreign_flows_raw_pounds():
    from datetime import date
    from pulse.collectors.flows import parse_flows
    t = ("EGX closes mostly green on 19 October. Egyptians and Arabs were net buyers with 26,929,042,681 Egyptian pounds and "
         "83,336,831 pounds, respectively. Meanwhile, non-Arab foreigners were net sellers with 27,012,379,512 pounds.")
    r = parse_flows(t, date(2026, 10, 19))
    assert len(r) == 1 and abs(r[0]["value"] + 27012.38) < 0.01 and r[0]["date"] == date(2026, 10, 19)


def test_foreign_flows_respectively():
    from datetime import date
    from pulse.collectors.flows import parse_flows
    t = ("EGX closes in green area on October 15. Arabs and non-Arab foreigners were net buyers with 9,422,965,489 Egyptian pounds "
         "and 307,832,282 pounds, respectively. On the other hand, Egyptians were net sellers with 9,730,797,772 pounds.")
    r = parse_flows(t, date(2026, 10, 15))
    assert len(r) == 1 and abs(r[0]["value"] - 307.83) < 0.01
