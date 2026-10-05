# My agent: Aussie Burger Chef Assistant (Urban Bites Co)

One-liner: A conversational AI assistant that helps the Head Chef at **Urban Bites Co** in Valley View, South Australia invent gourmet recipes, calculate menu margins, generate promotional marketing images, and manage restaurant operations.

## Restaurant Details

- **Business Name**: Urban Bites Co
- **Website**: https://urbanbitesco.com/
- **Address**: Shop 8/24 Vale Ave, Valley View SA 5093, Australia

## Tool coverage

- **Memory**: Remembers restaurant details (Urban Bites Co brand identity, Valley View SA location, kitchen equipment, signature sauce recipes, dietary preferences, pricing targets, past top-selling menu items).
- **Tools**:
  - `search_burger_recipes`: Looks up burger concepts, flavor profiles, and seasonal South Australian ingredient pairings.
  - `calculate_portion_cost`: Computes batch ingredient scaling, per-burger food cost percentage, and suggested retail menu pricing in AUD.
  - `generate_marketing_image`: Generates social media promotional photos and food imagery for new Urban Bites Co burger specials.
- **Catalog/UI**: A catalog of active menu items, seasonal burger specials, and ingredient inventories displayed as rich A2UI cards and pricing tables.
- **Image gen**: High-quality promotional images of gourmet burgers, promotional banners, and social media posts.
- **Sandbox**: Python code execution in the sandbox for complex recipe scaling (e.g., scaling a recipe from 10 to 250 covers) and profit margin analysis.

Recommended for every project: memory, storage, tools, image generation, A2UI
Agent-specific / stretch: Code sandbox for recipe scaling & cost margin calculations, Vertex AI Memory Bank for cross-session chef preferences.
