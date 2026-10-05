# Copyright 2026 Google LLC
# Tools for Urban Bites Co menu management, margin calculations, and media generation.

import hashlib
import time
import subprocess
import google.auth
import google.oauth2.credentials
from google.cloud import firestore, storage
from google.adk.tools import ToolContext
from google import genai
from google.genai import types

FIRESTORE_PROJECT_ID = "qwiklabs-gcp-01-7a15d6c92f07"
GCS_BUCKET_NAME = "urban-bites-co-media-qwiklabs-gcp-01-7a15d6c92f07"

_db = None
_storage_client = None


def get_firestore_client() -> firestore.Client:
    global _db
    if _db is None:
        try:
            token = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()
            creds = google.oauth2.credentials.Credentials(token)
            _db = firestore.Client(project=FIRESTORE_PROJECT_ID, credentials=creds)
        except Exception:
            _db = firestore.Client(project=FIRESTORE_PROJECT_ID)
    return _db


def get_storage_client() -> storage.Client:
    global _storage_client
    if _storage_client is None:
        try:
            token = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()
            creds = google.oauth2.credentials.Credentials(token)
            _storage_client = storage.Client(project=FIRESTORE_PROJECT_ID, credentials=creds)
        except Exception:
            _storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
    return _storage_client


def get_menu_items(category: str = None) -> list[dict]:
    """Retrieves menu items from Urban Bites Co's Firestore database.

    Args:
        category: Optional category string to filter by (e.g., 'Smash Burgers', 'Gourmet Specials', 'Aussie Classics', 'Vegetarian').

    Returns:
        List of dictionaries containing menu item details including name, price_aud, food_cost_aud, ingredients, and description.
    """
    db = get_firestore_client()
    collection_ref = db.collection("menu_items")

    docs = collection_ref.stream()
    items = []
    for doc in docs:
        data = doc.to_dict()
        if category and data.get("category", "").lower() != category.lower():
            continue
        items.append(data)
    return items


def add_menu_item(
    name: str,
    description: str,
    category: str,
    price_aud: float,
    food_cost_aud: float,
    ingredients: list[str],
    allergens: list[str] = None,
) -> str:
    """Adds or updates a burger menu item in Urban Bites Co's Firestore database.

    Args:
        name: Name of the burger or menu item (e.g. 'Valley View Truffle Smash').
        description: Detailed description of the burger.
        category: Category (e.g., 'Smash Burgers', 'Gourmet Specials', 'Aussie Classics', 'Sides').
        price_aud: Retail selling price in Australian Dollars (AUD).
        food_cost_aud: Cost of ingredients per burger in AUD.
        ingredients: List of ingredient strings.
        allergens: Optional list of allergen strings (e.g., ['Gluten', 'Dairy']).

    Returns:
        Confirmation string indicating successful addition to Firestore.
    """
    db = get_firestore_client()
    doc_id = name.lower().replace(" ", "-").replace("&", "and")
    item_data = {
        "id": doc_id,
        "name": name,
        "description": description,
        "category": category,
        "price_aud": float(price_aud),
        "food_cost_aud": float(food_cost_aud),
        "is_active": True,
        "ingredients": ingredients,
        "allergens": allergens or [],
    }
    db.collection("menu_items").document(doc_id).set(item_data)
    return f"Successfully saved menu item '{name}' (ID: {doc_id}) to Urban Bites Co menu database!"


def calculate_recipe_margins(ingredients_costs: dict[str, float], selling_price_aud: float) -> dict:
    """Calculates food cost, gross profit margin, profit percentage, and recommended pricing for Urban Bites Co recipes.

    Args:
        ingredients_costs: Dictionary mapping ingredient name to cost in AUD (e.g. {'Beef Patty': 2.50, 'Cheese': 0.80, 'Brioche': 0.90}).
        selling_price_aud: The proposed retail selling price of the item in AUD (e.g. 18.50).

    Returns:
        Dictionary containing total_ingredient_cost_aud, gross_profit_aud, food_cost_percentage, gross_margin_percentage, and recommended_retail_price_30_percent_food_cost.
    """
    total_cost = sum(ingredients_costs.values())
    selling_price = float(selling_price_aud)

    food_cost_pct = (total_cost / selling_price * 100) if selling_price > 0 else 0.0
    gross_profit = selling_price - total_cost
    gross_margin_pct = (gross_profit / selling_price * 100) if selling_price > 0 else 0.0

    recommended_price_30_pct = round(total_cost / 0.30, 2)

    return {
        "total_ingredient_cost_aud": round(total_cost, 2),
        "selling_price_aud": round(selling_price, 2),
        "gross_profit_aud": round(gross_profit, 2),
        "food_cost_percentage": round(food_cost_pct, 1),
        "gross_margin_percentage": round(gross_margin_pct, 1),
        "recommended_retail_price_30_pct_target_aud": recommended_price_30_pct,
    }


def generate_marketing_image(prompt: str) -> str:
    """Generates a high-quality promotional photo for Urban Bites Co burgers using AI and uploads it to Cloud Storage.

    Args:
        prompt: Description of the burger or dish photo to generate (e.g., 'Gourmet smashed beef burger with dripping cheddar and truffle aioli on brioche').

    Returns:
        Public HTTPS URL of the generated image saved in Cloud Storage.
    """
    genai_client = genai.Client(vertexai=True, project=FIRESTORE_PROJECT_ID, location="us-central1")
    full_prompt = f"{prompt}, professional food photography, gourmet burger for Urban Bites Co restaurant"

    response = genai_client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=full_prompt,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )

    image_bytes = None
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            image_bytes = part.inline_data.data
            break

    if not image_bytes:
        return "Failed to generate image bytes."

    storage_client = get_storage_client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    filename = f"images/burger_{hashlib.md5(prompt.encode()).hexdigest()[:10]}_{int(time.time())}.png"
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type="image/png")

    public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"
    return f"Generated promotional image successfully! Public URL: {public_url}"


def generate_item_image(prompt: str, tool_context: ToolContext = None) -> str:
    """Generates an image for an item in Urban Bites Co's domain using gemini-3.1-flash-lite-image in the global region.
    Saves the image as an artifact via tool_context.save_artifact for Playground Artifacts panel, and uploads it to Cloud Storage,
    returning its public HTTPS URL.

    Args:
        prompt: Description of the burger or menu item to generate (e.g., 'Gourmet Aussie smash burger with double cheddar, beetroot, and fried egg').
        tool_context: ToolContext passed automatically by the agent framework.

    Returns:
        Public HTTPS URL of the uploaded image in Cloud Storage (https://storage.googleapis.com/<bucket>/<object>).
    """
    import hashlib
    import time

    bucket_name = "urban-bites-co-media-qwiklabs-gcp-01-7a15d6c92f07"
    project_id = "qwiklabs-gcp-01-7a15d6c92f07"

    genai_client = genai.Client(vertexai=True, project=project_id, location="global")
    full_prompt = f"{prompt}, professional food photography, gourmet burger for Urban Bites Co restaurant"

    response = genai_client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=full_prompt,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )

    image_bytes = None
    mime_type = "image/png"
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            image_bytes = part.inline_data.data
            if part.inline_data.mime_type:
                mime_type = part.inline_data.mime_type
            break

    if not image_bytes:
        return "Failed to generate image bytes."

    filename = f"burger_{hashlib.md5(prompt.encode()).hexdigest()[:8]}_{int(time.time())}.png"

    # 1. Save as artifact using tool_context.save_artifact for Playground Artifacts panel
    if tool_context and hasattr(tool_context, "save_artifact"):
        try:
            artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            tool_context.save_artifact(filename=filename, artifact=artifact_part)
        except Exception as e:
            print(f"Warning: save_artifact notice: {e}")

    # 2. Upload same image bytes to public Cloud Storage bucket
    storage_client = get_storage_client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"
    return public_url


def generate_item_video(prompt: str, tool_context: ToolContext = None) -> str:
    """Generates a short video for an item in Urban Bites Co's domain using Google's Omni model (gemini-omni-flash-preview) in the global region.
    Saves the generated video as an artifact via tool_context.save_artifact for the Playground Artifacts panel, and uploads it to Cloud Storage,
    returning its public HTTPS URL.

    Args:
        prompt: Description of the video to generate for the menu item or burger (e.g., 'A short video clip of a sizzling gourmet smash burger at Urban Bites Co').
        tool_context: ToolContext passed automatically by the agent framework.

    Returns:
        Public HTTPS URL of the uploaded video in Cloud Storage (https://storage.googleapis.com/<bucket>/<object>).
    """
    import base64
    import hashlib
    import time

    bucket_name = "urban-bites-co-media-qwiklabs-gcp-01-7a15d6c92f07"
    project_id = "qwiklabs-gcp-01-7a15d6c92f07"

    genai_client = genai.Client(vertexai=True, project=project_id, location="global")
    full_prompt = f"{prompt}, professional food video for Urban Bites Co"

    interaction = genai_client.interactions.create(
        model="gemini-omni-flash-preview",
        input=full_prompt,
        generation_config={"response_modalities": ["VIDEO"]},
    )

    video_bytes = None
    mime_type = "video/mp4"

    if hasattr(interaction, "output_video") and interaction.output_video:
        output_video = interaction.output_video
        if hasattr(output_video, "mime_type") and output_video.mime_type:
            mime_type = str(output_video.mime_type)
        if hasattr(output_video, "data") and output_video.data:
            data = output_video.data
            if isinstance(data, str):
                try:
                    video_bytes = base64.b64decode(data)
                except Exception:
                    video_bytes = data.encode("utf-8")
            elif isinstance(data, bytes):
                video_bytes = data

    if not video_bytes and hasattr(interaction, "outputs") and interaction.outputs:
        for out in interaction.outputs:
            data = getattr(out, "data", None)
            if data:
                if isinstance(data, str):
                    try:
                        video_bytes = base64.b64decode(data)
                    except Exception:
                        video_bytes = data.encode("utf-8")
                elif isinstance(data, bytes):
                    video_bytes = data
                if hasattr(out, "mime_type") and out.mime_type:
                    mime_type = str(out.mime_type)
                break

    if not video_bytes:
        return "Failed to generate video bytes from omni model interaction."

    ext = "mp4" if "mp4" in mime_type else "webm"
    filename = f"burger_video_{hashlib.md5(prompt.encode()).hexdigest()[:8]}_{int(time.time())}.{ext}"

    # 1. Save as artifact using tool_context.save_artifact for Playground Artifacts panel
    if tool_context and hasattr(tool_context, "save_artifact"):
        try:
            artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
            tool_context.save_artifact(filename=filename, artifact=artifact_part)
        except Exception as e:
            print(f"Warning: save_artifact notice: {e}")

    # 2. Upload same video bytes to public Cloud Storage bucket
    storage_client = get_storage_client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_string(video_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"
    return public_url




def generate_marketing_video(prompt: str) -> str:
    """Generates a short promotional social media video clip for Urban Bites Co using Google Veo AI and uploads it to Cloud Storage.

    Args:
        prompt: Video scene description (e.g., 'Sizzling gourmet smashed beef patty with melting cheese for Instagram reel').

    Returns:
        Public HTTPS URL of the generated video saved in Cloud Storage.
    """
    genai_client = genai.Client(vertexai=True, project=FIRESTORE_PROJECT_ID, location="us-central1")
    full_prompt = f"{prompt}, professional restaurant promo video for Urban Bites Co"

    operation = genai_client.models.generate_videos(
        model="veo-3.1-generate-001",
        source=types.GenerateVideosSource(prompt=full_prompt),
    )

    while not operation.done:
        time.sleep(5)
        operation = genai_client.operations.get(operation)

    if operation.error:
        return f"Video generation failed: {operation.error}"

    generated_video = operation.result.generated_videos[0]
    video_bytes = generated_video.video.video_bytes

    storage_client = get_storage_client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    filename = f"videos/burger_{hashlib.md5(prompt.encode()).hexdigest()[:10]}_{int(time.time())}.mp4"
    blob = bucket.blob(filename)
    blob.upload_from_string(video_bytes, content_type="video/mp4")

    public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"
    return f"Generated promotional video successfully! Public URL: {public_url}"


def search_recipe_inspiration(query: str = "burger") -> list[dict]:
    """Searches the free public TheMealDB API for recipe inspirations, side dishes, and global culinary ideas for Urban Bites Co.

    Args:
        query: Search term for recipes or ingredients (e.g., 'burger', 'beef', 'sauce', 'fries', 'lamb').

    Returns:
        List of dictionaries with recipe names, categories, instructions summary, and key ingredients.
    """
    import json
    import urllib.parse
    import urllib.request

    encoded_query = urllib.parse.quote(query)
    url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={encoded_query}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "UrbanBitesCo-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            meals = data.get("meals") or []
            results = []
            for meal in meals[:5]:
                ingredients = []
                for i in range(1, 21):
                    ing = meal.get(f"strIngredient{i}")
                    measure = meal.get(f"strMeasure{i}")
                    if ing and ing.strip():
                        ingredients.append(f"{measure.strip() if measure else ''} {ing.strip()}".strip())
                results.append({
                    "name": meal.get("strMeal"),
                    "category": meal.get("strCategory"),
                    "area": meal.get("strArea"),
                    "instructions": (meal.get("strInstructions") or "")[:200] + "...",
                    "ingredients": ingredients,
                })
            return results
    except Exception as e:
        return [{"error": f"Failed to fetch recipe inspiration: {str(e)}"}]


def _get_maps_api_key() -> str:
    import os

    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key:
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("GOOGLE_MAPS_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        os.environ["GOOGLE_MAPS_API_KEY"] = key
                        break
    return key or ""


def geocode_address(address: str) -> dict:
    """Converts a street address or location name into geographical coordinates (latitude and longitude) using Google Geocoding API.

    Args:
        address: Street address or location name (e.g. 'Shop 8/24 Vale Ave, Valley View SA 5093, Australia').

    Returns:
        Dictionary containing formatted_address, latitude, and longitude.
    """
    import json
    import urllib.parse
    import urllib.request

    api_key = _get_maps_api_key()
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY not found in environment or .env file."}

    encoded_address = urllib.parse.quote(address)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    try:
        req = urllib.request.urlopen(url, timeout=5)
        res = json.loads(req.read().decode())
        if res.get("status") == "OK" and res.get("results"):
            top_result = res["results"][0]
            loc = top_result["geometry"]["location"]
            return {
                "formatted_address": top_result.get("formatted_address"),
                "latitude": loc["lat"],
                "longitude": loc["lng"],
            }
        return {"error": f"Geocoding failed with status: {res.get('status')}"}
    except Exception as e:
        return {"error": f"Geocoding request error: {str(e)}"}


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "restaurant",
    radius_meters: float = 3000.0,
) -> list[dict]:
    """Finds nearby places (restaurants, suppliers, stores) of a given type around coordinates using Google Places API (New).

    Args:
        latitude: Center latitude coordinate.
        longitude: Center longitude coordinate.
        place_type: Type of place to search for (e.g., 'restaurant', 'supermarket', 'bakery', 'cafe').
        radius_meters: Search radius in meters (default is 3000.0 meters).

    Returns:
        List of dictionaries with name, address, location (latitude & longitude), and types for each place found.
    """
    import json
    import urllib.request

    api_key = _get_maps_api_key()
    if not api_key:
        return [{"error": "GOOGLE_MAPS_API_KEY not found in environment or .env file."}]

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.types",
    }
    body = json.dumps({
        "includedTypes": [place_type],
        "locationRestriction": {
            "circle": {
                "center": {"latitude": float(latitude), "longitude": float(longitude)},
                "radius": float(radius_meters),
            }
        },
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            places = data.get("places") or []
            results = []
            for p in places[:10]:
                results.append({
                    "name": p.get("displayName", {}).get("text"),
                    "address": p.get("formattedAddress"),
                    "location": p.get("location"),
                    "types": p.get("types", []),
                })
            return results
    except Exception as e:
        return [{"error": f"Places API request error: {str(e)}"}]


