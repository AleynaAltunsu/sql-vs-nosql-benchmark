// ============================================================
// MongoDB CRUD Queries — E-Commerce (ecommerce_nosql)
// Run in mongosh or adapt for pymongo
// ============================================================

db = db.getSiblingDB("ecommerce_nosql");

// ──────────────────────────────────────────────────────────
// CREATE
// ──────────────────────────────────────────────────────────

// Insert a user with embedded addresses
db.users.insertOne({
  email: "ayse.kaya@example.com",
  username: "aysekaya",
  fullName: "Ayşe Kaya",
  phone: "+905551234567",
  isActive: true,
  createdAt: new Date(),
  updatedAt: new Date(),
  addresses: [
    {
      label: "home",
      street: "Bağcılar Cd. No:12/3",
      city: "İstanbul",
      country: "Turkey",
      postalCode: "34200",
      isDefault: true
    }
  ]
});

// Insert a product with flexible attributes
db.products.insertOne({
  name: "Wireless Noise-Cancelling Headphones",
  description: "Over-ear Bluetooth headphones with 40hr battery and active noise cancellation.",
  sku: "WH-1000XM5-BLK",
  price: 349.99,
  stock: 120,
  brand: "SoundMax",
  categoryId: ObjectId("000000000000000000000001"),  // replace with real ObjectId
  isActive: true,
  createdAt: new Date(),
  updatedAt: new Date(),
  // No fixed schema — add any product-specific attributes
  attributes: {
    color: "Black",
    connectivity: "Bluetooth 5.2",
    batteryLife: "40 hours",
    weight: "254g",
    foldable: true,
    frequencyResponse: "4Hz–40kHz"
  },
  ratingSummary: { avgRating: 0.0, reviewCount: 0 }
});

// Place an order with embedded items + address snapshot
db.orders.insertOne({
  userId: ObjectId("000000000000000000000002"),  // replace with real ObjectId
  status: "pending",
  totalAmount: 699.98,
  discountAmount: 0,
  shippingFee: 0,
  paymentMethod: "credit_card",
  createdAt: new Date(),
  updatedAt: new Date(),
  // Snapshot — won't change even if user updates their address later
  shippingAddress: {
    street: "Bağcılar Cd. No:12/3",
    city: "İstanbul",
    country: "Turkey",
    postalCode: "34200"
  },
  // Embedded items — no join needed to render the order
  items: [
    {
      productId: ObjectId("000000000000000000000003"),
      productName: "Wireless Noise-Cancelling Headphones",  // snapshot
      sku: "WH-1000XM5-BLK",
      quantity: 2,
      unitPrice: 349.99,
      discountPct: 0
    }
  ]
});

// ──────────────────────────────────────────────────────────
// READ
// ──────────────────────────────────────────────────────────

// Find user by email
db.users.findOne(
  { email: "ayse.kaya@example.com" },
  { _id: 1, username: 1, fullName: 1, email: 1, createdAt: 1 }
);

// Get all orders for a user, sorted newest first
db.orders.find(
  { userId: ObjectId("000000000000000000000002") },
  { status: 1, totalAmount: 1, createdAt: 1, "items": { $size: "$items" } }
).sort({ createdAt: -1 });

// Full-text search on products (requires text index)
db.products.find(
  { $text: { $search: "bluetooth headphones" } },
  { score: { $meta: "textScore" }, name: 1, price: 1, brand: 1 }
).sort({ score: { $meta: "textScore" } }).limit(20);

// Find products in price range with stock
db.products.find({
  price: { $gte: 100, $lte: 500 },
  stock: { $gt: 0 },
  isActive: true
}).sort({ "ratingSummary.avgRating": -1 }).limit(20);

// ──────────────────────────────────────────────────────────
// UPDATE
// ──────────────────────────────────────────────────────────

// Update order status
db.orders.updateOne(
  {
    _id: ObjectId("000000000000000000000004"),
    status: "processing"   // guard: only update if currently processing
  },
  {
    $set: { status: "shipped", updatedAt: new Date() }
  }
);

// Atomically decrement stock
db.products.updateOne(
  {
    _id: ObjectId("000000000000000000000003"),
    stock: { $gte: 2 }    // prevent negative stock
  },
  {
    $inc: { stock: -2 },
    $set: { updatedAt: new Date() }
  }
);

// Add a new address to a user (push to embedded array)
db.users.updateOne(
  { _id: ObjectId("000000000000000000000002") },
  {
    $push: {
      addresses: {
        label: "work",
        street: "Levent Mah. Büyükdere Cd. No:201",
        city: "İstanbul",
        country: "Turkey",
        postalCode: "34394",
        isDefault: false
      }
    },
    $set: { updatedAt: new Date() }
  }
);

// ──────────────────────────────────────────────────────────
// DELETE
// ──────────────────────────────────────────────────────────

// Soft-delete a user
db.users.updateOne(
  { _id: ObjectId("000000000000000000000002") },
  { $set: { isActive: false, updatedAt: new Date() } }
);

// Hard-delete cancelled orders older than 1 year
db.orders.deleteMany({
  status: "cancelled",
  createdAt: { $lt: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000) }
});
