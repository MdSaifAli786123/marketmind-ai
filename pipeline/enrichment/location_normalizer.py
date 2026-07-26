from __future__ import annotations

import html
import re
from dataclasses import dataclass

import pycountry


@dataclass(frozen=True)
class NormalizedLocation:
    city: str | None
    state: str | None
    country: str | None
    remote: bool


class LocationNormalizer:
    """
    Conservative deterministic geographic normalizer.

    Responsibilities:
    - Clean malformed/encoded source text.
    - Detect remote work independently from geography.
    - Normalize country names.
    - Parse structured city/state/country strings.
    - Remove repeated geographic components.
    - Resolve known German city-only locations.
    - Resolve selected unambiguous locations present in the dataset.
    - Avoid guessing ambiguous geography.
    """

    VERSION = "location-v2.1"

    # ==========================================================
    # Country aliases
    # ==========================================================

    COUNTRY_ALIASES: dict[str, str] = {
        "de": "Germany",
        "deutschland": "Germany",
        "germany": "Germany",

        "us": "United States",
        "u.s": "United States",
        "u.s.": "United States",
        "usa": "United States",
        "u.s.a": "United States",
        "u.s.a.": "United States",
        "united states": "United States",
        "united states of america": "United States",

        "uk": "United Kingdom",
        "u.k": "United Kingdom",
        "u.k.": "United Kingdom",
        "great britain": "United Kingdom",
        "britain": "United Kingdom",
        "united kingdom": "United Kingdom",

        "brasil": "Brazil",
        "brazil": "Brazil",

        "españa": "Spain",
        "espana": "Spain",
        "spain": "Spain",

        "perú": "Peru",
        "peru": "Peru",

        "philippines": "Philippines",
        "venezuela": "Venezuela",

        "india": "India",
        "australia": "Australia",
        "canada": "Canada",
        "france": "France",
        "italy": "Italy",
        "netherlands": "Netherlands",
        "the netherlands": "Netherlands",
        "austria": "Austria",
        "switzerland": "Switzerland",
        "belgium": "Belgium",
        "ireland": "Ireland",
        "portugal": "Portugal",
        "poland": "Poland",
        "sweden": "Sweden",
        "norway": "Norway",
        "denmark": "Denmark",
        "finland": "Finland",
        "czech republic": "Czechia",
        "czechia": "Czechia",
        "new zealand": "New Zealand",
        "singapore": "Singapore",
        "japan": "Japan",
        "mexico": "Mexico",
        "indonesia": "Indonesia",
        "ecuador": "Ecuador",
    }

    # ==========================================================
    # Encoding repairs
    # ==========================================================

    TEXT_REPAIRS: dict[str, str] = {
        "EspaÃ±a": "España",
        "PerÃº": "Perú",
        "AndalucÃ\xada": "Andalucía",
        "AndalucÃ­a": "Andalucía",
    }

    # ==========================================================
    # German locations
    # ==========================================================

    GERMAN_LOCATIONS: dict[str, tuple[str, str | None]] = {
        "berlin": ("Berlin", "Berlin"),
        "munich": ("Munich", "Bavaria"),
        "münchen": ("Munich", "Bavaria"),
        "hamburg": ("Hamburg", "Hamburg"),
        "cologne": ("Cologne", "North Rhine-Westphalia"),
        "köln": ("Cologne", "North Rhine-Westphalia"),
        "frankfurt": ("Frankfurt am Main", "Hesse"),
        "frankfurt am main": ("Frankfurt am Main", "Hesse"),
        "stuttgart": ("Stuttgart", "Baden-Württemberg"),
        "düsseldorf": ("Düsseldorf", "North Rhine-Westphalia"),
        "dusseldorf": ("Düsseldorf", "North Rhine-Westphalia"),
        "dresden": ("Dresden", "Saxony"),
        "nuremberg": ("Nuremberg", "Bavaria"),
        "nürnberg": ("Nuremberg", "Bavaria"),
        "mannheim": ("Mannheim", "Baden-Württemberg"),
        "leipzig": ("Leipzig", "Saxony"),
        "bonn": ("Bonn", "North Rhine-Westphalia"),
        "kiel": ("Kiel", "Schleswig-Holstein"),
        "braunschweig": ("Braunschweig", "Lower Saxony"),
        "flensburg": ("Flensburg", "Schleswig-Holstein"),
        "molbergen": ("Molbergen", "Lower Saxony"),
        "bochum": ("Bochum", "North Rhine-Westphalia"),
        "münster": ("Münster", "North Rhine-Westphalia"),
        "essen": ("Essen", "North Rhine-Westphalia"),
        "hanover": ("Hannover", "Lower Saxony"),
        "hannover": ("Hannover", "Lower Saxony"),
        "markt indersdorf": ("Markt Indersdorf", "Bavaria"),
        "regensburg": ("Regensburg", "Bavaria"),
        "augsburg": ("Augsburg", "Bavaria"),
        "chemnitz": ("Chemnitz", "Saxony"),
        "landau": ("Landau", "Rhineland-Palatinate"),
        "ludwigsburg": ("Ludwigsburg", "Baden-Württemberg"),
        "mülheim": ("Mülheim", "North Rhine-Westphalia"),
        "würzburg": ("Würzburg", "Bavaria"),

        "bischofsheim in der rhön": (
            "Bischofsheim in der Rhön",
            "Bavaria",
        ),

        "bremen": ("Bremen", "Bremen"),
        "dortmund": ("Dortmund", "North Rhine-Westphalia"),
        "herford": ("Herford", "North Rhine-Westphalia"),
        "hilden": ("Hilden", "North Rhine-Westphalia"),
        "idstein": ("Idstein", "Hesse"),
        "kaarst": ("Kaarst", "North Rhine-Westphalia"),
        "kempten": ("Kempten", "Bavaria"),
        "langenhagen": ("Langenhagen", "Lower Saxony"),

        "leinfelden-echterdingen": (
            "Leinfelden-Echterdingen",
            "Baden-Württemberg",
        ),

        "lingen": ("Lingen", "Lower Saxony"),
        "mainz": ("Mainz", "Rhineland-Palatinate"),
        "minden": ("Minden", "North Rhine-Westphalia"),

        "neufahrn bei freising": (
            "Neufahrn bei Freising",
            "Bavaria",
        ),

        "oberhausen": (
            "Oberhausen",
            "North Rhine-Westphalia",
        ),

        "passau": ("Passau", "Bavaria"),
        "ravensburg": ("Ravensburg", "Baden-Württemberg"),
        "schönefeld": ("Schönefeld", "Brandenburg"),
        "taunusstein": ("Taunusstein", "Hesse"),
        "trossingen": ("Trossingen", "Baden-Württemberg"),
        "weil am rhein": ("Weil am Rhein", "Baden-Württemberg"),
        "weingarten": ("Weingarten", "Baden-Württemberg"),
        "wustermark": ("Wustermark", "Brandenburg"),

        "altdorf bei nürnberg": (
            "Altdorf bei Nürnberg",
            "Bavaria",
        ),

        "amberg": ("Amberg", "Bavaria"),
        "aschersleben": ("Aschersleben", "Saxony-Anhalt"),
        "backnang": ("Backnang", "Baden-Württemberg"),
        "bad krozingen": ("Bad Krozingen", "Baden-Württemberg"),
        "bad säckingen": ("Bad Säckingen", "Baden-Württemberg"),
        "baiersdorf": ("Baiersdorf", "Bavaria"),
        "beilngries": ("Beilngries", "Bavaria"),
        "bielefeld": ("Bielefeld", "North Rhine-Westphalia"),
        "bruchköbel": ("Bruchköbel", "Hesse"),

        "bruchmühlbach-miesau": (
            "Bruchmühlbach-Miesau",
            "Rhineland-Palatinate",
        ),

        "darmstadt": ("Darmstadt", "Hesse"),
        "delmenhorst": ("Delmenhorst", "Lower Saxony"),
        "dingolfing": ("Dingolfing", "Bavaria"),
        "duisburg": ("Duisburg", "North Rhine-Westphalia"),
        "dülmen": ("Dülmen", "North Rhine-Westphalia"),
        "eching": ("Eching", "Bavaria"),
        "edling": ("Edling", "Bavaria"),
        "ehingen": ("Ehingen", "Baden-Württemberg"),
        "eichenzell": ("Eichenzell", "Hesse"),
        "emskirchen": ("Emskirchen", "Bavaria"),
        "erfurt": ("Erfurt", "Thuringia"),
        "erfweiler": ("Erfweiler", "Rhineland-Palatinate"),
        "eschborn": ("Eschborn", "Hesse"),
        "ettlingen": ("Ettlingen", "Baden-Württemberg"),
        "falkensee": ("Falkensee", "Brandenburg"),
        "fischen": ("Fischen", "Bavaria"),
        "forchheim": ("Forchheim", "Bavaria"),
        "frankenheim": ("Frankenheim", "Thuringia"),

        "freiburg im breisgau": (
            "Freiburg im Breisgau",
            "Baden-Württemberg",
        ),

        "fürth": ("Fürth", "Bavaria"),
        "gaimersheim": ("Gaimersheim", "Bavaria"),

        "garching an der alz": (
            "Garching an der Alz",
            "Bavaria",
        ),

        "gau-bickelheim": (
            "Gau-Bickelheim",
            "Rhineland-Palatinate",
        ),

        "gemmrigheim": ("Gemmrigheim", "Baden-Württemberg"),
        "gröbenzell": ("Gröbenzell", "Bavaria"),
        "gärtringen": ("Gärtringen", "Baden-Württemberg"),
        "göppingen": ("Göppingen", "Baden-Württemberg"),
        "hasloh": ("Hasloh", "Schleswig-Holstein"),
        "heidelberg": ("Heidelberg", "Baden-Württemberg"),
        "hockenheim": ("Hockenheim", "Baden-Württemberg"),
        "hohenwestedt": ("Hohenwestedt", "Schleswig-Holstein"),
        "hüfingen": ("Hüfingen", "Baden-Württemberg"),
        "isen": ("Isen", "Bavaria"),

        "kaiserslautern": (
            "Kaiserslautern",
            "Rhineland-Palatinate",
        ),

        "karlsfeld": ("Karlsfeld", "Bavaria"),
        "karlsruhe": ("Karlsruhe", "Baden-Württemberg"),
        "kevelaer": ("Kevelaer", "North Rhine-Westphalia"),
        "kleinmachnow": ("Kleinmachnow", "Brandenburg"),
        "konstanz": ("Konstanz", "Baden-Württemberg"),
        "krien": ("Krien", "Mecklenburg-Vorpommern"),
        "kulmbach": ("Kulmbach", "Bavaria"),

        "königsbach-stein": (
            "Königsbach-Stein",
            "Baden-Württemberg",
        ),

        "königstein im taunus": (
            "Königstein im Taunus",
            "Hesse",
        ),

        "küssaberg": ("Küssaberg", "Baden-Württemberg"),
        "langenfeld": ("Langenfeld", "North Rhine-Westphalia"),
        "lauter": ("Lauter", "Saxony"),
        "lauterbach": ("Lauterbach", "Hesse"),
        "lemgow": ("Lemgow", "Lower Saxony"),
        "leverkusen": ("Leverkusen", "North Rhine-Westphalia"),
        "lietzow": ("Lietzow", "Mecklenburg-Vorpommern"),
        "magdeburg": ("Magdeburg", "Saxony-Anhalt"),
        "marlow": ("Marlow", "Mecklenburg-Vorpommern"),
        "montabaur": ("Montabaur", "Rhineland-Palatinate"),
        "morbach": ("Morbach", "Rhineland-Palatinate"),
        "murg": ("Murg", "Baden-Württemberg"),

        "neumarkt in der oberpfalz": (
            "Neumarkt in der Oberpfalz",
            "Bavaria",
        ),

        "neunkirchen": ("Neunkirchen", "Saarland"),
        "nordhausen": ("Nordhausen", "Thuringia"),
        "oberstenfeld": ("Oberstenfeld", "Baden-Württemberg"),
        "obersulm": ("Obersulm", "Baden-Württemberg"),
        "offenbach am main": ("Offenbach am Main", "Hesse"),
        "offenburg": ("Offenburg", "Baden-Württemberg"),
        "puchheim": ("Puchheim", "Bavaria"),
        "ratingen": ("Ratingen", "North Rhine-Westphalia"),
        "reken": ("Reken", "North Rhine-Westphalia"),
        "remseck": ("Remseck", "Baden-Württemberg"),
        "reutlingen": ("Reutlingen", "Baden-Württemberg"),

        "rheda-wiedenbrück": (
            "Rheda-Wiedenbrück",
            "North Rhine-Westphalia",
        ),

        "rüsselsheim": ("Rüsselsheim", "Hesse"),

        "schondorf am ammersee": (
            "Schondorf am Ammersee",
            "Bavaria",
        ),

        "schopp": ("Schopp", "Rhineland-Palatinate"),
        "schwetzingen": ("Schwetzingen", "Baden-Württemberg"),

        "schwäbisch hall": (
            "Schwäbisch Hall",
            "Baden-Württemberg",
        ),

        "siegburg": ("Siegburg", "North Rhine-Westphalia"),
        "siegen": ("Siegen", "North Rhine-Westphalia"),
        "siek": ("Siek", "Schleswig-Holstein"),
        "steinach": ("Steinach", "Bavaria"),
        "steinau an der straße": ("Steinau an der Straße", "Hesse"),
        "steingaden": ("Steingaden", "Bavaria"),
        "surberg": ("Surberg", "Bavaria"),
        "sylt": ("Sylt", "Schleswig-Holstein"),
        "traunreut": ("Traunreut", "Bavaria"),
        "uhingen": ("Uhingen", "Baden-Württemberg"),
        "urbach": ("Urbach", "Baden-Württemberg"),

        "wangen im allgäu": (
            "Wangen im Allgäu",
            "Baden-Württemberg",
        ),

        "wedemark": ("Wedemark", "Lower Saxony"),

        "weilheim in oberbayern": (
            "Weilheim in Oberbayern",
            "Bavaria",
        ),

        "weitersburg": ("Weitersburg", "Rhineland-Palatinate"),

        "westerkappeln": (
            "Westerkappeln",
            "North Rhine-Westphalia",
        ),

        "wetzlar": ("Wetzlar", "Hesse"),
        "wiehl": ("Wiehl", "North Rhine-Westphalia"),
        "wuppertal": ("Wuppertal", "North Rhine-Westphalia"),
        "öhringen": ("Öhringen", "Baden-Württemberg"),
    }

    # ==========================================================
    # Other known unambiguous locations
    # ==========================================================

    KNOWN_LOCATIONS: dict[
        str,
        tuple[str | None, str | None, str],
    ] = {
        # ------------------------------------------------------
        # United States
        # ------------------------------------------------------

        "new york": (
            "New York",
            "New York",
            "United States",
        ),

        "pittsburgh": (
            "Pittsburgh",
            "Pennsylvania",
            "United States",
        ),

        "apopka": (
            "Apopka",
            "Florida",
            "United States",
        ),

        "cloquet": (
            "Cloquet",
            "Minnesota",
            "United States",
        ),

        "greater houston": (
            "Houston",
            "Texas",
            "United States",
        ),

        # ------------------------------------------------------
        # India
        # ------------------------------------------------------

        "guindy": (
            "Guindy",
            "Tamil Nadu",
            "India",
        ),

        "dharmavaram": (
            "Dharmavaram",
            "Andhra Pradesh",
            "India",
        ),

        "greater nagpur area": (
            "Nagpur",
            "Maharashtra",
            "India",
        ),

        "anupgarh": (
            "Anupgarh",
            "Rajasthan",
            "India",
        ),

        "dehradun": (
            "Dehradun",
            "Uttarakhand",
            "India",
        ),

        "jaipur": (
            "Jaipur",
            "Rajasthan",
            "India",
        ),

        "jodhpur": (
            "Jodhpur",
            "Rajasthan",
            "India",
        ),

        "kanke": (
            "Kanke",
            "Jharkhand",
            "India",
        ),

        "goilkera": (
            "Goilkera",
            "Jharkhand",
            "India",
        ),

        # ------------------------------------------------------
        # United Kingdom
        # ------------------------------------------------------

        "london": (
            "London",
            "England",
            "United Kingdom",
        ),

        "frome": (
            "Frome",
            "England",
            "United Kingdom",
        ),

        "fort william": (
            "Fort William",
            "Scotland",
            "United Kingdom",
        ),

        "greater edinburgh area": (
            "Edinburgh",
            "Scotland",
            "United Kingdom",
        ),

        "high beech": (
            "High Beech",
            "England",
            "United Kingdom",
        ),

        # ------------------------------------------------------
        # Spain
        # ------------------------------------------------------

        "madrid": (
            "Madrid",
            "Community of Madrid",
            "Spain",
        ),

        "granada": (
            "Granada",
            "Andalusia",
            "Spain",
        ),

        # ------------------------------------------------------
        # Ecuador
        # ------------------------------------------------------

        "quito": (
            "Quito",
            "Pichincha",
            "Ecuador",
        ),

        # ------------------------------------------------------
        # Indonesia
        # ------------------------------------------------------

        "surabaya": (
            "Surabaya",
            "East Java",
            "Indonesia",
        ),

        # ------------------------------------------------------
        # Australia
        # ------------------------------------------------------

        "albury": (
            "Albury",
            "New South Wales",
            "Australia",
        ),

        "wagga wagga": (
            "Wagga Wagga",
            "New South Wales",
            "Australia",
        ),

        "greater sydney area": (
            "Sydney",
            "New South Wales",
            "Australia",
        ),

        "wynn vale": (
            "Wynn Vale",
            "South Australia",
            "Australia",
        ),

        # ------------------------------------------------------
        # Canada
        # ------------------------------------------------------

        "lethbridge": (
            "Lethbridge",
            "Alberta",
            "Canada",
        ),

        # ------------------------------------------------------
        # France
        # ------------------------------------------------------

        "gironde": (
            None,
            "Gironde",
            "France",
        ),
    }

    # ==========================================================
    # Remote markers
    # ==========================================================

    REMOTE_VALUES: set[str] = {
        "remote",
        "worldwide",
        "world wide",
        "anywhere",
        "global",
        "fully remote",
        "100% remote",
        "remote worldwide",
    }

    # ==========================================================
    # Public API
    # ==========================================================

    def normalize(
        self,
        raw_location: str | None,
        remote: bool = False,
    ) -> NormalizedLocation:

        value = self._clean(raw_location)

        if not value:
            return NormalizedLocation(
                city=None,
                state=None,
                country=None,
                remote=remote,
            )

        remote_detected = (
            remote
            or self._contains_remote_marker(value)
        )

        # ------------------------------------------------------
        # Pure remote value
        # ------------------------------------------------------

        if value.lower() in self.REMOTE_VALUES:
            return NormalizedLocation(
                city=None,
                state=None,
                country=None,
                remote=True,
            )

        # ------------------------------------------------------
        # Remove remote markers while preserving geography
        # ------------------------------------------------------

        geographic_value = self._remove_remote_markers(
            value
        )

        if not geographic_value:
            return NormalizedLocation(
                city=None,
                state=None,
                country=None,
                remote=remote_detected,
            )

        # ------------------------------------------------------
        # Country-only location
        # ------------------------------------------------------

        country = self._country(
            geographic_value
        )

        if country:
            return NormalizedLocation(
                city=None,
                state=None,
                country=country,
                remote=remote_detected,
            )

        # ------------------------------------------------------
        # Known German city / municipality
        # ------------------------------------------------------

        german = self._german_location(
            geographic_value
        )

        if german:
            city, state = german

            return NormalizedLocation(
                city=city,
                state=state,
                country="Germany",
                remote=remote_detected,
            )

        # ------------------------------------------------------
        # Other known location
        # ------------------------------------------------------

        known = self._known_location(
            geographic_value
        )

        if known:
            city, state, country = known

            return NormalizedLocation(
                city=city,
                state=state,
                country=country,
                remote=remote_detected,
            )

        # ------------------------------------------------------
        # Structured location
        # ------------------------------------------------------

        parts = self._split(
            geographic_value
        )

        if len(parts) >= 2:
            result = self._parse_structured(
                parts=parts,
                remote=remote_detected,
            )

            if result is not None:
                return result

        # ------------------------------------------------------
        # Unknown / ambiguous geography
        # ------------------------------------------------------
        #
        # Preserve the raw cleaned value as a city-like field,
        # but do NOT invent state/country.
        # ------------------------------------------------------

        return NormalizedLocation(
            city=geographic_value,
            state=None,
            country=None,
            remote=remote_detected,
        )

    # ==========================================================
    # Structured location parser
    # ==========================================================

    def _parse_structured(
        self,
        parts: list[str],
        remote: bool,
    ) -> NormalizedLocation | None:

        if not parts:
            return None

        # ------------------------------------------------------
        # Country should normally be the final component.
        #
        # IMPORTANT:
        # Determine the country BEFORE duplicate reduction.
        # This lets us use known city mappings before information
        # such as "New York, New York" is collapsed.
        # ------------------------------------------------------

        country = self._country(
            parts[-1]
        )

        if not country:
            return None

        geography = parts[:-1]

        if not geography:
            return NormalizedLocation(
                city=None,
                state=None,
                country=country,
                remote=remote,
            )

        # ------------------------------------------------------
        # Known location takes precedence.
        #
        # Example:
        #
        # New York, New York, New York, United States
        #
        # -> New York / New York / United States
        # ------------------------------------------------------

        known = self._known_location(
            geography[0]
        )

        if (
            known is not None
            and known[2] == country
        ):
            city, state, _ = known

            return NormalizedLocation(
                city=city,
                state=state,
                country=country,
                remote=remote,
            )

        # ------------------------------------------------------
        # Now remove consecutive duplicate components.
        #
        # Sydney, Sydney, New South Wales
        #
        # -> Sydney, New South Wales
        # ------------------------------------------------------

        geography = self._deduplicate_parts(
            geography
        )

        if not geography:
            return NormalizedLocation(
                city=None,
                state=None,
                country=country,
                remote=remote,
            )

        # ------------------------------------------------------
        # Germany
        # ------------------------------------------------------

        if country == "Germany":

            city_candidate = geography[0]

            german = self._german_location(
                city_candidate
            )

            if german:
                city, known_state = german

                explicit_state = (
                    geography[-1]
                    if len(geography) >= 2
                    else None
                )

                state = self._normalize_state(
                    explicit_state,
                    country,
                )

                if not state:
                    state = known_state

                return NormalizedLocation(
                    city=city,
                    state=state,
                    country=country,
                    remote=remote,
                )

        # ------------------------------------------------------
        # Generic structured geography
        #
        # Examples:
        #
        # Pasadena, Pasadena, California, United States
        # -> Pasadena / California / United States
        #
        # Sydney, Sydney, New South Wales, Australia
        # -> Sydney / New South Wales / Australia
        # ------------------------------------------------------

        city = geography[0]

        state = None

        if len(geography) >= 2:
            state = geography[-1]

        city = self._normalize_city(
            city,
            country,
        )

        state = self._normalize_state(
            state,
            country,
        )

        return NormalizedLocation(
            city=city,
            state=state,
            country=country,
            remote=remote,
        )

    # ==========================================================
    # Country resolution
    # ==========================================================

    @classmethod
    def _country(
        cls,
        value: str,
    ) -> str | None:

        normalized = cls._key(
            value
        )

        alias = cls.COUNTRY_ALIASES.get(
            normalized
        )

        if alias:
            return alias

        cleaned = value.strip(
            " ,.;"
        )

        try:
            result = pycountry.countries.lookup(
                cleaned
            )

            common_name = getattr(
                result,
                "common_name",
                None,
            )

            if common_name:
                return common_name

            return result.name

        except LookupError:
            return None

    # ==========================================================
    # German location lookup
    # ==========================================================

    @classmethod
    def _german_location(
        cls,
        value: str,
    ) -> tuple[str, str | None] | None:

        return cls.GERMAN_LOCATIONS.get(
            cls._key(value)
        )

    # ==========================================================
    # Known location lookup
    # ==========================================================

    @classmethod
    def _known_location(
        cls,
        value: str,
    ) -> tuple[
        str | None,
        str | None,
        str,
    ] | None:

        return cls.KNOWN_LOCATIONS.get(
            cls._key(value)
        )

    # ==========================================================
    # Text cleanup
    # ==========================================================

    @classmethod
    def _clean(
        cls,
        value: str | None,
    ) -> str:

        if not value:
            return ""

        result = html.unescape(
            str(value)
        )

        for bad, good in cls.TEXT_REPAIRS.items():
            result = result.replace(
                bad,
                good,
            )

        result = re.sub(
            r"\s+",
            " ",
            result,
        )

        return result.strip(
            " ,;|"
        )

    # ==========================================================
    # Split structured geography
    # ==========================================================

    @staticmethod
    def _split(
        value: str,
    ) -> list[str]:

        parts = re.split(
            r"\s*[,;|]\s*",
            value,
        )

        return [
            part.strip()
            for part in parts
            if part.strip()
        ]

    # ==========================================================
    # Remove consecutive duplicate geography
    # ==========================================================

    @classmethod
    def _deduplicate_parts(
        cls,
        parts: list[str],
    ) -> list[str]:

        result: list[str] = []

        previous_key: str | None = None

        for part in parts:

            key = cls._key(
                part
            )

            if (
                previous_key is not None
                and key == previous_key
            ):
                continue

            result.append(
                part
            )

            previous_key = key

        return result

    # ==========================================================
    # City normalization
    # ==========================================================

    @classmethod
    def _normalize_city(
        cls,
        city: str | None,
        country: str,
    ) -> str | None:

        if not city:
            return None

        if country == "Germany":
            german = cls._german_location(
                city
            )

            if german:
                return german[0]

        known = cls._known_location(
            city
        )

        if (
            known is not None
            and known[2] == country
            and known[0]
        ):
            return known[0]

        return city.strip()

    # ==========================================================
    # State normalization
    # ==========================================================

    @classmethod
    def _normalize_state(
        cls,
        state: str | None,
        country: str,
    ) -> str | None:

        if not state:
            return None

        value = state.strip()

        aliases = {
            # Germany
            ("bayern", "Germany"): "Bavaria",
            ("bavaria", "Germany"): "Bavaria",
            ("berlin", "Germany"): "Berlin",
            ("hamburg", "Germany"): "Hamburg",
            ("saxony", "Germany"): "Saxony",
            ("sachsen", "Germany"): "Saxony",
            ("saxony-anhalt", "Germany"): "Saxony-Anhalt",
            ("hesse", "Germany"): "Hesse",
            ("hessen", "Germany"): "Hesse",

            (
                "baden-württemberg",
                "Germany",
            ): "Baden-Württemberg",

            (
                "north rhine-westphalia",
                "Germany",
            ): "North Rhine-Westphalia",

            (
                "nordrhein-westfalen",
                "Germany",
            ): "North Rhine-Westphalia",

            (
                "lower saxony",
                "Germany",
            ): "Lower Saxony",

            (
                "niedersachsen",
                "Germany",
            ): "Lower Saxony",

            (
                "rheinland-pfalz",
                "Germany",
            ): "Rhineland-Palatinate",

            (
                "rhineland-palatinate",
                "Germany",
            ): "Rhineland-Palatinate",

            (
                "schleswig-holstein",
                "Germany",
            ): "Schleswig-Holstein",

            (
                "brandenburg",
                "Germany",
            ): "Brandenburg",

            (
                "thüringen",
                "Germany",
            ): "Thuringia",

            (
                "thuringia",
                "Germany",
            ): "Thuringia",

            (
                "mecklenburg-vorpommern",
                "Germany",
            ): "Mecklenburg-Vorpommern",

            (
                "saarland",
                "Germany",
            ): "Saarland",

            (
                "bremen",
                "Germany",
            ): "Bremen",

            # Spain
            (
                "andalucía",
                "Spain",
            ): "Andalusia",

            (
                "andalucia",
                "Spain",
            ): "Andalusia",
        }

        return aliases.get(
            (
                cls._key(value),
                country,
            ),
            value,
        )

    # ==========================================================
    # Remote detection
    # ==========================================================

    @staticmethod
    def _contains_remote_marker(
        value: str,
    ) -> bool:

        patterns = [
            r"\bremote\b",
            r"\bworldwide\b",
            r"\bworld wide\b",
            r"\banywhere\b",
            r"\bfully remote\b",
            r"\b100%\s*remote\b",
        ]

        return any(
            re.search(
                pattern,
                value,
                flags=re.IGNORECASE,
            )
            is not None
            for pattern in patterns
        )

    # ==========================================================
    # Remove remote markers
    # ==========================================================

    @staticmethod
    def _remove_remote_markers(
        value: str,
    ) -> str:

        result = value

        patterns = [
            r"\(\s*remote\s*\)",
            r"\[\s*remote\s*\]",
            r"\bfully\s+remote\b",
            r"\b100%\s*remote\b",
            r"\bremote\s+worldwide\b",
            r"\bworldwide\b",
            r"\bworld\s+wide\b",
            r"\banywhere\b",
            r"\bremote\b",
        ]

        for pattern in patterns:
            result = re.sub(
                pattern,
                " ",
                result,
                flags=re.IGNORECASE,
            )

        result = re.sub(
            r"\s+",
            " ",
            result,
        )

        result = re.sub(
            r"^[\s,;|/\-]+",
            "",
            result,
        )

        result = re.sub(
            r"[\s,;|/\-]+$",
            "",
            result,
        )

        return result.strip()

    # ==========================================================
    # Lookup key
    # ==========================================================

    @staticmethod
    def _key(
        value: str,
    ) -> str:

        value = value.strip().lower()

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip(
            " ,.;"
        )