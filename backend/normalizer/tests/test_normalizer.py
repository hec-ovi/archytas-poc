"""One test per promise in the contract, through the public entry points.

The cases are the real ones: the spellings, formats and duplicates that actually arrive from
the portal. A case that never happens proves nothing.
"""

from normalizer.dates import parse_date
from normalizer.duplicates import DuplicateFinder, DuplicateKind
from normalizer.matching import CatalogEntry, CatalogMatcher, build_catalog
from normalizer.money import format_amount, parse_amount


class TestDates:
    def test_reads_every_format_that_arrives(self):
        assert parse_date("2026-05-03").value == "2026-05-03"
        assert parse_date("3 de mayo de 2026").value == "2026-05-03"
        assert parse_date("20260503").value == "2026-05-03"
        assert parse_date("3-may-2026").value == "2026-05-03"

    def test_day_comes_first_because_this_is_argentina(self):
        assert parse_date("03/05/2026").value == "2026-05-03"

    def test_an_ambiguous_date_says_it_was_a_judgement_call(self):
        both_readings_valid = parse_date("03/05/2026")
        only_one_reading = parse_date("15/03/2026")
        assert both_readings_valid.confidence < only_one_reading.confidence

    def test_a_date_that_does_not_exist_stays_unresolved(self):
        result = parse_date("31/02/2025")
        assert result.value is None
        assert result.needs_review

    def test_an_empty_date_is_not_an_error(self):
        assert parse_date("").value is None
        assert parse_date(None).value is None


class TestAmounts:
    def test_the_dot_is_thousands_in_the_price_list(self):
        assert parse_amount("$223.376").value == 22337600

    def test_the_dot_is_decimals_in_the_sales_export(self):
        # both conventions arrive from the same portal, told apart by the digits after the dot
        assert parse_amount("37377.00").value == 3737700

    def test_reads_the_argentinian_and_the_english_shape(self):
        assert parse_amount("$1.234,56").value == 123456
        assert parse_amount("1,399,069.50").value == 139906950

    def test_a_negative_arrives_either_way(self):
        assert parse_amount("-$500").value == -50000
        assert parse_amount("($1.200)").value == -120000

    def test_writes_it_back_the_way_the_client_reads_it(self):
        assert format_amount(139906900) == "$1.399.069,00"

    def test_something_that_is_not_a_number_stays_unresolved(self):
        assert parse_amount("pendiente").needs_review


class TestMatching:
    def matcher(self):
        return CatalogMatcher([
            CatalogEntry("ferretera-del-norte", "Ferretera del Norte S.R.L."),
            CatalogEntry("herramientas-cuyo", "Herramientas Cuyo S.R.L."),
            CatalogEntry("pinturerias-reunidas", "Pinturerias Reunidas S.A."),
        ])

    def test_company_form_and_case_do_not_change_who_it_is(self):
        assert self.matcher().match("FERRETERA DEL NORTE").value == "ferretera-del-norte"
        assert self.matcher().match("Herramientas Cuyo").value == "herramientas-cuyo"

    def test_a_truncation_still_resolves(self):
        assert self.matcher().match("Pint. Reunidas").value == "pinturerias-reunidas"

    def test_a_typo_is_proposed_not_applied(self):
        result = self.matcher().match("Ferretera del Nrote SRL")
        assert result.value is None
        assert result.needs_review
        assert result.candidates[0][0] == "ferretera-del-norte"

    def test_something_unrelated_is_not_forced_onto_anyone(self):
        result = self.matcher().match("Corralon San Martin")
        assert result.value is None
        assert not result.candidates or result.candidates[0][1] < 0.72

    def test_a_confirmed_spelling_resolves_instantly_next_time(self):
        matcher = self.matcher()
        matcher.learn_alias("ferretera-del-norte", "FDN")
        assert matcher.match("FDN").value == "ferretera-del-norte"

    def test_discovers_the_real_list_when_nobody_wrote_it_down(self):
        catalog = build_catalog([
            "HERRAMIENTAS", "Herramientas", "Herram.",
            "Pinturas y Adhesivos", "PINTURAS Y ADHESIVOS", "Pinturas/Adhesivos",
        ])
        assert len(catalog.entries) == 2
        assert catalog.match("Herram.").resolved

    def test_the_canonical_name_is_the_readable_one(self):
        catalog = build_catalog(["ELECTRICIDAD", "Electricidad"])
        assert catalog.entries[0].name == "Electricidad"


class TestDuplicates:
    def rows(self):
        return [
            {"codigo": "V-1", "cantidad": "5", "total": "500"},
            {"codigo": " v-1 ", "cantidad": "5", "total": "500"},
            {"codigo": "V-2", "cantidad": "3", "total": "300"},
            {"codigo": "V-2", "cantidad": "7", "total": "700"},
            {"codigo": "V-3", "cantidad": "1", "total": "100"},
        ]

    def test_the_same_code_typed_differently_is_the_same_code(self):
        groups = DuplicateFinder("codigo").scan(self.rows())
        assert {g.key for g in groups} == {"V-1", "V-2"}

    def test_the_same_row_twice_collapses_on_its_own(self):
        groups = {g.key: g for g in DuplicateFinder("codigo").scan(self.rows())}
        assert groups["V-1"].kind is DuplicateKind.IDENTICAL

    def test_the_same_code_with_different_content_needs_a_person(self):
        groups = {g.key: g for g in DuplicateFinder("codigo").scan(self.rows())}
        assert groups["V-2"].kind is DuplicateKind.CONFLICTING
        assert "cantidad" in groups["V-2"].differing_fields

    def test_a_row_that_appears_once_is_not_a_duplicate(self):
        assert "V-3" not in {g.key for g in DuplicateFinder("codigo").scan(self.rows())}
