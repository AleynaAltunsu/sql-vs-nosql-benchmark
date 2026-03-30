// ============================================================
// MongoDB Aggregation Pipelines — E-Commerce
// ============================================================

db = db.getSiblingDB("ecommerce_nosql");

// ──────────────────────────────────────────────────────────
// 1. Revenue by category (last 30 days)
// ──────────────────────────────────────────────────────────
db.orders.aggregate([
  // Stage 1: filter relevant orders
  {
    $match: {
      status: { $nin: ["cancelled", "refunded"] },
      createdAt: { $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) }
    }
  },
  // Stage 2: unwind items array to get one doc per item
  { $unwind: "$items" },
  // Stage 3: lookup product to get categoryId
  {
    $lookup: {
      from: "products",
      localField: "items.productId",
      foreignField: "_id",
      as: "product"
    }
  },
  { $unwind: "$product" },
  // Stage 4: lookup category name
  {
    $lookup: {
      from: "categories",
      localField: "product.categoryId",
      foreignField: "_id",
      as: "category"
    }
  },
  { $unwind: "$category" },
  // Stage 5: group by category
  {
    $group: {
      _id: "$category._id",
      categoryName:  { $first: "$category.name" },
      totalOrders:   { $addToSet: "$_id" },
      unitsSold:     { $sum: "$items.quantity" },
      grossRevenue:  { $sum: { $multiply: ["$items.quantity", "$items.unitPrice"] } },
      avgUnitPrice:  { $avg: "$items.unitPrice" }
    }
  },
  // Stage 6: project clean output
  {
    $project: {
      categoryName: 1,
      totalOrders:  { $size: "$totalOrders" },
      unitsSold: 1,
      grossRevenue: { $round: ["$grossRevenue", 2] },
      avgUnitPrice: { $round: ["$avgUnitPrice", 2] }
    }
  },
  { $sort: { grossRevenue: -1 } }
]);

// ──────────────────────────────────────────────────────────
// 2. Monthly revenue trend (last 12 months)
// ──────────────────────────────────────────────────────────
db.orders.aggregate([
  {
    $match: {
      status: { $nin: ["cancelled", "refunded"] },
      createdAt: { $gte: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000) }
    }
  },
  {
    $group: {
      _id: {
        year:  { $year: "$createdAt" },
        month: { $month: "$createdAt" }
      },
      orderCount:    { $sum: 1 },
      uniqueBuyers:  { $addToSet: "$userId" },
      revenue:       { $sum: "$totalAmount" }
    }
  },
  {
    $project: {
      month:         "$_id",
      orderCount: 1,
      uniqueBuyers:  { $size: "$uniqueBuyers" },
      revenue:       { $round: ["$revenue", 2] }
    }
  },
  { $sort: { "_id.year": 1, "_id.month": 1 } }
]);

// ──────────────────────────────────────────────────────────
// 3. Top 10 best-selling products
// ──────────────────────────────────────────────────────────
db.orders.aggregate([
  { $match: { status: { $nin: ["cancelled", "refunded"] } } },
  { $unwind: "$items" },
  {
    $group: {
      _id:         "$items.productId",
      productName: { $first: "$items.productName" },
      sku:         { $first: "$items.sku" },
      unitsSold:   { $sum: "$items.quantity" },
      revenue:     { $sum: { $multiply: ["$items.quantity", "$items.unitPrice"] } }
    }
  },
  {
    $project: {
      productName: 1,
      sku: 1,
      unitsSold: 1,
      revenue: { $round: ["$revenue", 2] }
    }
  },
  { $sort: { unitsSold: -1 } },
  { $limit: 10 }
]);

// ──────────────────────────────────────────────────────────
// 4. Customer lifetime value (CLV)
// ──────────────────────────────────────────────────────────
db.orders.aggregate([
  { $match: { status: { $nin: ["cancelled", "refunded"] } } },
  {
    $group: {
      _id:             "$userId",
      totalOrders:     { $sum: 1 },
      lifetimeValue:   { $sum: "$totalAmount" },
      avgOrderValue:   { $avg: "$totalAmount" },
      firstOrder:      { $min: "$createdAt" },
      lastOrder:       { $max: "$createdAt" }
    }
  },
  {
    $lookup: {
      from: "users",
      localField: "_id",
      foreignField: "_id",
      as: "user"
    }
  },
  { $unwind: "$user" },
  {
    $project: {
      username:      "$user.username",
      email:         "$user.email",
      totalOrders: 1,
      lifetimeValue: { $round: ["$lifetimeValue", 2] },
      avgOrderValue: { $round: ["$avgOrderValue", 2] },
      firstOrder: 1,
      lastOrder: 1
    }
  },
  { $sort: { lifetimeValue: -1 } },
  { $limit: 50 }
]);

// ──────────────────────────────────────────────────────────
// 5. Products with low stock but high demand (restock alert)
// ──────────────────────────────────────────────────────────
db.orders.aggregate([
  {
    $match: {
      status: { $nin: ["cancelled", "refunded"] },
      createdAt: { $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) }
    }
  },
  { $unwind: "$items" },
  {
    $group: {
      _id:        "$items.productId",
      soldLast30d: { $sum: "$items.quantity" }
    }
  },
  {
    $lookup: {
      from: "products",
      localField: "_id",
      foreignField: "_id",
      as: "product"
    }
  },
  { $unwind: "$product" },
  { $match: { "product.stock": { $lt: 50 } } },
  {
    $project: {
      productName:      "$product.name",
      currentStock:     "$product.stock",
      soldLast30d: 1,
      dailyVelocity:    { $round: [{ $divide: ["$soldLast30d", 30] }, 1] },
      daysUntilStockout: {
        $round: [{
          $divide: [
            "$product.stock",
            { $max: [{ $divide: ["$soldLast30d", 30] }, 0.01] }
          ]
        }, 0]
      }
    }
  },
  { $sort: { daysUntilStockout: 1 } }
]);
