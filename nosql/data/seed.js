// ============================================================
// seed.js — Minimal fixed dataset for smoke-testing
// For large datasets, use: python scripts/generate_data.py
// ============================================================

db = db.getSiblingDB("ecommerce_nosql");

// Categories
const cat_electronics = ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa");
const cat_headphones  = ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb");
const cat_books       = ObjectId("cccccccccccccccccccccccc");

db.categories.insertMany([
  { _id: cat_electronics, name: "Electronics", slug: "electronics", parentId: null },
  { _id: cat_headphones,  name: "Headphones",  slug: "headphones",  parentId: cat_electronics },
  { _id: cat_books,       name: "Books",        slug: "books",       parentId: null }
], { ordered: false });

// Users
const user_alice = ObjectId("dddddddddddddddddddddddd");
const user_bob   = ObjectId("eeeeeeeeeeeeeeeeeeeeeeee");

db.users.insertMany([
  {
    _id: user_alice,
    email: "alice@example.com",
    username: "alice",
    fullName: "Alice Smith",
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date(),
    addresses: [
      { label: "home", street: "123 Main St", city: "Istanbul", country: "Turkey", isDefault: true }
    ]
  },
  {
    _id: user_bob,
    email: "bob@example.com",
    username: "bob",
    fullName: "Bob Jones",
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date(),
    addresses: [
      { label: "home", street: "456 Oak Ave", city: "Ankara", country: "Turkey", isDefault: true }
    ]
  }
], { ordered: false });

// Products
const prod_headphones = ObjectId("ffffffffffffffffffffffff");
const prod_book       = ObjectId("111111111111111111111111");

db.products.insertMany([
  {
    _id: prod_headphones,
    name: "ProSound X1 Headphones",
    sku: "PSX1-BLK",
    price: 199.99,
    stock: 50,
    brand: "ProSound",
    categoryId: cat_headphones,
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date(),
    attributes: { color: "Black", connectivity: "Bluetooth 5.0", batteryLife: "30 hours" },
    ratingSummary: { avgRating: 4.5, reviewCount: 12 }
  },
  {
    _id: prod_book,
    name: "Clean Code",
    sku: "CC-BOOK",
    price: 35.00,
    stock: 200,
    brand: "Prentice Hall",
    categoryId: cat_books,
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date(),
    attributes: { format: "Paperback", pages: 464, language: "English" },
    ratingSummary: { avgRating: 4.8, reviewCount: 340 }
  }
], { ordered: false });

// Orders
db.orders.insertMany([
  {
    userId: user_alice,
    status: "delivered",
    totalAmount: 234.99,
    shippingFee: 0,
    paymentMethod: "credit_card",
    createdAt: new Date(Date.now() - 7 * 86400000),
    updatedAt: new Date(),
    shippingAddress: { street: "123 Main St", city: "Istanbul", country: "Turkey" },
    items: [
      { productId: prod_headphones, productName: "ProSound X1 Headphones",
        sku: "PSX1-BLK", quantity: 1, unitPrice: 199.99 },
      { productId: prod_book, productName: "Clean Code",
        sku: "CC-BOOK", quantity: 1, unitPrice: 35.00 }
    ]
  }
], { ordered: false });

print("✅ Seed data inserted.");
