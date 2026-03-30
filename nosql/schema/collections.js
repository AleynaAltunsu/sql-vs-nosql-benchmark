// ============================================================
// MongoDB Collection Design — E-Commerce (ecommerce_nosql)
// MongoDB 6.0 — Schema validation with $jsonSchema
// ============================================================
// Design philosophy: denormalized, document-first.
// Orders embed items; products embed attributes and reviews summary.
// Users embed addresses (bounded list, max ~10 per user).
// ============================================================

// ─────────────────────────────────────────────────
// Switch to our database
// ─────────────────────────────────────────────────
db = db.getSiblingDB("ecommerce_nosql");

// ─────────────────────────────────────────────────
// USERS collection
// ─────────────────────────────────────────────────
db.createCollection("users", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["email", "username", "createdAt"],
      properties: {
        email: {
          bsonType: "string",
          pattern: "^[^@]+@[^@]+\\.[^@]+$",
          description: "Valid email address, required"
        },
        username: { bsonType: "string", minLength: 2, maxLength: 100 },
        fullName: { bsonType: ["string", "null"] },
        phone: { bsonType: ["string", "null"] },
        isActive: { bsonType: "bool" },
        createdAt: { bsonType: "date" },
        updatedAt: { bsonType: "date" },
        // Embedded addresses — denormalized for fast checkout reads
        addresses: {
          bsonType: "array",
          maxItems: 15,
          items: {
            bsonType: "object",
            required: ["street", "city", "country"],
            properties: {
              label:      { bsonType: "string" },
              street:     { bsonType: "string" },
              city:       { bsonType: "string" },
              country:    { bsonType: "string" },
              postalCode: { bsonType: ["string", "null"] },
              isDefault:  { bsonType: "bool" }
            }
          }
        }
      }
    }
  },
  validationAction: "warn"  // warn instead of error during development
});

db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ createdAt: -1 });
db.users.createIndex({ "addresses.city": 1 });

// ─────────────────────────────────────────────────
// CATEGORIES collection
// ─────────────────────────────────────────────────
db.createCollection("categories", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name", "slug"],
      properties: {
        name:        { bsonType: "string" },
        slug:        { bsonType: "string" },
        parentId:    { bsonType: ["objectId", "null"] },
        description: { bsonType: ["string", "null"] }
      }
    }
  }
});

db.categories.createIndex({ slug: 1 }, { unique: true });
db.categories.createIndex({ parentId: 1 });

// ─────────────────────────────────────────────────
// PRODUCTS collection (denormalized — embeds attrs + rating summary)
// ─────────────────────────────────────────────────
db.createCollection("products", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name", "sku", "price", "stock", "categoryId"],
      properties: {
        name:        { bsonType: "string" },
        description: { bsonType: ["string", "null"] },
        sku:         { bsonType: "string" },
        price:       { bsonType: ["double", "decimal"], minimum: 0 },
        stock:       { bsonType: "int", minimum: 0 },
        brand:       { bsonType: ["string", "null"] },
        categoryId:  { bsonType: "objectId" },
        isActive:    { bsonType: "bool" },
        createdAt:   { bsonType: "date" },
        updatedAt:   { bsonType: "date" },
        // Flexible key-value attributes (e.g. color, size, material)
        attributes: {
          bsonType: "object",
          description: "Arbitrary product specs — no fixed schema"
        },
        // Denormalized rating summary for fast product listing reads
        ratingSummary: {
          bsonType: "object",
          properties: {
            avgRating:   { bsonType: "double" },
            reviewCount: { bsonType: "int" }
          }
        }
      }
    }
  },
  validationAction: "warn"
});

db.products.createIndex({ sku: 1 }, { unique: true });
db.products.createIndex({ categoryId: 1 });
db.products.createIndex({ price: 1 });
db.products.createIndex({ name: "text", description: "text", brand: "text" });  // full-text
db.products.createIndex({ "ratingSummary.avgRating": -1 });

// ─────────────────────────────────────────────────
// ORDERS collection (fully denormalized — embeds items + snapshots)
// ─────────────────────────────────────────────────
db.createCollection("orders", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["userId", "status", "totalAmount", "createdAt"],
      properties: {
        userId:         { bsonType: "objectId" },
        status: {
          bsonType: "string",
          enum: ["pending","confirmed","processing","shipped","delivered","cancelled","refunded"]
        },
        totalAmount:    { bsonType: ["double", "decimal"], minimum: 0 },
        discountAmount: { bsonType: ["double", "decimal"] },
        shippingFee:    { bsonType: ["double", "decimal"] },
        paymentMethod:  { bsonType: ["string", "null"] },
        notes:          { bsonType: ["string", "null"] },
        createdAt:      { bsonType: "date" },
        updatedAt:      { bsonType: "date" },
        // Snapshot of shipping address at time of order
        shippingAddress: {
          bsonType: "object",
          properties: {
            street:     { bsonType: "string" },
            city:       { bsonType: "string" },
            country:    { bsonType: "string" },
            postalCode: { bsonType: ["string", "null"] }
          }
        },
        // Embedded line items with product snapshot (name/price at purchase time)
        items: {
          bsonType: "array",
          minItems: 1,
          items: {
            bsonType: "object",
            required: ["productId", "quantity", "unitPrice"],
            properties: {
              productId:    { bsonType: "objectId" },
              productName:  { bsonType: "string" },   // snapshot
              sku:          { bsonType: "string" },    // snapshot
              quantity:     { bsonType: "int", minimum: 1 },
              unitPrice:    { bsonType: ["double", "decimal"], minimum: 0 },
              discountPct:  { bsonType: ["double", "null"] }
            }
          }
        }
      }
    }
  },
  validationAction: "warn"
});

db.orders.createIndex({ userId: 1 });
db.orders.createIndex({ status: 1 });
db.orders.createIndex({ createdAt: -1 });
db.orders.createIndex({ "items.productId": 1 });

// ─────────────────────────────────────────────────
// REVIEWS collection (separate — unbounded per product)
// ─────────────────────────────────────────────────
db.createCollection("reviews", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["productId", "userId", "rating", "createdAt"],
      properties: {
        productId:  { bsonType: "objectId" },
        userId:     { bsonType: "objectId" },
        rating:     { bsonType: "int", minimum: 1, maximum: 5 },
        title:      { bsonType: ["string", "null"] },
        body:       { bsonType: ["string", "null"] },
        createdAt:  { bsonType: "date" }
      }
    }
  }
});

db.reviews.createIndex({ productId: 1, userId: 1 }, { unique: true });
db.reviews.createIndex({ productId: 1, rating: -1 });

print("✅ Collections and indexes created successfully.");
