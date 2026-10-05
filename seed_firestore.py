# Copyright 2026 Google LLC
# Seed script for Urban Bites Co menu_items collection in Firestore

import subprocess
import google.auth
import google.oauth2.credentials
from google.cloud import firestore

# CRITICAL: Hardcode the GCP Project ID as a literal string.
# Do NOT rely on GOOGLE_CLOUD_PROJECT or google.auth.default() project,
# as Agent Platform sets GOOGLE_CLOUD_PROJECT to the numerical project number,
# which causes "NotFound: The database (default) does not exist" errors in Firestore.
PROJECT_ID = "qwiklabs-gcp-01-7a15d6c92f07"


def get_db():
    try:
        token = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()
        creds = google.oauth2.credentials.Credentials(token)
        return firestore.Client(project=PROJECT_ID, credentials=creds)
    except Exception:
        return firestore.Client(project=PROJECT_ID)


db = get_db()

SEED_ITEMS = [
    {
        "id": "valley-view-smash",
        "name": "The Valley View Classic Smash",
        "description": "Double smashed beef patty, double American cheddar, house-made Valley pickle, secret sauce on toasted brioche.",
        "category": "Smash Burgers",
        "price_aud": 18.50,
        "food_cost_aud": 5.20,
        "is_active": True,
        "ingredients": ["Beef Smash Patty", "American Cheddar", "House Pickles", "Secret Sauce", "Brioche Bun"],
        "allergens": ["Gluten", "Dairy", "Egg"]
    },
    {
        "id": "outback-truffle-bacon",
        "name": "Outback Truffle & Bacon Special",
        "description": "200g Grass-fed Aussie beef, truffle aioli, crispy smoked bacon, aged cheddar, caramelized onion relish.",
        "category": "Gourmet Specials",
        "price_aud": 22.50,
        "food_cost_aud": 6.80,
        "is_active": True,
        "ingredients": ["Aussie Grass-fed Beef", "Truffle Aioli", "Smoked Bacon", "Aged Cheddar", "Caramelized Onion"],
        "allergens": ["Gluten", "Dairy", "Egg"]
    },
    {
        "id": "aussie-beetroot-bliss",
        "name": "Aussie Beetroot & Egg Crunch",
        "description": "Aussie classic: smashed beef, fried free-range egg, pickled Australian beetroot, pineapple, lettuce, tomato & mayo.",
        "category": "Aussie Classics",
        "price_aud": 19.50,
        "food_cost_aud": 5.60,
        "is_active": True,
        "ingredients": ["Smashed Beef", "Free-Range Egg", "Aussie Beetroot", "Pineapple Ring", "Crisp Lettuce", "Herb Mayo"],
        "allergens": ["Gluten", "Egg"]
    },
    {
        "id": "sa-halloumi-stack",
        "name": "SA Grilled Halloumi & Mushroom (V)",
        "description": "Local SA grilled halloumi cheese, roasted portobello mushroom, roast pepper pesto, rocket on potato bun.",
        "category": "Vegetarian",
        "price_aud": 17.50,
        "food_cost_aud": 4.90,
        "is_active": True,
        "ingredients": ["SA Halloumi", "Portobello Mushroom", "Roast Pepper Pesto", "Wild Rocket", "Potato Bun"],
        "allergens": ["Gluten", "Dairy", "Nuts"]
    }
]


def seed_menu():
    collection_ref = db.collection("menu_items")
    print(f"Seeding 'menu_items' collection in project '{PROJECT_ID}'...")
    for item in SEED_ITEMS:
        doc_id = item["id"]
        collection_ref.document(doc_id).set(item)
        print(f"  ✓ Added menu item: {item['name']} (${item['price_aud']} AUD)")
    print("Seeding complete!")


if __name__ == "__main__":
    seed_menu()
