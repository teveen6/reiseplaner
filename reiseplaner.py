from typing import List, Dict

from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(
    title="Reiseplaner API (Single File)",
    description="Reiseplaner anhand von Stadt, Dauer, Interessen und Wetter.",
    version="1.0.0",
)


# ---------- Logik ----------

def _normalize(text: str) -> str:
    return text.strip().title()


def _classify_weather(weather: str) -> str:
    """Einfache Einteilung der Wetterlage."""
    if not weather:
        return "gemischt"

    w = weather.lower()
    if any(wort in w for wort in ["regen", "schlecht", "bewölkt"]):
        return "schlecht"
    if any(wort in w for wort in ["sonnig", "warm", "heiss"]):
        return "gut"
    return "gemischt"


def _build_activity_pool(city: str) -> Dict[str, Dict[str, List[str]]]:
    city_name = _normalize(city)

    return {
        "gut": {
            "morgen": [
                f"Spaziergang durch die Altstadt von {city_name}",
                f"Besuch eines lokalen Marktes in {city_name}",
                f"Frühstück in einem Café mit Terrasse in {city_name}",
            ],
            "nachmittag": [
                f"Stadtführung oder Hop On Hop Off Tour in {city_name}",
                f"Besuch eines Parks oder einer Grünanlage in {city_name}",
                f"Radtour durch verschiedene Viertel von {city_name}",
            ],
            "abend": [
                f"Abendessen in einem typischen Restaurant in {city_name}",
                f"Spaziergang am Abend durch {city_name}",
                f"Besuch einer Rooftop Bar mit Aussicht über {city_name}",
            ],
        },
        "schlecht": {
            "morgen": [
                f"Besuch eines Museums in {city_name}",
                f"Frühstück in einem gemütlichen Café in {city_name}",
                f"Besuch einer Markthalle in {city_name}",
            ],
            "nachmittag": [
                f"Besuch einer Galerie oder Ausstellung in {city_name}",
                f"Shopping in einer Passage oder Mall in {city_name}",
                f"Besuch eines Science Centers oder Erlebnis-Museums in {city_name}",
            ],
            "abend": [
                f"Abendessen mit lokaler Küche in {city_name}",
                f"Besuch eines Konzerts oder Theaters in {city_name}",
                f"Besuch einer Wein- oder Cocktailbar in {city_name}",
            ],
        },
        "gemischt": {
            "morgen": [
                f"Gemütlicher Start mit Café und kurzem Stadtspaziergang in {city_name}",
                f"Besuch einer bekannten Sehenswürdigkeit in {city_name}",
            ],
            "nachmittag": [
                f"Kombination aus Museum und Spaziergang in {city_name}",
                f"Kulinarische Tour oder Street Food in {city_name}",
            ],
            "abend": [
                f"Abendessen mit regionalen Spezialitäten in {city_name}",
                f"Entspannter Abend in einer Bar oder einem Café in {city_name}",
            ],
        },
    }


def _interest_hint(interests: str) -> str:
    if not interests:
        return ""

    lower = interests.lower()
    teile = []

    if any(wort in lower for wort in ["essen", "food", "kulinar", "restaurant"]):
        teile.append("Fokus auf Essen und lokale Spezialitäten")
    if any(wort in lower for wort in ["kultur", "museum", "geschichte"]):
        teile.append("viele kulturelle Programmpunkte und Museen")
    if any(wort in lower for wort in ["natur", "park", "wandern"]):
        teile.append("Möglichkeit für Natur und Grünflächen")
    if any(wort in lower for wort in ["nachtleben", "bar", "club"]):
        teile.append("Optionen für Bars und Nachtleben")

    if not teile:
        return ""

    return "Schwerpunkt: " + ", ".join(teile) + "."


def plan_trip(city: str, days: int, interests: str, weather: str) -> str:
    if not city:
        return "Bitte eine Stadt angeben."

    try:
        days_int = int(days)
        if days_int < 1:
            return "Bitte die Anzahl Tage als positive Zahl angeben."
        if days_int > 21:
            return "Bitte maximal 21 Tage planen, sonst wird der Plan zu lang."
    except Exception:
        return "Bitte 'days' als ganze Zahl angeben."

    weather_class = _classify_weather(weather)
    pool = _build_activity_pool(city)
    interest_text = _interest_hint(interests)

    lines: List[str] = []
    city_name = _normalize(city)

    lines.append(f"Reiseplan für {city_name} ({days_int} Tage)")
    if interests:
        lines.append(f"Interessen: {interests.strip()}")
    if weather:
        lines.append(f"Ausgegangene Wetterlage: {weather.strip()}")
    if interest_text:
        lines.append(interest_text)
    lines.append("")

    buckets = pool.get(weather_class, pool["gemischt"])
    morgens = buckets["morgen"]
    nachmittags = buckets["nachmittag"]
    abends = buckets["abend"]

    for tag in range(1, days_int + 1):
        lines.append(f"Tag {tag}")
        m = morgens[(tag - 1) % len(morgens)]
        n = nachmittags[(tag - 1) % len(nachmittags)]
        a = abends[(tag - 1) % len(abends)]
        lines.append(f"  Morgen: {m}")
        lines.append(f"  Nachmittag: {n}")
        lines.append(f"  Abend: {a}")
        lines.append("")

    return "\n".join(lines)


# ---------- API ----------

class TripRequest(BaseModel):
    city: str = Field(..., example="Madrid")
    days: int = Field(..., example=4, ge=1, le=21)
    interests: str = Field("Essen, Kultur", example="Essen, Kultur")
    weather: str = Field("sonnig", example="sonnig oder leicht bewölkt")


class TripResponse(BaseModel):
    plan: str


@app.post("/plan_trip", response_model=TripResponse)
def plan_trip_endpoint(req: TripRequest) -> TripResponse:
    plan = plan_trip(
        city=req.city,
        days=req.days,
        interests=req.interests,
        weather=req.weather,
    )
    return TripResponse(plan=plan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("reiseplaner:app", host="127.0.0.1", port=8000, reload=True)
